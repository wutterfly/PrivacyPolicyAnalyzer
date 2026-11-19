import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from datasets import Dataset, DatasetInfo, concatenate_datasets
from sklearn.model_selection import train_test_split

from privacy_policy_analyzer.shared.annotation import RawEntry
from privacy_policy_analyzer.shared.logging import get_logger

logger = get_logger(__name__)


def _build_label2id_map(labels: list[str], fallback: str = "Other") -> dict[str, int]:
    """Build label to ID mapping with the fallback label as the first label.

    The fallback is 'Other' for topics and contents and 'Unspecified' for scopes.
    """
    label2id: dict[str, int] = {fallback: 0}
    for label in labels:
        if label not in label2id:
            label2id[label] = len(label2id)
    return label2id


@dataclass
class LabelSchema:
    """Schema for sentence labeling annotation."""

    scope: list[str]
    topics: list[str]
    topicContents: dict[str, list[str]]
    contentAttributes: dict[str, list[str]]
    # second scope layer: scope -> allowed specific values (empty for schemas without it)
    scopeSpecifics: dict[str, list[str]] = field(default_factory=dict)

    @staticmethod
    def from_dict(schema_dict: dict) -> "LabelSchema":
        return LabelSchema(
            scope=schema_dict.get("scope", []),
            topics=schema_dict.get("topics", []),
            topicContents=schema_dict.get("topicContents", {}),
            contentAttributes=schema_dict.get("contentAttributes", {}),
            scopeSpecifics=schema_dict.get("scopeSpecifics", {}),
        )


def read_annotation_schema(schema_file: Path) -> LabelSchema:
    """Read annotation schema from a JSON file."""

    with schema_file.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    return LabelSchema.from_dict(schema)


def extract_training_data_scope(
    raw_data: list[list[RawEntry]], label2id: dict[str, int]
) -> Dataset:
    num_labels: int = len(label2id)

    # Extract data
    data: dict[str, list] = {"text": [], "labels": []}
    for raw in raw_data:
        for entry in raw:
            scope_flags: list[float] = [0.0] * num_labels
            for scope in entry.scopes:
                scope_flags[label2id[scope]] = 1.0

            data["text"].append(entry.text)
            data["labels"].append(scope_flags)

    # Create Dataset
    return Dataset.from_dict(data, info=DatasetInfo(description="scope"))


def extract_training_data_topics(
    raw_data: list[list[RawEntry]], label2id: dict[str, int]
) -> Dataset:
    num_labels: int = len(label2id)

    # Extract data
    data: dict[str, list] = {"text": [], "labels": []}
    for raw in raw_data:
        for entry in raw:
            topic_flags: list[float] = [0.0] * num_labels
            for topic in entry.topics:
                topic_flags[label2id[topic.topic]] = 1.0

            data["text"].append(entry.text)
            data["labels"].append(topic_flags)

    # Create Dataset
    return Dataset.from_dict(data, info=DatasetInfo(description="topic"))


def extract_training_data_content(
    raw_data: list[list[RawEntry]], label2id: dict[str, int], topic: str
) -> Dataset:
    num_labels: int = len(label2id)
    data: dict[str, list] = {"text": [], "labels": []}
    for i, raw in enumerate(raw_data):
        for entry in raw:
            for topic_annotation in entry.topics:
                if topic_annotation.topic == topic:
                    content_flags: list[float] = [0.0] * num_labels
                    for content_annotation in topic_annotation.contents:
                        if content_annotation.content not in label2id:
                            logger.error(
                                "Content label not in label2id mapping: label=%s",
                                content_annotation.content,
                            )
                            logger.error(
                                "Error in entry: index=%d text=%s", i, entry.text
                            )
                        content_flags[label2id[content_annotation.content]] = 1.0

                    data["text"].append(entry.text)
                    data["labels"].append(content_flags)
    return Dataset.from_dict(data, info=DatasetInfo(description=f"content_{topic}"))


def split_dataset(
    dataset: Dataset, test_size: float, seed: int
) -> tuple[Dataset, Dataset]:
    indices = np.arange(len(dataset))

    train_indices, test_indices = train_test_split(
        indices, test_size=test_size, random_state=seed
    )

    # Create datasets from indices
    train_dataset = dataset.select(train_indices.tolist())
    eval_dataset = dataset.select(test_indices.tolist())

    return train_dataset, eval_dataset


def oversample_minority_labels(dataset: Dataset, ratio: float):
    labels_array = np.array([example["labels"] for example in dataset])
    for x, y in zip(labels_array, np.array(dataset["labels"])):
        assert np.array_equal(x, y)
    pos_counts = labels_array.sum(axis=0)
    n_labels = labels_array.shape[1]

    max_count = int(pos_counts.max())
    target_count = int(max_count * ratio)

    all_indices_to_add = []

    for label_idx in range(n_labels):
        current_count = int(pos_counts[label_idx])

        if current_count >= target_count:
            continue

        indices_with_label = np.where(labels_array[:, label_idx] > 0.5)[0].tolist()

        if len(indices_with_label) == 0:
            continue

        samples_needed = target_count - current_count

        # Calculate how many times to duplicate each sample
        copies_per_sample = samples_needed // len(indices_with_label)
        remainder = samples_needed % len(indices_with_label)

        # Add full copies for all samples
        for idx in indices_with_label:
            all_indices_to_add.extend([idx] * copies_per_sample)

        # Add remainder copies to first N samples (deterministic)
        for i in range(remainder):
            all_indices_to_add.append(indices_with_label[i])

    if len(all_indices_to_add) == 0:
        return dataset

    oversampled_subset = dataset.select(all_indices_to_add)
    balanced_dataset = concatenate_datasets([dataset, oversampled_subset])

    return balanced_dataset
