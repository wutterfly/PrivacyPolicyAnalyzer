"""The propagation comparison example (examples/compare_propagation.py)."""

import importlib.util
import json
from dataclasses import replace
from pathlib import Path

import pytest

from privacy_policy_analyzer import Language
from privacy_policy_analyzer.analysis import classification
from privacy_policy_analyzer.config import EN_DEFAULT_CONFIGURATION

SCRIPT = Path(__file__).resolve().parents[1] / "examples" / "compare_propagation.py"
spec = importlib.util.spec_from_file_location("compare_propagation", SCRIPT)
cp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cp)


def entry(
    text: str = "a sentence",
    contexts: list[str] | None = None,
    topics: dict[str, list[str]] | None = None,
    scores: dict | None = None,
) -> dict:
    return {
        "text": text,
        "contexts": contexts or [],
        "topics": [
            {"topic": t, "contents": [{"content": c, "attributes": []} for c in cs]}
            for t, cs in (topics or {}).items()
        ],
        "structure": {"type": "text", "text_id": 0},
        "scores": scores,
    }


# ---------------------------------------------------------------------------
# reading results
# ---------------------------------------------------------------------------


class TestLabels:
    def test_label_sets_per_level(self):
        e = entry(contexts=["Website"], topics={"Sharing": ["DataType", "Country"], "Selling": []})
        sets = cp.label_sets(e)
        assert sets["scope"] == {"Website"}
        assert sets["topic"] == {"Sharing", "Selling"}
        assert sets["content"] == {("Sharing", "DataType"), ("Sharing", "Country")}

    def test_contents_are_formatted_without_clashing_with_slashes_in_names(self):
        assert cp.format_label(("Security/Privacy", "Tracking/Conversion")) == (
            "Security/Privacy:Tracking/Conversion"
        )
        assert cp.format_label("Website") == "Website"

    def test_own_score_of_every_level(self):
        scores = {
            "contexts": {"Website": 0.8},
            "topics": {"Sharing": 0.35},
            "contents": {"Sharing": {"DataType": 0.9}},
        }
        e = entry(scores=scores)
        assert cp.own_score(e, "scope", "Website") == 0.8
        assert cp.own_score(e, "topic", "Sharing") == 0.35
        assert cp.own_score(e, "content", ("Sharing", "DataType")) == 0.9

    def test_own_score_is_none_when_missing(self):
        scores = {"contexts": {}, "topics": {}, "contents": {}}
        assert cp.own_score(entry(scores=None), "scope", "Website") is None
        assert cp.own_score(entry(scores=scores), "scope", "Website") is None
        assert cp.own_score(entry(scores=scores), "content", ("Sharing", "DataType")) is None

    def test_percentile_interpolates(self):
        values = [0.0, 1.0, 2.0, 3.0, 4.0]
        assert cp.percentile(values, 0.0) == 0.0
        assert cp.percentile(values, 0.5) == 2.0
        assert cp.percentile(values, 0.1) == pytest.approx(0.4)
        assert cp.percentile(values, 1.0) == 4.0
        assert cp.percentile([7.0], 0.9) == 7.0

    def test_runs_with_different_sentences_are_rejected(self):
        runs = {
            "a": {"analyzed": [entry("one"), entry("two")]},
            "b": {"analyzed": [entry("one"), entry("other")]},
        }
        with pytest.raises(cp.MisalignedRuns):
            cp.check_aligned("policy", runs)
        cp.check_aligned("policy", {"a": runs["a"], "b": runs["a"]})


# ---------------------------------------------------------------------------
# comparison
# ---------------------------------------------------------------------------


class TestSummarize:
    def test_shares_and_labels_per_entry(self):
        entries = [
            entry("a", contexts=["Website"], topics={"Sharing": ["DataType"]}),
            entry("b", contexts=["Unspecified"], topics={"Other": []}),
            entry("c", contexts=["App", "Device"], topics={"Sharing": []}),
            entry("", contexts=["Website"]),  # no text of its own: not counted
        ]
        s = cp.summarize([entries])
        assert s["entries"] == 3
        assert s["scope_other_share"] == pytest.approx(1 / 3)
        assert s["topic_other_share"] == pytest.approx(1 / 3)
        assert s["with_content_share"] == pytest.approx(1 / 3)
        assert s["labels_per_entry"] == {
            "scope": pytest.approx(4 / 3),
            "topic": pytest.approx(3 / 3),
            "content": pytest.approx(1 / 3),
        }
        assert s["label_counts"]["scope"] == {"Website": 1, "Unspecified": 1, "App": 1, "Device": 1}
        assert s["label_counts"]["content"] == {"Sharing:DataType": 1}

    def test_works_over_several_policies(self):
        s = cp.summarize([[entry("a", contexts=["Website"])], [entry("b", contexts=["Unspecified"])]])
        assert s["entries"] == 2
        assert s["scope_other_share"] == 0.5

    def test_no_entries(self):
        assert cp.summarize([])["entries"] == 0


class TestCompareRuns:
    def test_identical_runs(self):
        lists = [[entry("a", contexts=["Website"], topics={"Sharing": ["DataType"]})]]
        result = cp.compare_runs(lists, lists)
        for level in cp.LEVELS:
            assert result[level]["differing_entries"] == 0
            assert result[level]["mean_jaccard"] == 1.0
            assert result[level]["labels_only_in_a"] == result[level]["labels_only_in_b"] == 0

    def test_differences_per_level(self):
        a = [[entry("one", contexts=["Website"]), entry("two", topics={"Sharing": []})]]
        b = [
            [
                entry("one", contexts=["Website", "App"]),
                entry("two", topics={"Sharing": [], "Selling": []}),
            ]
        ]
        result = cp.compare_runs(a, b)

        assert result["scope"]["differing_entries"] == 1
        assert result["scope"]["labels_only_in_b"] == 1
        assert result["scope"]["labels_only_in_a"] == 0
        # entry one: |{Website}| / |{Website, App}| = 0.5, entry two: both empty = 1.0
        assert result["scope"]["mean_jaccard"] == pytest.approx(0.75)
        assert result["scope"]["top_only_in_b"] == [("App", 1)]

        assert result["topic"]["differing_entries"] == 1
        assert result["topic"]["top_only_in_b"] == [("Selling", 1)]
        assert result["content"]["differing_entries"] == 0

    def test_labels_only_in_a_are_counted_too(self):
        a = [[entry("one", topics={"Sharing": ["DataType"]})]]
        b = [[entry("one", topics={"Sharing": []})]]
        result = cp.compare_runs(a, b)
        assert result["content"]["labels_only_in_a"] == 1
        assert result["content"]["top_only_in_a"] == [("Sharing:DataType", 1)]

    def test_entries_without_text_are_ignored(self):
        result = cp.compare_runs([[entry("", contexts=["A"])]], [[entry("", contexts=["B"])]])
        assert result["scope"]["entries"] == 0
        assert result["scope"]["differing_entries"] == 0


class TestAddedLabelScores:
    def test_scores_of_the_labels_a_run_adds(self):
        base = [[entry("one"), entry("two"), entry("three")]]

        def scored(topic_score: float) -> dict:
            return {"contexts": {}, "topics": {"Sharing": topic_score}, "contents": {}}

        run = [
            [
                entry("one", topics={"Sharing": []}, scores=scored(0.1)),
                entry("two", topics={"Sharing": []}, scores=scored(0.3)),
                entry("three", scores=scored(0.9)),  # nothing added here
            ]
        ]
        added = cp.added_label_scores(base, run)["topic"]
        assert added["added"] == 2
        assert added["without_score"] == 0
        assert added["median"] == pytest.approx(0.2)
        assert added["p10"] == pytest.approx(0.12)
        assert added["p90"] == pytest.approx(0.28)

    def test_labels_without_a_score_are_counted_separately(self):
        base = [[entry("one")]]
        run = [[entry("one", topics={"Sharing": []}, scores=None)]]
        added = cp.added_label_scores(base, run)["topic"]
        assert added["added"] == 1
        assert added["without_score"] == 1
        assert added["median"] is None

    def test_nothing_added(self):
        lists = [[entry("one", contexts=["Website"])]]
        added = cp.added_label_scores(lists, lists)
        assert all(added[level]["added"] == 0 for level in cp.LEVELS)


def test_propagation_totals_count_what_was_added_in_both_passes_and_blocked_once():
    def stats(added_topics: int, blocked: dict | None) -> dict:
        part = {"contexts": {"total": 1}, "topics": {"total": added_topics}}
        if blocked:
            part["blocked"] = {k: {"total": v} for k, v in blocked.items()}
        return part

    def result(first: dict, second: dict) -> dict:
        return {"stats": {"propagate": {"context_topic": first, "content": second}}}

    totals = cp.propagation_totals(
        [
            result(
                stats(2, {"contexts": 1, "topics": 2, "contents": 0}),
                # the second pass blocks the same scopes and topics again, plus contents
                stats(0, {"contexts": 1, "topics": 2, "contents": 3}),
            ),
            result(
                stats(1, {"contexts": 0, "topics": 1, "contents": 0}),
                stats(0, {"contexts": 0, "topics": 1, "contents": 4}),
            ),
        ]
    )
    assert totals == {
        "added_scopes": 4,
        "added_topics": 3,
        "blocked_contexts": 1,
        "blocked_topics": 3,
        "blocked_contents": 7,
    }
    # a run without a gate has no blocked counts at all
    totals = cp.propagation_totals([result(stats(1, None), stats(0, None))])
    assert totals["blocked_topics"] == totals["blocked_contents"] == 0


# ---------------------------------------------------------------------------
# a whole run, with fake models on saved HTML
# ---------------------------------------------------------------------------

POLICY_A = (
    "<html><body><h1>Sharing</h1>"
    "<p>We give data to partners.</p><p>The weather is nice.</p></body></html>"
)
POLICY_B = (
    "<html><body><h1>Sharing</h1>"
    "<p>Our partners get your data.</p><p>Cats are cute.</p></body></html>"
)


class FakeModel:
    def __init__(self, score_fn):
        self.score_fn = score_fn

    def classifier(self, texts, **kwargs):
        return [
            [{"label": label, "score": score} for label, score in self.score_fn(t).items()]
            for t in texts
        ]


def topic_scores(text: str) -> dict[str, float]:
    if text == "Sharing":
        return {"Sharing": 0.9}
    # a near miss of the Sharing threshold (0.6) for sentences about partners
    return {"Sharing": 0.35 if "partners" in text else 0.02}


@pytest.fixture
def fake_models(monkeypatch):
    base = EN_DEFAULT_CONFIGURATION.model_configs
    score_fns = {
        base.context.model_name: lambda text: {"Website": 0.8},
        base.topic.model_name: topic_scores,
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


@pytest.fixture
def raw_policies(tmp_path) -> Path:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "policy_a.html").write_text(POLICY_A, encoding="utf-8")
    (raw / "policy_b.html").write_text(POLICY_B, encoding="utf-8")
    return raw


CONFIGS = {Language.EN: replace(EN_DEFAULT_CONFIGURATION, use_ner_for_company=False)}


def run_main(raw: Path, out: Path, *extra: str) -> int:
    return cp.main(
        ["--raw", str(raw), "--out", str(out), "--no-preload", *extra], configs=CONFIGS
    )


@pytest.mark.usefixtures("fake_models")
class TestMain:
    def test_writes_four_runs_per_policy_and_the_comparison(self, raw_policies, tmp_path):
        out = tmp_path / "out"
        assert run_main(raw_policies, out) == 0

        runs = ["no_propagation", "default_propagation", "confidence_mild", "confidence_strict"]
        for run in runs:
            for policy in ("policy_a", "policy_b"):
                assert (out / run / f"{policy}.json").is_file()
        assert (out / "comparison.json").is_file()
        assert (out / "comparison.md").is_file()
        assert json.loads((out / "runs.json").read_text()).keys() == set(runs)

        report = (out / "comparison.md").read_text(encoding="utf-8")
        assert "# Header propagation comparison" in report
        assert all(f"`{run}`" in report for run in runs)

    def test_run_results_are_slim_and_include_scores(self, raw_policies, tmp_path):
        out = tmp_path / "out"
        run_main(raw_policies, out)
        data = json.loads((out / "default_propagation" / "policy_a.json").read_text())
        assert set(data) == set(cp.KEPT_KEYS)
        sentence = next(e for e in data["analyzed"] if e["text"] == "We give data to partners.")
        assert sentence["scores"]["topics"] == {"Sharing": 0.35}

    def test_the_runs_differ_as_expected(self, raw_policies, tmp_path):
        out = tmp_path / "out"
        run_main(raw_policies, out)
        comparison = json.loads((out / "comparison.json").read_text())
        pairwise = comparison["pairwise"]

        # default propagation gives Sharing to all four sentences below the headers
        none_vs_default = pairwise["no_propagation vs default_propagation"]
        assert none_vs_default["topic"]["differing_entries"] == 4
        assert none_vs_default["scope"]["differing_entries"] == 0

        # mild: floor 0.5 * 0.6 = 0.3 lets the 0.35 sentences through, not the 0.02 ones
        assert pairwise["no_propagation vs confidence_mild"]["topic"]["differing_entries"] == 2
        assert pairwise["default_propagation vs confidence_mild"]["topic"]["differing_entries"] == 2

        # strict: floor 0.48 blocks them all, so the topics equal the baseline
        assert pairwise["no_propagation vs confidence_strict"]["topic"]["differing_entries"] == 0

        added = comparison["added_vs_baseline"]
        assert added["default_propagation"]["topic"]["added"] == 4
        assert added["default_propagation"]["topic"]["median"] == pytest.approx(0.185)
        assert added["confidence_mild"]["topic"]["added"] == 2
        assert added["confidence_mild"]["topic"]["median"] == pytest.approx(0.35)

        per_run = comparison["per_run"]
        assert per_run["no_propagation"]["propagation"]["added_topics"] == 0
        assert per_run["confidence_mild"]["propagation"]["blocked_topics"] == 2
        assert per_run["confidence_strict"]["propagation"]["blocked_topics"] == 4

        assert comparison["per_policy"]["policy_a"][
            "differs_from_no_propagation:default_propagation"
        ] > 0

    def test_resume_reuses_results_and_checks_the_settings(self, raw_policies, tmp_path, capsys):
        out = tmp_path / "out"
        run_main(raw_policies, out)
        first = (out / "comparison.json").read_text()

        assert run_main(raw_policies, out, "--resume") == 0
        assert capsys.readouterr().out.count("reused") == 2
        assert (out / "comparison.json").read_text() == first

        assert run_main(raw_policies, out, "--resume", "--mild", "0.1") == 2

    def test_limit_and_pattern(self, raw_policies, tmp_path):
        out = tmp_path / "out"
        assert run_main(raw_policies, out, "--limit", "1") == 0
        assert json.loads((out / "comparison.json").read_text())["policies"] == 1

        assert run_main(raw_policies, tmp_path / "none", "--pattern", "*.txt") == 1

    def test_invalid_ratio_is_rejected(self, raw_policies, tmp_path):
        with pytest.raises(ValueError):
            run_main(raw_policies, tmp_path / "out", "--mild", "1.5")
