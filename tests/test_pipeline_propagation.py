"""Pipeline wiring of (gated) header propagation, with fake models."""

from dataclasses import replace
from datetime import date

import pytest

from privacy_policy_analyzer import Language
from privacy_policy_analyzer.analysis import classification
from privacy_policy_analyzer.config import (
    EN_DEFAULT_CONFIGURATION,
    PipelineConfiguration,
    PropagationConfig,
)
from privacy_policy_analyzer.pipeline import Pipeline, PolicyResult

HTML = (
    "<html><body>"
    "<h1>Sharing</h1>"
    "<p>We give data to partners.</p>"
    "<p>The weather is nice.</p>"
    "</body></html>"
)

# model scores per sentence: the header is clearly about sharing, the first
# sentence nearly (0.35 against a threshold of 0.6), the second not at all
TOPIC_SCORES = {
    "Sharing": {"Sharing": 0.9},
    "We give data to partners.": {"Sharing": 0.35},
    "The weather is nice.": {"Sharing": 0.02},
}


class FakeModel:
    def __init__(self, score_fn):
        self.score_fn = score_fn

    def classifier(self, texts, **kwargs):
        return [
            [{"label": label, "score": score} for label, score in self.score_fn(t).items()]
            for t in texts
        ]


@pytest.fixture
def fake_models(monkeypatch):
    base = EN_DEFAULT_CONFIGURATION.model_configs
    score_fns = {
        base.scope.model_name: lambda text: {"Website": 0.8},
        base.topic.model_name: lambda text: TOPIC_SCORES[text],
    }
    for config in base.content_models().values():
        score_fns[config.model_name] = lambda text: {
            "DataType": 0.9 if "data" in text else 0.0
        }

    monkeypatch.setattr(
        classification,
        "_load_pipeline",
        lambda model_name, *args, **kwargs: FakeModel(score_fns[model_name]),
    )


def analyze(propagation: PropagationConfig) -> PolicyResult:
    config: PipelineConfiguration = replace(
        EN_DEFAULT_CONFIGURATION, use_ner_for_company=False, propagation=propagation
    )
    pipeline = Pipeline({Language.EN: config}, prefer_onnx=False, cache_load_models=False)
    result = pipeline.run_with_html(
        "test", "test://policy", Language.EN, date(2026, 1, 1), HTML
    )
    assert isinstance(result, PolicyResult)
    return result


def topics_by_text(result: PolicyResult) -> dict[str, list[str]]:
    return {entry.text: [t.topic for t in entry.topics] for entry in result.analyzed}


@pytest.mark.usefixtures("fake_models")
class TestPipelinePropagation:
    def test_without_a_gate_everything_below_the_header_inherits_its_topic(self):
        result = analyze(PropagationConfig())
        assert topics_by_text(result) == {
            "Sharing": ["Sharing"],
            "We give data to partners.": ["Sharing"],
            "The weather is nice.": ["Sharing"],
        }
        assert "blocked" not in result.stats["propagate"]["scope_topic"]

    def test_with_a_gate_only_sentences_that_nearly_scored_it_inherit_the_topic(self):
        # floor = 0.5 * 0.6 = 0.3: passes for 0.35, blocks 0.02
        result = analyze(PropagationConfig(topic_floor_ratio=0.5))
        topics = topics_by_text(result)
        assert topics["We give data to partners."] == ["Sharing"]
        assert "Sharing" not in topics["The weather is nice."]

        blocked = result.stats["propagate"]["scope_topic"]["blocked"]
        assert blocked["topics"] == {"Sharing": 1, "total": 1}

    def test_content_model_runs_on_sentences_that_inherited_the_topic(self):
        result = analyze(PropagationConfig(topic_floor_ratio=0.5))
        entry = next(e for e in result.analyzed if e.text == "We give data to partners.")
        sharing = next(t for t in entry.topics if t.topic == "Sharing")
        assert [c.content for c in sharing.contents] == ["DataType"]

    def test_without_propagation_headers_pass_nothing_on(self):
        result = analyze(PropagationConfig(enabled=False))
        topics = topics_by_text(result)
        assert topics["Sharing"] == ["Sharing"]
        # the 0.35 sentence misses its threshold of 0.6 and gets nothing
        assert "Sharing" not in topics["We give data to partners."]
        assert "Sharing" not in topics["The weather is nice."]
        propagate = result.stats["propagate"]
        assert propagate["scope_topic"] == {"scopes": {"total": 0}, "topics": {"total": 0}}
        assert propagate["content"] == {"scopes": {"total": 0}, "topics": {"total": 0}}

    def test_scores_of_every_label_are_part_of_the_serialized_result(self):
        result = analyze(PropagationConfig())
        entries = {e["text"]: e for e in result.to_json()["analyzed"]}

        scores = entries["We give data to partners."]["scores"]
        assert scores["scopes"] == {"Website": 0.8}
        assert scores["topics"] == {"Sharing": 0.35}  # below its threshold, kept anyway
        # contents are scored for the topics the sentence had when the model ran
        assert scores["contents"]["Sharing"] == {"DataType": 0.9}

    def test_scores_are_the_same_with_and_without_propagation(self):
        # propagation changes labels, never what the models said
        def scores(propagation: PropagationConfig) -> dict:
            return {
                e["text"]: e["scores"]["topics"]
                for e in analyze(propagation).to_json()["analyzed"]
            }

        assert scores(PropagationConfig(enabled=False)) == scores(PropagationConfig())

    def test_saved_results_can_be_loaded_again_with_their_scores(self):
        result = analyze(PropagationConfig())
        loaded = PolicyResult.from_json(result.to_json())
        assert [e.scores for e in loaded.analyzed] == [e.scores for e in result.analyzed]
