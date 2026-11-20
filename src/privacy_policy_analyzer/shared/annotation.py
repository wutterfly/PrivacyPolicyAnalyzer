import json
from dataclasses import dataclass, field
from pathlib import Path

from privacy_policy_analyzer.shared.logging import get_logger

logger = get_logger(__name__)

# Fallback labels used when no real label applies: scopes (scopes) fall back
# to "Unspecified", topics and contents fall back to "Other".
UNSPECIFIED_SCOPE = "Unspecified"
OTHER = "Other"


@dataclass
class ContentAnnotation:
    """An annotated content within a topic."""

    content: str
    attributes: list[str]


@dataclass
class TopicAnnotation:
    """An annotated topic within a training entry."""

    topic: str
    contents: list[ContentAnnotation]


@dataclass
class EntryScores:
    """Raw model scores for a single entry, for every label the models
    returned - not only the ones above their threshold.

    Filled in by the classification stage and used by gated header
    propagation. Transient: never serialized with the analysis results.
    """

    scopes: dict[str, float] = field(default_factory=dict)
    topics: dict[str, float] = field(default_factory=dict)
    # topic -> content -> score; only for topics the entry had when the
    # content model of that topic ran
    contents: dict[str, dict[str, float]] = field(default_factory=dict)


@dataclass
class RawEntry:
    """A single annotated entry in the training data."""

    line_number: int
    text: str
    scopes: list[str]
    topics: list[TopicAnnotation]
    scores: EntryScores = field(default_factory=EntryScores, repr=False, compare=False)
    # second scope layer: for every scope with specifics (e.g. Device, Communication,
    # Event/Program) a list of specific values, possibly empty, e.g. {"Device": ["Camera"]}
    scope_specifics: dict[str, list[str]] = field(default_factory=dict)


def read_raw_entry(data: dict) -> RawEntry:
    """Reads a single raw entry from a dictionary."""

    line_number = data["line_number"]
    text = data["text"]
    scopes = data.get("annotations", data)["scopes"]
    assert all(isinstance(scope, str) for scope in scopes), (
        "All scopes must be strings"
    )
    annotations_ = data.get("annotations", data)
    assert "scopeSpecifics" in annotations_, "scopeSpecifics is required"
    scope_specifics_ = annotations_["scopeSpecifics"]
    assert isinstance(scope_specifics_, dict) and all(
        isinstance(scope, str)
        and isinstance(values, list)
        and all(isinstance(value, str) for value in values)
        for scope, values in scope_specifics_.items()
    ), "scopeSpecifics must map a scope to a list of strings"
    assert all(scope in scopes for scope in scope_specifics_), (
        "scopeSpecifics may only have keys of selected scopes"
    )
    scope_specifics = {scope: list(values) for scope, values in scope_specifics_.items()}
    topics_ = data.get("annotations", data)["topics"]
    topics = []
    try:
        for topic_data in topics_:
            contents = []
            for content_data in topic_data["contents"]:
                assert isinstance(content_data["content"], str), (
                    "Content must be a string"
                )
                assert all(
                    isinstance(attr, str) for attr in content_data["attributes"]
                ), "All attributes must be strings"
                content_annotation = ContentAnnotation(
                    content=content_data["content"],
                    attributes=content_data["attributes"],
                )
                contents.append(content_annotation)
            assert isinstance(topic_data["topic"], str), "Topic must be a string"
            topic_annotation = TopicAnnotation(
                topic=topic_data["topic"],
                contents=contents,
            )
            topics.append(topic_annotation)
    except Exception as e:
        logger.error("Error parsing topics for line_number=%d: %s", line_number, e)
        logger.error("Data: %s", data)

    return RawEntry(
        line_number=line_number,
        text=text,
        scopes=scopes,
        topics=topics,
        scope_specifics=scope_specifics,
    )


def read_training_documents(folder: Path) -> list[tuple[str, list[RawEntry]]]:
    """Reads all annotated files from the folder as ``(name, entries)`` pairs.

    The name is the file stem. Files are returned sorted by name so the result
    does not depend on the order the file system lists them in.
    """

    documents: list[tuple[str, list[RawEntry]]] = []
    for filename in sorted(folder.glob("*.json"), key=lambda p: p.name):
        try:
            with filename.open("r", encoding="utf-8") as f:
                content: list[dict] = json.load(f)
            documents.append((filename.stem, [read_raw_entry(e) for e in content]))
        except Exception as e:
            logger.error("Error reading file=%s: %s", filename, e)

    logger.info("Loaded %d training files from folder=%s", len(documents), folder)
    return documents


def read_training_data(folder: Path) -> list[list[RawEntry]]:
    """Reads all training data from the specified folder (entries only)."""

    return [entries for _, entries in read_training_documents(folder)]
