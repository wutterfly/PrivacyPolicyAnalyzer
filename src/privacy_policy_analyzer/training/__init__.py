"""Fine-tuning of the scope / topic / content classifiers.

Command line::

    python -m privacy_policy_analyzer.training --data DIR --schema FILE --out DIR \\
        --models distilbert-base-uncased [--tasks scope topic content:UserRights] [--dry-run]

Python::

    corpus = load_corpus(data_dir)
    split = prepare_split(corpus, out_dir / "split.json", seed=42)
    train("distilbert-base-uncased", Task("scope"), split, schema, out_dir)

or ``run_experiment(...)`` for several models and tasks at once. Data is split by
policy (see ``split.py``); the split is frozen to ``split.json`` next to the models.
"""

from privacy_policy_analyzer.training.config import TrainingConfig
from privacy_policy_analyzer.training.data import (
    LabelSchema,
    Task,
    label_distribution,
    read_annotation_schema,
)
from privacy_policy_analyzer.training.experiment import run_experiment
from privacy_policy_analyzer.training.split import (
    Corpus,
    DataSplit,
    load_corpus,
    make_split,
    prepare_split,
)

__all__ = [
    "Corpus",
    "DataSplit",
    "LabelSchema",
    "Task",
    "TrainResult",
    "TrainingConfig",
    "label_distribution",
    "load_corpus",
    "make_split",
    "prepare_split",
    "read_annotation_schema",
    "run_experiment",
    "train",
]


def __getattr__(name: str):
    # torch / transformers / datasets are only loaded when training is requested
    if name in ("train", "TrainResult"):
        from privacy_policy_analyzer.training import trainer

        return getattr(trainer, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
