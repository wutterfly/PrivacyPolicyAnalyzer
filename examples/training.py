"""Train classifiers on annotated policies.

Equivalent command line:

    python -m privacy_policy_analyzer.training --data DATA --schema SCHEMA --out OUT \
        --models distilbert-base-uncased --tasks scope topic content:UserRights
"""

import logging
from pathlib import Path

from privacy_policy_analyzer.shared.logging import set_logging
from privacy_policy_analyzer.training import (
    Task,
    TrainingConfig,
    label_distribution,
    load_corpus,
    prepare_split,
    read_annotation_schema,
    run_experiment,
)
from privacy_policy_analyzer.training.util import disable_logging

if __name__ == "__main__":
    disable_logging()  # silence other libraries
    set_logging("training.log", level=logging.INFO)

    # input and output paths
    data_dir = Path(...)  # folder with the annotated *.json files
    schema_file = Path(...)  # annotation_schema.json
    out_dir = Path(...)  # models, results and the frozen split.json go here

    config = TrainingConfig(seed=42)

    # look at the data and the split before training (nothing is trained here)
    corpus = load_corpus(data_dir)
    split = prepare_split(corpus, out_dir / "split.json", seed=config.seed, by="policy")
    print("train label distribution:", label_distribution(split.items("train")))

    # train every model on the chosen tasks; omit `tasks` for scope, topic and all content tasks
    run_experiment(
        data_dir=data_dir,
        schema_file=schema_file,
        out_dir=out_dir,
        models=["distilbert-base-uncased"],
        tasks=[Task("scope"), Task("topic"), Task("content", "UserRights")],
        config=config,
        split_by="policy",  # or "sentence" for a plain per-sentence split
    )
