"""Label schema, training tasks and conversion of annotated entries to arrays.

Light on purpose (numpy only): everything torch / datasets related lives in
``trainer.py``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Sequence

import numpy as np

from privacy_policy_analyzer.shared.annotation import OTHER, UNSPECIFIED_SCOPE
from privacy_policy_analyzer.training.split import Item

Level = Literal["scope", "topic", "content"]


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

    with Path(schema_file).open("r", encoding="utf-8") as f:
        return LabelSchema.from_dict(json.load(f))


def build_label2id(labels: Sequence[str], fallback: str) -> dict[str, int]:
    """Label to ID mapping with the fallback label ('Other' / 'Unspecified') first."""

    label2id: dict[str, int] = {fallback: 0}
    for label in labels:
        label2id.setdefault(label, len(label2id))
    return label2id


def slugify(name: str) -> str:
    """File-system safe name: ``mukund/privbert`` -> ``mukund_privbert``."""

    return re.sub(r"[^\w.\-]+", "_", name)


@dataclass(frozen=True)
class Task:
    """One classifier to train: the scope model, the topic model, or the content
    model of one topic."""

    level: Level
    topic: str | None = None  # only for level == "content"

    def __post_init__(self) -> None:
        if self.level not in ("scope", "topic", "content"):
            raise ValueError(f"Unknown level: {self.level!r}")
        if (self.level == "content") != (self.topic is not None):
            raise ValueError("A topic is required for (and only for) level 'content'")

    @staticmethod
    def parse(text: str) -> "Task":
        """``scope``, ``topic`` or ``content:<Topic>`` (e.g. ``content:Security/Privacy``)."""

        level, _, topic = text.partition(":")
        return Task(level, topic or None)  # type: ignore[arg-type]

    @staticmethod
    def all(schema: LabelSchema) -> list["Task"]:
        """Scope, topic and one content task per topic that has content labels."""

        return [Task("scope"), Task("topic")] + [
            Task("content", topic)
            for topic, contents in schema.topicContents.items()
            if contents
        ]

    def __str__(self) -> str:
        return self.level if self.topic is None else f"{self.level}:{self.topic}"

    @property
    def path(self) -> Path:
        """Relative output location, e.g. ``content/Security_Privacy``."""

        return Path(self.level) / (slugify(self.topic) if self.topic else "")

    @property
    def fallback(self) -> str:
        return UNSPECIFIED_SCOPE if self.level == "scope" else OTHER

    @property
    def default_oversampling(self) -> float:
        return 0.5 if self.level != "content" else 0.7

    def labels(self, schema: LabelSchema) -> list[str]:
        if self.level == "scope":
            return schema.scope
        if self.level == "topic":
            return schema.topics
        assert self.topic is not None
        if self.topic not in schema.topicContents:
            raise ValueError(f"Schema has no content labels for topic {self.topic!r}")
        return schema.topicContents[self.topic]

    def label2id(self, schema: LabelSchema) -> dict[str, int]:
        return build_label2id(self.labels(schema), self.fallback)


@dataclass
class Samples:
    """Multi-hot encoded sentences of one partition for one task."""

    texts: list[str]
    labels: np.ndarray  # (n, n_labels) float32 multi-hot
    synthetic: np.ndarray  # (n,) bool

    def __len__(self) -> int:
        return len(self.texts)

    def subset(self, mask_or_idx: np.ndarray) -> "Samples":
        idx = np.flatnonzero(mask_or_idx) if mask_or_idx.dtype == bool else mask_or_idx
        return Samples(
            [self.texts[i] for i in idx], self.labels[idx], self.synthetic[idx]
        )

    def support(self, label_names: Sequence[str]) -> dict[str, int]:
        return {n: int(self.labels[:, i].sum()) for i, n in enumerate(label_names)}


def extract_samples(items: Sequence[Item], task: Task, label2id: dict[str, int]) -> Samples:
    """Turns annotated sentences into multi-hot rows for ``task``.

    Content tasks only use sentences annotated with the task's topic.
    """

    def flag(names: list[str], where: str) -> np.ndarray:
        row = np.zeros(len(label2id), dtype=np.float32)
        for name in names:
            if name not in label2id:
                raise ValueError(
                    f"{where}: label {name!r} is not in the {task} label set "
                    f"{sorted(label2id)}"
                )
            row[label2id[name]] = 1.0
        return row

    texts: list[str] = []
    rows: list[np.ndarray] = []
    synthetic: list[bool] = []
    for item in items:
        e = item.entry
        where = f"{item.source} line {e.line_number}"
        if task.level == "scope":
            row = flag(e.scopes, where)
        elif task.level == "topic":
            row = flag([t.topic for t in e.topics], where)
        else:
            matching = [t for t in e.topics if t.topic == task.topic]
            if not matching:
                continue
            row = flag([c.content for t in matching for c in t.contents], where)
        texts.append(e.text)
        rows.append(row)
        synthetic.append(item.synthetic)

    labels = np.stack(rows) if rows else np.zeros((0, len(label2id)), dtype=np.float32)
    return Samples(texts, labels, np.array(synthetic, dtype=bool))


def oversample_indices(labels: np.ndarray, ratio: float) -> np.ndarray:
    """Row indices for a training set where rare labels are repeated.

    Every label with fewer than ``ratio * (count of the most frequent label)``
    positives gets copies of its positive rows (round robin, deterministic) until
    it reaches that target. The result starts with all original rows.
    """

    n = len(labels)
    if n == 0:
        return np.arange(0)
    pos_counts = labels.sum(axis=0)
    target = int(pos_counts.max() * ratio)

    extra: list[int] = []
    for label_idx in range(labels.shape[1]):
        missing = target - int(pos_counts[label_idx])
        positives = np.flatnonzero(labels[:, label_idx] > 0.5)
        if missing <= 0 or len(positives) == 0:
            continue
        copies, remainder = divmod(missing, len(positives))
        extra.extend(np.repeat(positives, copies).tolist())
        extra.extend(positives[:remainder].tolist())

    return np.concatenate([np.arange(n), np.array(extra, dtype=int)])


def label_distribution(items: Sequence[Item]) -> dict:
    """Counts of scopes, topics and contents per topic over the given sentences."""

    scopes: dict[str, int] = {}
    topics: dict[str, int] = {}
    contents: dict[str, dict[str, int]] = {}
    for item in items:
        for scope in item.entry.scopes:
            scopes[scope] = scopes.get(scope, 0) + 1
        for tpc in item.entry.topics:
            topics[tpc.topic] = topics.get(tpc.topic, 0) + 1
            for cnt in tpc.contents:
                per_topic = contents.setdefault(tpc.topic, {})
                per_topic[cnt.content] = per_topic.get(cnt.content, 0) + 1
    return {"len": len(items), "scopes": scopes, "topics": topics, "contents": contents}
