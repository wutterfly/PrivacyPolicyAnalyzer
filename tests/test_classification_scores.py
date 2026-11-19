from dataclasses import fields

import pytest

import privacy_policy_analyzer.analysis as analysis
from privacy_policy_analyzer.analysis import classification
from privacy_policy_analyzer.analysis.classification import (
    ModelConfig,
    ModelConfigs,
    classify_content,
    classify_scope,
    classify_topics,
)
from privacy_policy_analyzer.shared.annotation import RawEntry, TopicAnnotation


class FakeModel:
    """Stands in for a loaded classifier: returns all label scores per text."""

    def __init__(self, scores_by_text: dict[str, dict[str, float]]):
        self.scores_by_text = scores_by_text

    def classifier(self, texts, **kwargs):
        return [
            [{"label": label, "score": score} for label, score in self.scores_by_text[t].items()]
            for t in texts
        ]


@pytest.fixture
def install_fake_model(monkeypatch):
    def install(scores_by_text: dict[str, dict[str, float]]):
        monkeypatch.setattr(
            classification,
            "_load_pipeline",
            lambda *args, **kwargs: FakeModel(scores_by_text),
        )

    return install


def make_raw_entry(text: str, topics: list[TopicAnnotation] | None = None) -> RawEntry:
    return RawEntry(line_number=0, text=text, scopes=[], topics=topics or [])


def make_model_configs() -> ModelConfigs:
    return ModelConfigs(
        **{f.name: ModelConfig(model_name=f.name, thresholds={}) for f in fields(ModelConfigs)}
    )


def test_scope_scores_are_kept_for_every_label_not_only_those_above_threshold(
    install_fake_model,
):
    install_fake_model({"a sentence": {"Website": 0.8, "App": 0.2, "Device": 0.49}})
    entry = make_raw_entry("a sentence")

    classify_scope(
        [entry],
        ModelConfig("m", {"App": 0.1}),  # App passes with its own lower threshold
        prefer_onnx=False,
        cached=False,
    )

    assert entry.scopes == ["Website", "App"]
    assert entry.scores.scopes == {"Website": 0.8, "App": 0.2, "Device": 0.49}


def test_topic_scores_are_kept_for_every_label(install_fake_model):
    install_fake_model({"a sentence": {"Sharing": 0.7, "Selling": 0.1}})
    entry = make_raw_entry("a sentence")

    classify_topics([entry], ModelConfig("m", {}), prefer_onnx=False, cached=False)

    assert [t.topic for t in entry.topics] == ["Sharing"]
    assert entry.scores.topics == {"Sharing": 0.7, "Selling": 0.1}


def test_content_scores_are_kept_per_topic_for_entries_that_have_the_topic(
    install_fake_model,
):
    install_fake_model({"has topic": {"DataType": 0.9, "Country": 0.2}})
    with_topic = make_raw_entry("has topic", [TopicAnnotation("Sharing", [])])
    without_topic = make_raw_entry("no topic", [TopicAnnotation("Retention", [])])

    classify_content(
        [with_topic, without_topic],
        "Sharing",
        ModelConfig("m", {}),
        prefer_onnx=False,
        cached=False,
    )

    assert with_topic.scores.contents == {"Sharing": {"DataType": 0.9, "Country": 0.2}}
    assert [c.content for c in with_topic.topics[0].contents] == ["DataType"]
    # the Sharing model never ran on the other entry
    assert without_topic.scores.contents == {}


def test_each_entry_has_its_own_scores():
    first = make_raw_entry("first")
    second = make_raw_entry("second")
    first.scores.scopes["Website"] = 1.0
    assert second.scores.scopes == {}


def test_content_models_cover_every_topic_model():
    configs = make_model_configs()
    content_models = configs.content_models()

    assert len(content_models) == 14
    expected = {f.name for f in fields(ModelConfigs)} - {"scope", "topic"}
    assert {config.model_name for config in content_models.values()} == expected


def test_classify_contents_runs_the_content_model_of_every_topic(monkeypatch):
    configs = make_model_configs()
    called: list[tuple[str, str]] = []

    def record(entries, topic, config, prefer_onnx, cached):
        called.append((topic, config.model_name))

    monkeypatch.setattr(analysis, "classify_content", record)

    error = analysis.classify_contents(
        entries=[], model_config=configs, prefer_onnx=False, cached=False
    )

    assert error is None
    assert called == [
        (topic, config.model_name) for topic, config in configs.content_models().items()
    ]
