from dataclasses import dataclass

# from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TextClassificationPipeline,
    pipeline,
)
from transformers import (
    logging as hf_logging,
)

from privacy_policy_analyzer.shared.annotation import (
    ContentAnnotation,
    RawEntry,
    TopicAnnotation,
)
from privacy_policy_analyzer.shared.logging import get_logger
from privacy_policy_analyzer.shared.util import cleanup_memory, get_device

logger = get_logger(__name__)
hf_logging.set_verbosity_error()

DEFAULT_THRESHOLD = 0.5


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
    """Configuration for all models used in the pipeline."""

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

    def _get_model_configs(self) -> list[tuple[str, ModelConfig]]:
        """Return all model configs with their display names."""
        return [
            ("Context", self.context),
            ("Topic", self.topic),
            ("Audience", self.audience),
            ("Contact", self.contact),
            ("Control", self.control),
            ("Deletion", self.deletion),
            ("Legal Basis", self.legal_basis),
            ("Policy", self.policy),
            ("Processing", self.processing),
            ("Purpose", self.purpose),
            ("Retention", self.retention),
            ("Security/Privacy", self.security_privacy),
            ("Selling", self.selling),
            ("Sharing", self.sharing),
            ("Third Party", self.third_party),
            ("User Rights", self.user_rights),
        ]

    def test_load_models(self, onnx: bool):
        for name, config in self._get_model_configs():
            loaded = _load_pipeline(config.model_name, onnx, cached=False)
            del loaded
            logger.debug(
                "Model loaded successfully: name=%s model=%s", name, config.model_name
            )


def _load_pipeline(model_name: str, use_onnx: bool, cached: bool) -> LoadedClassifier:
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=cached)

    model = None
    device = None

    if use_onnx:
        # model = ORTModelForSequenceClassification.from_pretrained(model_name)
        device = "cpu"
        assert False, "ONNX models are currently not supported yet"

    else:
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name, local_files_only=cached
        )
        device = get_device()

    return LoadedClassifier(
        pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer,
            device=device,
            top_k=None,
            batch_size=16,
            truncation=True,
        )
    )


def classify_context(
    entries: list[RawEntry], config: ModelConfig, use_onnx: bool, cached: bool
):
    model = _load_pipeline(
        model_name=config.model_name, use_onnx=use_onnx, cached=cached
    )
    logger.debug(
        "Classifying context with model=%s entries=%d", config.model_name, len(entries)
    )

    texts = [entry.text for entry in entries]

    if len(texts) == 0:
        del model
        return

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


def classify_topics(
    entries: list[RawEntry], config: ModelConfig, use_onnx: bool, cached: bool
):
    model = _load_pipeline(
        model_name=config.model_name, use_onnx=use_onnx, cached=cached
    )
    logger.debug(
        "Classifying topics with model=%s entries=%d", config.model_name, len(entries)
    )

    texts = [entry.text for entry in entries]

    if len(texts) == 0:
        del model
        return

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
    entries: list[RawEntry],
    topic: str,
    config: ModelConfig,
    use_onnx: bool,
    cached: bool,
):
    model = _load_pipeline(
        model_name=config.model_name, use_onnx=use_onnx, cached=cached
    )

    logger.debug("Classifying content for topic=%s model=%s", topic, config.model_name)

    # filter entries by topic
    filtered_indices = []
    texts = []
    for i, entry in enumerate(entries):
        has_topic = any(annotation.topic == topic for annotation in entry.topics)
        if has_topic:
            filtered_indices.append(i)
            texts.append(entry.text)

    if len(texts) == 0:
        del model
        return

    # classify only the filtered entries
    predictions = model.classifier(texts)
    for idx, prediction in zip(filtered_indices, predictions):
        assert isinstance(prediction, list)

        # find topic index
        # there should be only one topic annotation for the given topic
        tpc_idx: int | None = next(
            (i for i, ann in enumerate(entries[idx].topics) if ann.topic == topic),
            None,
        )
        if tpc_idx is None:
            continue

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
