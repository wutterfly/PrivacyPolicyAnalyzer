import json
from dataclasses import dataclass
from pathlib import Path

from privacy_policy_analyzer.shared.logging import get_logger

logger = get_logger(__name__)


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
class RawEntry:
    """A single annotated entry in the training data."""

    line_number: int
    text: str
    contexts: list[str]
    topics: list[TopicAnnotation]


def read_raw_entry(data: dict) -> RawEntry:
    """Reads a single raw entry from a dictionary."""

    line_number = data["line_number"]
    text = data["text"]
    contexts = data.get("annotations", data)["contexts"]
    assert all(isinstance(context, str) for context in contexts), (
        "All contexts must be strings"
    )
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
        contexts=contexts,
        topics=topics,
    )


def read_training_data(folder: Path) -> list[list[RawEntry]]:
    """Reads all training data from the specified folder."""

    training_files: list[list[RawEntry]] = []
    for filename in folder.glob("*.json"):
        try:
            x = filename.open("r", encoding="utf-8")
            content: dict = json.load(x)
            contents = []
            for entry in content:
                contents.append(read_raw_entry(entry))
            training_files.append(contents)
        except Exception as e:
            logger.error("Error reading file=%s: %s", filename, e)

    logger.info("Loaded %d training files from folder=%s", len(training_files), folder)
    return training_files
