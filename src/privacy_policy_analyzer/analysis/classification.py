from dataclasses import dataclass
from logging import debug

# from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TextClassificationPipeline,
    logging,
    pipeline,
)

from privacy_policy_analyzer.shared.annotation import (
    ContentAnnotation,
    RawEntry,
    TopicAnnotation,
)
from privacy_policy_analyzer.shared.util import cleanup_memory, get_device

DEFAULT_THRESHOLD = 0.5
logging.set_verbosity_error()


@dataclass
class LoadedClassifier:
    classifier: TextClassificationPipeline

    def __del__(self):
        del self.classifier
        cleanup_memory()


@dataclass
class ModelConfig:
    model_name: str
    thresholds: dict[str, float]


@dataclass
class ModelConfigs:
    context: ModelConfig
    topic: ModelConfig
    audience: ModelConfig
    contact: ModelConfig
    control: ModelConfig
    deletion: ModelConfig
    legal_basis: ModelConfig
    policy: ModelConfig
    processing: ModelConfig
    purpose: ModelConfig
    retention: ModelConfig
    security_privacy: ModelConfig
    selling: ModelConfig
    sharing: ModelConfig
    third_party: ModelConfig
    user_rights: ModelConfig


def load_pipeline(model_name: str, use_onnx: bool) -> TextClassificationPipeline:
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    model = None
    device = None

    if use_onnx:
        # model = ORTModelForSequenceClassification.from_pretrained(model_name)
        device = "cpu"

    else:
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        device = get_device()

    return pipeline(
        "text-classification",
        model=model,
        tokenizer=tokenizer,
        device=device,
        top_k=None,
        batch_size=16,
        truncation=True,
    )


def classify_context(
    entries: list[RawEntry],
    config: ModelConfig,
    use_onnx: bool,
):
    model = LoadedClassifier(
        classifier=load_pipeline(model_name=config.model_name, use_onnx=use_onnx)
    )
    debug(f"Classifying context with model {config.model_name}")

    texts = [entry.text for entry in entries]
    predictions = model.classifier(texts, batch_size=16)

    for entry, prediction in zip(entries, predictions):
        assert isinstance(prediction, list)

        for pred in prediction:
            pred: dict = pred

            label: str = pred["label"]
            score: float = pred["score"]
            threshold = config.thresholds.get(label, DEFAULT_THRESHOLD)
            if score >= threshold:
                entry.contexts.append(label)

        if entry.contexts == []:
            entry.contexts.append("Other")

    del model


def classify_topics(entries: list[RawEntry], config: ModelConfig, use_onnx: bool):
    model = LoadedClassifier(
        classifier=load_pipeline(model_name=config.model_name, use_onnx=use_onnx)
    )
    debug(f"Classifying topics with model {config.model_name}")

    texts = [entry.text for entry in entries]
    predictions = model.classifier(texts, batch_size=16)

    for entry, prediction in zip(entries, predictions):
        assert isinstance(prediction, list)

        for pred in prediction:
            pred: dict = pred

            label: str = pred["label"]
            score: float = pred["score"]
            threshold = config.thresholds.get(label, DEFAULT_THRESHOLD)
            if score >= threshold:
                entry.topics.append(TopicAnnotation(topic=label, contents=[]))

        if entry.topics == []:
            entry.topics.append(TopicAnnotation(topic="Other", contents=[]))

    del model


def classify_content(
    entries: list[RawEntry], topic: str, config: ModelConfig, use_onnx: bool
):
    model = LoadedClassifier(
        classifier=load_pipeline(model_name=config.model_name, use_onnx=use_onnx)
    )
    debug(f"Classifying content for topic {topic} with model {config.model_name}")

    # filter entries by topic
    filtered_indices = []
    texts = []
    for i, entry in enumerate(entries):
        has_topic = any(annotation.topic == topic for annotation in entry.topics)
        if has_topic:
            filtered_indices.append(i)
            texts.append(entry.text)

    # classify only the filtered entries
    predictions = model.classifier(texts)
    for idx, prediction in zip(filtered_indices, predictions):
        assert isinstance(prediction, list)

        # find topic index
        # there should be only one topic annotation for the given topic
        tpc_idx: int | None = next(
            (i for i, ann in enumerate(entries[idx].topics) if ann.topic == topic)
        )
        assert tpc_idx is not None

        for pred in prediction:
            pred: dict = pred

            label: str = pred["label"]
            score: float = pred["score"]
            threshold = config.thresholds.get(label, DEFAULT_THRESHOLD)
            if score >= threshold:
                entries[idx].topics[tpc_idx].contents.append(
                    ContentAnnotation(content=label, attributes=[])
                )

    del model
