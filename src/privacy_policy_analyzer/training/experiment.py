"""Runs several models over several tasks on one frozen split."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from privacy_policy_analyzer.shared.logging import get_logger
from privacy_policy_analyzer.training.config import TrainingConfig
from privacy_policy_analyzer.training.data import (
    Task,
    extract_samples,
    read_annotation_schema,
)
from privacy_policy_analyzer.training.split import (
    DEFAULT_RATIOS,
    PARTITIONS,
    DataSplit,
    Ratios,
    SplitBy,
    load_corpus,
    prepare_split,
)

logger = get_logger(__name__)

SPLIT_FILE = "split.json"


def describe_plan(split: DataSplit, tasks: Sequence[Task], schema) -> str:
    """Per task: samples per partition, and labels a partition has no positive for."""

    lines = [
        f"split {split.hash} (seed={split.seed}, ratios={split.ratios}, by={split.by}, "
        f"stratify={split.stratify})",
        *(
            f"  {p:<5} policies: {', '.join(split.policies[p]) or '-'}"
            for p in PARTITIONS
            if split.by == "policy"
        ),
        f"  {split.summary()}",
        "",
        f"{'task':<28}{'train':>7}{'eval':>7}{'test':>7}  labels without positives",
    ]
    for task in tasks:
        label2id = task.label2id(schema)
        names = list(label2id)
        parts = {p: extract_samples(split.items(p), task, label2id) for p in PARTITIONS}
        gaps = []
        for p, samples in parts.items():
            empty = [n for n, c in samples.support(names).items() if c == 0 and n != task.fallback]
            if empty and len(samples):
                gaps.append(f"{p}: {len(empty)}")
        lines.append(
            f"{str(task):<28}{len(parts['train']):>7}{len(parts['eval']):>7}"
            f"{len(parts['test']):>7}  {', '.join(gaps) or '-'}"
        )
    return "\n".join(lines)


def format_summary(results: Sequence) -> str:
    """Table of finished runs; the scores are test F1 at threshold 0.5."""

    width = max([len("model")] + [len(r.model_name) for r in results]) + 2
    rows = [f"{'model':<{width}}{'task':<26}{'status':<9}{'f1_macro':>9}{'f1_micro':>9}"]
    for r in results:
        m = r.metrics or {}
        macro = f"{m['f1_macro']:.3f}" if "f1_macro" in m else "-"
        micro = f"{m['f1_micro']:.3f}" if "f1_micro" in m else "-"
        rows.append(f"{r.model_name:<{width}}{str(r.task):<26}{r.status:<9}{macro:>9}{micro:>9}")
        if r.reason:
            rows.append(f"    {r.reason}")
    return "\n".join(rows)


def run_experiment(
    data_dir: Path,
    schema_file: Path,
    out_dir: Path,
    models: Sequence[str],
    tasks: Sequence[Task] | None = None,
    config: TrainingConfig = TrainingConfig(),
    ratios: Ratios = DEFAULT_RATIOS,
    split_by: SplitBy = "policy",
    resplit: bool = False,
    force: bool = False,
    dry_run: bool = False,
    stratify: bool = True,
) -> list:
    """Trains every model on every task (default: all tasks of the schema).

    The data is split once and the split is frozen to ``<out_dir>/split.json``,
    so all models and tasks share train/eval/test and reruns reproduce it.
    ``split_by="policy"`` (default) keeps each policy whole in one partition and
    splits synthetic and individual sentences one by one; ``"sentence"`` splits every
    sentence individually (leaks near-duplicates across partitions). ``stratify``
    (default) distributes the sentences split one by one label by label, so every
    label reaches train, eval and test where possible. Runs that already finished
    with identical inputs are skipped unless ``force``.
    ``dry_run`` only prints the split and the per-task sample counts.
    """

    out_dir = Path(out_dir)
    corpus = load_corpus(Path(data_dir))
    schema = read_annotation_schema(Path(schema_file))
    tasks = list(tasks) if tasks is not None else Task.all(schema)

    if dry_run:
        # same split as a real run, but nothing is written
        manifest = out_dir / SPLIT_FILE
        split = prepare_split(
            corpus, manifest if manifest.exists() else None, config.seed, ratios, resplit,
            split_by, stratify,
        )
        print(describe_plan(split, tasks, schema))
        return []

    from privacy_policy_analyzer.training.trainer import train  # needs torch
    from privacy_policy_analyzer.training.util import set_global_seed

    set_global_seed(config.seed, config.deterministic)
    split = prepare_split(
        corpus, out_dir / SPLIT_FILE, config.seed, ratios, resplit, split_by, stratify
    )

    results = []
    for model_name in models:
        for task in tasks:
            results.append(train(model_name, task, split, schema, out_dir, config, force))
    print(format_summary(results))
    return results
