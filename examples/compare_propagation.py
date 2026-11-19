"""Compare header propagation settings on saved privacy policies.

Nothing is fetched: the saved HTML of the policies is analyzed with the same
pipeline four times. Only what headings pass on to the sentences below them
differs between the runs:

  no_propagation       headings pass nothing on
  default_propagation  headings pass all their labels on to everything below them
  confidence_mild      ... but only to sentences whose own model score for the
                       label is at least <mild> x the label's threshold
  confidence_strict    ... same with <strict> x the threshold

For every policy and run the result is written to <out>/<run>/<policy>.json
(including the model scores of every label), and the runs are compared with
each other in <out>/comparison.json and <out>/comparison.md:

  * per run: share of sentences without any scope / topic, labels per sentence,
    what propagation added and what the gate blocked
  * per pair of runs: how many sentences differ, mean Jaccard similarity of
    their label sets, labels only one of the runs has
  * for the labels a run adds compared to no_propagation: how high the
    sentences scored those labels themselves
  * per policy: how many sentences differ from no_propagation

Usage (from the repository root, with the analyzer installed):

    python examples/compare_propagation.py --limit 10
    python examples/compare_propagation.py --raw ../privpolicydata/datasets/PrivaScopeApp/raw --out out_app
    python examples/compare_propagation.py --mild 0.4 --strict 0.9 --min-score 0.05

Every policy is analyzed four times and every analysis loads all classifiers,
so start with --limit. Use --resume to continue an interrupted run with the
same settings.
"""

import argparse
import copy
import json
import logging
import statistics
import sys
from collections import Counter
from dataclasses import asdict, replace
from datetime import date
from itertools import combinations
from pathlib import Path

LEVELS = ("scope", "topic", "content")
BASELINE = "no_propagation"
DEFAULT_RAW = (
    Path(__file__).resolve().parents[2]
    / "privpolicydata"
    / "datasets"
    / "PrivaScopeWeb"
    / "raw"
)
KEPT_KEYS = ("name", "source", "language", "date", "analyzed", "stats")


# ---------------------------------------------------------------------------
# runs
# ---------------------------------------------------------------------------


def make_runs(mild: float, strict: float, min_score: float) -> dict:
    """The four propagation settings, as `PropagationConfig`s."""
    from privacy_policy_analyzer.config import PropagationConfig

    def gated(ratio: float) -> PropagationConfig:
        return PropagationConfig(
            context_floor_ratio=ratio,
            topic_floor_ratio=ratio,
            content_floor_ratio=ratio,
            min_score=min_score,
        )

    return {
        BASELINE: PropagationConfig(enabled=False),
        "default_propagation": PropagationConfig(),
        "confidence_mild": gated(mild),
        "confidence_strict": gated(strict),
    }


# ---------------------------------------------------------------------------
# reading the results of a run (JSON form of PolicyResult.analyzed)
# ---------------------------------------------------------------------------


def label_sets(entry: dict) -> dict[str, set]:
    """The labels of an analyzed entry per level; contents as (topic, content)."""
    return {
        "scope": set(entry["contexts"]),
        "topic": {t["topic"] for t in entry["topics"]},
        "content": {
            (t["topic"], c["content"]) for t in entry["topics"] for c in t["contents"]
        },
    }


def format_label(label) -> str:
    # topic and content names both contain "/" at times, so use ":" here
    return f"{label[0]}:{label[1]}" if isinstance(label, tuple) else label


def own_score(entry: dict, level: str, label) -> float | None:
    """The score the models gave this sentence for the label, if there is one."""
    scores = entry.get("scores")
    if not scores:
        return None
    if level == "scope":
        return scores["contexts"].get(label)
    if level == "topic":
        return scores["topics"].get(label)
    topic, content = label
    return scores["contents"].get(topic, {}).get(content)


def percentile(sorted_values: list[float], q: float) -> float:
    """Linear interpolation, q in [0, 1]; `sorted_values` must not be empty."""
    position = q * (len(sorted_values) - 1)
    low = int(position)
    high = min(low + 1, len(sorted_values) - 1)
    return sorted_values[low] + (sorted_values[high] - sorted_values[low]) * (
        position - low
    )


class MisalignedRuns(Exception):
    """The runs of a policy do not have the same sentences."""


def check_aligned(policy: str, runs: dict[str, dict]) -> None:
    reference_name, reference = next(iter(runs.items()))
    reference_texts = [e["text"] for e in reference["analyzed"]]
    for name, result in runs.items():
        if [e["text"] for e in result["analyzed"]] != reference_texts:
            raise MisalignedRuns(
                f"{policy}: runs {reference_name} and {name} have different sentences"
            )


# ---------------------------------------------------------------------------
# comparison
# ---------------------------------------------------------------------------


def summarize(entry_lists: list[list[dict]]) -> dict:
    """Label statistics of one run over all policies."""
    entries = scope_other = topic_other = with_content = 0
    totals = dict.fromkeys(LEVELS, 0)
    counts: dict[str, Counter] = {level: Counter() for level in LEVELS}

    for analyzed in entry_lists:
        for entry in analyzed:
            if not entry["text"]:
                continue  # structural entries without text of their own
            entries += 1
            sets = label_sets(entry)
            scope_other += sets["scope"] <= {"Unspecified"}
            topic_other += sets["topic"] <= {"Other"}
            with_content += bool(sets["content"])
            for level in LEVELS:
                totals[level] += len(sets[level])
                counts[level].update(format_label(label) for label in sets[level])

    n = max(entries, 1)
    return {
        "entries": entries,
        "scope_other_share": scope_other / n,
        "topic_other_share": topic_other / n,
        "with_content_share": with_content / n,
        "labels_per_entry": {level: totals[level] / n for level in LEVELS},
        "label_counts": {level: dict(counts[level]) for level in LEVELS},
    }


def propagation_totals(results: list[dict]) -> dict:
    """What propagation added and what the gate blocked, summed over policies.

    The pipeline propagates twice: after the scope and topic models, and again
    after the content models. The second pass looks at the same scopes and
    topics once more, so blocked scopes and topics are taken from the first
    pass only; blocked contents are taken from both (only the second has any).
    """
    totals = Counter()
    for result in results:
        first = result["stats"]["propagate"]["context_topic"]
        second = result["stats"]["propagate"]["content"]
        for stats in (first, second):
            totals["added_scopes"] += stats["contexts"].get("total", 0)
            totals["added_topics"] += stats["topics"].get("total", 0)
        for kind, blocked in first.get("blocked", {}).items():
            totals[f"blocked_{kind}"] += blocked.get("total", 0)
        blocked_contents = second.get("blocked", {}).get("contents", {})
        totals["blocked_contents"] += blocked_contents.get("total", 0)
    return {
        key: totals[key]
        for key in (
            "added_scopes",
            "added_topics",
            "blocked_contexts",
            "blocked_topics",
            "blocked_contents",
        )
    }


def compare_runs(a_lists: list[list[dict]], b_lists: list[list[dict]]) -> dict:
    """How the labels of run A and run B differ, sentence by sentence."""
    out = {}
    for level in LEVELS:
        entries = differing = only_a = only_b = 0
        jaccard_sum = 0.0
        gained: Counter = Counter()
        lost: Counter = Counter()
        for a_entries, b_entries in zip(a_lists, b_lists):
            for a, b in zip(a_entries, b_entries):
                if not a["text"]:
                    continue
                entries += 1
                a_set, b_set = label_sets(a)[level], label_sets(b)[level]
                union = a_set | b_set
                jaccard_sum += len(a_set & b_set) / len(union) if union else 1.0
                if a_set != b_set:
                    differing += 1
                only_a += len(a_set - b_set)
                only_b += len(b_set - a_set)
                lost.update(format_label(label) for label in a_set - b_set)
                gained.update(format_label(label) for label in b_set - a_set)
        out[level] = {
            "entries": entries,
            "differing_entries": differing,
            "differing_share": differing / max(entries, 1),
            "mean_jaccard": jaccard_sum / max(entries, 1),
            "labels_only_in_a": only_a,
            "labels_only_in_b": only_b,
            "top_only_in_a": lost.most_common(5),
            "top_only_in_b": gained.most_common(5),
        }
    return out


def added_label_scores(base_lists: list[list[dict]], run_lists: list[list[dict]]) -> dict:
    """For the labels `run` has and the baseline does not: how high the
    sentences scored those labels themselves (the scores are the run's own)."""
    out = {}
    for level in LEVELS:
        scores: list[float] = []
        added = 0
        for base_entries, run_entries in zip(base_lists, run_lists):
            for base, run in zip(base_entries, run_entries):
                if not base["text"]:
                    continue
                for label in label_sets(run)[level] - label_sets(base)[level]:
                    added += 1
                    score = own_score(run, level, label)
                    if score is not None:
                        scores.append(score)
        scores.sort()
        out[level] = {
            "added": added,
            "without_score": added - len(scores),
            "median": statistics.median(scores) if scores else None,
            "p10": percentile(scores, 0.1) if scores else None,
            "p90": percentile(scores, 0.9) if scores else None,
        }
    return out


def build_comparison(results: dict[str, dict[str, dict]], runs: dict) -> dict:
    """`results`: policy -> run -> (slim) result JSON, `runs`: run -> PropagationConfig."""
    run_names = list(runs)
    policies = sorted(results)
    for policy in policies:
        check_aligned(policy, results[policy])

    lists = {run: [results[p][run]["analyzed"] for p in policies] for run in run_names}

    per_policy = {}
    for policy in policies:
        base = results[policy][BASELINE]["analyzed"]
        row = {"entries": sum(1 for e in base if e["text"])}
        for run in run_names:
            if run == BASELINE:
                continue
            differing = 0
            for b, r in zip(base, results[policy][run]["analyzed"]):
                if b["text"] and any(
                    label_sets(b)[level] != label_sets(r)[level] for level in LEVELS
                ):
                    differing += 1
            row[f"differs_from_{BASELINE}:{run}"] = differing
        per_policy[policy] = row

    return {
        "policies": len(policies),
        "runs": {name: asdict(config) for name, config in runs.items()},
        "per_run": {
            run: {
                **summarize(lists[run]),
                "propagation": propagation_totals(
                    [results[p][run] for p in policies]
                ),
            }
            for run in run_names
        },
        "pairwise": {
            f"{a} vs {b}": compare_runs(lists[a], lists[b])
            for a, b in combinations(run_names, 2)
        },
        "added_vs_baseline": {
            run: added_label_scores(lists[BASELINE], lists[run])
            for run in run_names
            if run != BASELINE
        },
        "per_policy": per_policy,
    }


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _num(value: float | None) -> str:
    return "-" if value is None else f"{value:.2f}"


def _table(header: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return lines + [""]


def _describe(config: dict) -> str:
    if not config["enabled"]:
        return "headings pass nothing on"
    ratios = (
        config["context_floor_ratio"],
        config["topic_floor_ratio"],
        config["content_floor_ratio"],
    )
    if not any(ratios) and not config["min_score"]:
        return "headings pass everything on"
    return (
        f"gate: scope {ratios[0]}, topic {ratios[1]}, content {ratios[2]} x threshold"
        f", at least {config['min_score']}"
    )


def render_markdown(comparison: dict) -> str:
    lines = [
        "# Header propagation comparison",
        "",
        f"{comparison['policies']} policies, analyzed once per run with the same models "
        "and the same sentences; only header propagation differs.",
        "",
        "## Runs",
        "",
    ]
    lines += _table(
        ["run", "setting"],
        [[f"`{run}`", _describe(c)] for run, c in comparison["runs"].items()],
    )

    lines += ["## Per run", ""]
    rows = []
    for run, s in comparison["per_run"].items():
        p = s["propagation"]
        rows.append(
            [
                f"`{run}`",
                str(s["entries"]),
                _pct(s["scope_other_share"]),
                _pct(s["topic_other_share"]),
                _pct(s["with_content_share"]),
                " / ".join(_num(s["labels_per_entry"][level]) for level in LEVELS),
                f"{p['added_scopes']} / {p['added_topics']}",
                f"{p['blocked_contexts']} / {p['blocked_topics']} / {p['blocked_contents']}",
            ]
        )
    lines += _table(
        [
            "run",
            "sentences",
            "scope = Unspecified",
            "topic = Other",
            "with content",
            "labels per sentence (scope / topic / content)",
            "added by headers (scopes / topics)",
            "blocked (scopes / topics / contents)",
        ],
        rows,
    )

    lines += [
        "## Pairwise differences",
        "",
        "Per sentence label sets are compared; Jaccard 1.00 means identical labels.",
        "",
    ]
    rows = []
    for pair, levels in comparison["pairwise"].items():
        for level in LEVELS:
            c = levels[level]
            rows.append(
                [
                    f"`{pair}`",
                    level,
                    f"{c['differing_entries']} ({_pct(c['differing_share'])})",
                    _num(c["mean_jaccard"]),
                    str(c["labels_only_in_a"]),
                    str(c["labels_only_in_b"]),
                ]
            )
    lines += _table(
        ["A vs B", "level", "sentences that differ", "mean Jaccard", "labels only in A", "labels only in B"],
        rows,
    )

    lines += [
        "## What the headers add: scores of the sentences themselves",
        "",
        "Labels a run has that `no_propagation` does not, and the score the "
        "sentence's own model gave that label. The lower, the less the "
        "sentence itself supports what it inherited.",
        "",
    ]
    rows = []
    for run, levels in comparison["added_vs_baseline"].items():
        for level in LEVELS:
            a = levels[level]
            rows.append(
                [
                    f"`{run}`",
                    level,
                    str(a["added"]),
                    _num(a["median"]),
                    f"{_num(a['p10'])} - {_num(a['p90'])}",
                ]
            )
    lines += _table(["run", "level", "labels added", "median score", "10th - 90th percentile"], rows)

    lines += ["## Labels that differ most", ""]
    for pair, levels in comparison["pairwise"].items():
        lines.append(f"**`{pair}`**")
        lines.append("")
        for level in LEVELS:
            c = levels[level]
            only_b = ", ".join(f"{label} ({n})" for label, n in c["top_only_in_b"]) or "-"
            only_a = ", ".join(f"{label} ({n})" for label, n in c["top_only_in_a"]) or "-"
            lines.append(f"- {level}: only in B: {only_b}; only in A: {only_a}")
        lines.append("")

    lines += ["## Per policy", "", "Sentences whose labels differ from `no_propagation`.", ""]
    run_columns = [r for r in comparison["runs"] if r != BASELINE]
    rows = []
    for policy, row in comparison["per_policy"].items():
        rows.append(
            [policy, str(row["entries"])]
            + [str(row[f"differs_from_{BASELINE}:{run}"]) for run in run_columns]
        )
    lines += _table(["policy", "sentences"] + [f"`{r}`" for r in run_columns], rows)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# running
# ---------------------------------------------------------------------------


def slim(result_json: dict) -> dict:
    return {key: result_json[key] for key in KEPT_KEYS}


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare header propagation settings on saved policies "
        "(see the module docstring)."
    )
    parser.add_argument(
        "--raw",
        type=Path,
        action="append",
        help="folder with saved policy HTML files (repeatable; default: PrivaScopeWeb/raw)",
    )
    parser.add_argument("--pattern", default="*.html", help="file pattern (default: *.html)")
    parser.add_argument("--limit", type=int, help="only the first N files of each folder")
    parser.add_argument("--out", type=Path, default=Path("propagation_comparison"))
    parser.add_argument("--mild", type=float, default=0.5, help="floor ratio of confidence_mild")
    parser.add_argument("--strict", type=float, default=0.8, help="floor ratio of confidence_strict")
    parser.add_argument(
        "--min-score", type=float, default=0.0, help="absolute lower bound of the floors"
    )
    parser.add_argument("--language", default="en", choices=["en", "de"])
    parser.add_argument("--full", action="store_true", help="keep html, structure and text in the run results")
    parser.add_argument(
        "--resume", action="store_true", help="reuse results already in --out (same settings only)"
    )
    parser.add_argument(
        "--no-preload", action="store_true", help="do not load all models once up front"
    )
    return parser.parse_args(argv)


def find_policies(args: argparse.Namespace) -> list[tuple[str, Path]]:
    folders = args.raw or [DEFAULT_RAW]
    found: list[tuple[str, Path]] = []
    for folder in folders:
        if not folder.is_dir():
            raise SystemExit(f"not a folder: {folder} (use --raw)")
        files = sorted(folder.glob(args.pattern))
        if args.limit:
            files = files[: args.limit]
        for path in files:
            name = path.stem if len(folders) == 1 else f"{folder.parent.name}__{path.stem}"
            found.append((name, path))
    return found


def main(argv: list[str] | None = None, configs: dict | None = None) -> int:
    """`configs`: pipeline configurations to use instead of the default ones."""
    args = parse_args(argv)

    from privacy_policy_analyzer import Language
    from privacy_policy_analyzer.config import DEFAULT_CONFIGURATIONS
    from privacy_policy_analyzer.crawl import CollectedPolicy
    from privacy_policy_analyzer.pipeline import Pipeline, PolicyResult
    from privacy_policy_analyzer.shared.logging import set_logging

    runs = make_runs(args.mild, args.strict, args.min_score)
    files = find_policies(args)
    if not files:
        print("no policies found", file=sys.stderr)
        return 1

    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    set_logging(level=logging.INFO, file=str(out / "compare.log"))

    settings = {name: asdict(config) for name, config in runs.items()}
    settings_file = out / "runs.json"
    if args.resume and settings_file.exists():
        if json.loads(settings_file.read_text(encoding="utf-8")) != settings:
            print(f"--resume: the settings in {settings_file} differ from the current ones", file=sys.stderr)
            return 2
    settings_file.write_text(json.dumps(settings, indent=2), encoding="utf-8")

    language = Language(args.language)
    base_config = (configs or DEFAULT_CONFIGURATIONS)[language]
    base_pipeline = Pipeline(
        configs={language: base_config},
        prefer_onnx=False,
        cache_load_models=not args.no_preload,
    )
    # one pipeline per run; they share everything but the propagation setting
    pipelines = {}
    for run, propagation in runs.items():
        pipeline = copy.copy(base_pipeline)
        pipeline.configs = {language: replace(base_config, propagation=propagation)}
        pipelines[run] = pipeline

    results: dict[str, dict[str, dict]] = {}
    for index, (name, path) in enumerate(files, start=1):
        files_of_policy = {run: out / run / f"{name}.json" for run in runs}
        if args.resume and all(f.exists() for f in files_of_policy.values()):
            results[name] = {
                run: json.loads(f.read_text(encoding="utf-8"))
                for run, f in files_of_policy.items()
            }
            print(f"[{index}/{len(files)}] {name}: reused")
            continue

        policy = CollectedPolicy.from_parts(
            splitter_config=base_config.splitter_configs,
            name=name,
            source=str(path),
            language=language,
            date=date.today(),
            html=path.read_text(encoding="utf-8", errors="replace"),
            structured_raw=None,
            harmonized_raw=None,
            text=None,
        )

        per_run: dict[str, dict] = {}
        for run, pipeline in pipelines.items():
            result = pipeline.run_with_policy(policy)
            if not isinstance(result, PolicyResult):
                print(f"[{index}/{len(files)}] {name}: skipped, {run} failed: {result}", file=sys.stderr)
                per_run = {}
                break
            per_run[run] = result.to_json() if args.full else slim(result.to_json())

        if not per_run:
            continue
        for run, data in per_run.items():
            (out / run).mkdir(exist_ok=True)
            files_of_policy[run].write_text(
                json.dumps(data, ensure_ascii=False, default=str), encoding="utf-8"
            )
        results[name] = per_run
        print(f"[{index}/{len(files)}] {name}: {len(per_run[BASELINE]['analyzed'])} entries")

    if not results:
        print("no policy could be analyzed", file=sys.stderr)
        return 1

    comparison = build_comparison(results, runs)
    (out / "comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    (out / "comparison.md").write_text(render_markdown(comparison), encoding="utf-8")
    print(f"\n{len(results)} policies compared, see {out / 'comparison.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
