import logging
from logging import info
from pathlib import Path

from privacy_policy_analyzer.shared.annotation import (
    RawEntry,
    read_training_data,
)
from privacy_policy_analyzer.shared.logging import set_logging
from privacy_policy_analyzer.training import ModelTrainingConfig, get_label_distribution
from privacy_policy_analyzer.training.data import (
    LabelSchema,
    read_annotation_schema,
)
from privacy_policy_analyzer.training.util import (
    disable_logging,
    set_global_seed,
)

if __name__ == "__main__":
    SEED: int = 42
    set_global_seed(SEED)

    # disable logging from other modules
    disable_logging()
    set_logging("training.log", level=logging.INFO)

    model_name = "distilbert-base-uncased"

    # input and output paths
    training_folder: Path = Path(...)
    annotation_schema_file: Path = Path(...)
    output_dir: Path = Path(...)

    # read training data and annotation schema
    training_files: list[list[RawEntry]] = read_training_data(training_folder)
    schema: LabelSchema = read_annotation_schema(annotation_schema_file)

    # check label distributions
    info(
        "Label distributions in training data:", get_label_distribution(training_files)
    )

    # define training configurations
    configs = [
        ModelTrainingConfig(
            model_name=model_name,
            output_dir=output_dir / Path("context"),
            training_files=training_files,
            labels=schema.context,
            scope="context",
            content_topic=None,
            train_eval_test_split=(0.7, 0.15, 0.15),
            oversampling_ratio=0.5,
            seed=SEED,
        ),
        ModelTrainingConfig(
            model_name=model_name,
            output_dir=output_dir / Path("topic"),
            training_files=training_files,
            labels=schema.topics,
            scope="topic",
            content_topic=None,
            train_eval_test_split=(0.7, 0.15, 0.15),
            oversampling_ratio=0.5,
            seed=SEED,
        ),
        ModelTrainingConfig(
            model_name=model_name,
            output_dir=output_dir / Path("content") / Path("UserRights"),
            training_files=training_files,
            labels=schema.topicContents["UserRights"],
            scope="content",
            content_topic="UserRights",
            train_eval_test_split=(0.7, 0.15, 0.15),
            oversampling_ratio=0.7,
            seed=SEED,
        ),
        # ....
    ]

    # execute training for each configuration
    for config in configs:
        config.execute_training()
