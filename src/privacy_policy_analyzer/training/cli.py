"""Command line interface: ``python -m privacy_policy_analyzer.training``."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from privacy_policy_analyzer.training.config import TrainingConfig
from privacy_policy_analyzer.training.data import Task
from privacy_policy_analyzer.training.experiment import run_experiment
from privacy_policy_analyzer.training.split import DEFAULT_RATIOS

_DEFAULTS = TrainingConfig()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m privacy_policy_analyzer.training",
        description="Fine-tune the scope / topic / content classifiers. The annotated "
        "data is split into train/eval/test (by policy unless --split-by sentence; "
        "synthetic and individual sentences are always split sentence by sentence, label by label "
        "unless --no-stratify); the split is frozen to <out>/split.json.",
    )
    g = p.add_argument_group("inputs and outputs")
    g.add_argument("--data", type=Path, required=True, help="folder with the annotated *.json files")
    g.add_argument("--schema", type=Path, required=True, help="annotation_schema.json")
    g.add_argument("--out", type=Path, required=True, help="output folder for models, results and split.json")
    g.add_argument("--models", nargs="+", required=True, metavar="MODEL", help="Hugging Face model names or local paths")
    g.add_argument(
        "--tasks", nargs="+", default=["all"], metavar="TASK",
        help="'all' (default), or any of: scope, topic, content:<Topic> (e.g. content:Security/Privacy)",
    )

    g = p.add_argument_group("data split")
    g.add_argument("--split", nargs=3, type=float, default=DEFAULT_RATIOS, metavar=("TRAIN", "EVAL", "TEST"), help="split ratios (default: %(default)s)")
    g.add_argument(
        "--split-by", choices=["policy", "sentence"], default="policy",
        help="policy (default): each policy goes whole into one partition, so nothing leaks "
        "between partitions; sentence: every sentence is split individually (optimistic scores)",
    )
    g.add_argument(
        "--no-stratify", action="store_true",
        help="split synthetic / individual sentences at random instead of label by label "
        "(the default stratified split puts every label into train, eval and test where possible)",
    )
    g.add_argument("--resplit", action="store_true", help="overwrite an existing split.json")

    g = p.add_argument_group("training")
    g.add_argument("--seed", type=int, default=_DEFAULTS.seed)
    g.add_argument("--epochs", type=int, default=_DEFAULTS.epochs)
    g.add_argument("--lr", type=float, default=_DEFAULTS.learning_rate, dest="learning_rate")
    g.add_argument("--batch-size", type=int, default=_DEFAULTS.batch_size)
    g.add_argument("--grad-accum", type=int, default=_DEFAULTS.grad_accum_steps, dest="grad_accum_steps")
    g.add_argument("--max-length", type=int, default=_DEFAULTS.max_length)
    g.add_argument("--oversampling", type=float, default=None, help="rare-label oversampling ratio (default: 0.5 scope/topic, 0.7 content)")
    g.add_argument("--max-copies", type=int, default=_DEFAULTS.oversampling_max_copies, dest="oversampling_max_copies", help="at most this many extra copies of one sentence when oversampling, 0 or less: no limit (default: %(default)s)")
    g.add_argument("--precision", choices=["auto", "fp32", "fp16", "bf16"], default=_DEFAULTS.precision)
    g.add_argument("--optim", default=_DEFAULTS.optim)
    g.add_argument("--no-deterministic", action="store_true", help="allow non-deterministic GPU kernels (faster)")

    g = p.add_argument_group("execution")
    g.add_argument("--force", action="store_true", help="retrain runs that already finished with identical inputs")
    g.add_argument("--dry-run", action="store_true", help="print the split and per-task sample counts, train nothing")
    g.add_argument("--log-file", type=Path, default=None)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.dry_run:
        from privacy_policy_analyzer.training.util import disable_logging

        disable_logging()
    from privacy_policy_analyzer.shared.logging import set_logging

    set_logging(str(args.log_file) if args.log_file else None, level=logging.INFO)

    config = TrainingConfig(
        seed=args.seed,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        batch_size=args.batch_size,
        grad_accum_steps=args.grad_accum_steps,
        max_length=args.max_length,
        oversampling=args.oversampling,
        oversampling_max_copies=args.oversampling_max_copies if args.oversampling_max_copies > 0 else None,
        precision=args.precision,
        optim=args.optim,
        deterministic=not args.no_deterministic,
    )
    tasks = None if args.tasks == ["all"] else [Task.parse(t) for t in args.tasks]

    run_experiment(
        data_dir=args.data,
        schema_file=args.schema,
        out_dir=args.out,
        models=args.models,
        tasks=tasks,
        config=config,
        ratios=tuple(args.split),
        split_by=args.split_by,
        resplit=args.resplit,
        force=args.force,
        dry_run=args.dry_run,
        stratify=not args.no_stratify,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
