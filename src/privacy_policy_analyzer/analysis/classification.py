from dataclasses import dataclass

from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TextClassificationPipeline,
    pipeline,
)
from transformers import (
    logging as hf_logging,
)

from privacy_policy_analyzer.analysis.err import ModelLoadError
from privacy_policy_analyzer.shared.annotation import (
    ContentAnnotation,
    RawEntry,
    TopicAnnotation,
)
from privacy_policy_analyzer.shared.logging import get_logger
from privacy_policy_analyzer.shared.util import cleanup_memory, get_device

logger = get_logger(__name__)
hf_logging.set_verbosity_error()
hf_logging.disable_progress_bar()

try:
    from optimum.onnxruntime import ORTModelForSequenceClassification

    ONNX_AVAILABLE = True
    ONNX_IMPORT_ERROR = None
except ImportError as e:
    # commonly caused by an installed `optimum` that doesn't support the
    # currently installed `transformers` version, not by a missing package
    ONNX_AVAILABLE = False
    ONNX_IMPORT_ERROR = str(e)
    print(e)

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

    def test_load_models(self, prefer_onnx: bool):
        for name, config in self._get_model_configs():
            loaded = _load_pipeline(config.model_name, prefer_onnx, cached=False)
            if isinstance(loaded, ModelLoadError):
                raise loaded
            del loaded
            logger.debug(
                "Model loaded successfully: name=%s model=%s", name, config.model_name
            )


def _load_pipeline(
    model_name: str, prefer_onnx: bool, cached: bool, logging: bool = True
) -> LoadedClassifier | ModelLoadError:
    if logging:
        logger.info("Loading model=%s", model_name)

    model = None
    tokenizer = None
    loaded_onnx = False

    if prefer_onnx and not ONNX_AVAILABLE:
        logger.warning(
            "prefer_onnx=True but optimum.onnxruntime could not be imported "
            "(%s), falling back to PyTorch model=%s",
            ONNX_IMPORT_ERROR,
            model_name,
        )

    if prefer_onnx and ONNX_AVAILABLE:
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                model_name, local_files_only=cached
            )
            model = ORTModelForSequenceClassification.from_pretrained(
                model_name, local_files_only=cached
            )
            loaded_onnx = True
            if logging:
                logger.debug("Loaded ONNX model=%s", model_name)
        except Exception as e:
            if logging:
                logger.warning(
                    "No ONNX model available for model=%s, falling back to "
                    "PyTorch: %s",
                    model_name,
                    e,
                )
            model = None
            tokenizer = None

    try:
        if model is None:
            tokenizer = AutoTokenizer.from_pretrained(
                model_name, local_files_only=cached
            )
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name, local_files_only=cached
            )
        # ONNX Runtime models always run on CPU here - GPU execution providers
        # aren't wired up, so device selection would silently be wrong.
        device = "cpu" if loaded_onnx else get_device()

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
    except Exception as e:
        logger.error("Failed to load model=%s: %s", model_name, e)
        return ModelLoadError(model_name, str(e))


def classify_context(
    entries: list[RawEntry], config: ModelConfig, prefer_onnx: bool, cached: bool
):
    model = _load_pipeline(
        model_name=config.model_name,
        prefer_onnx=prefer_onnx,
        cached=cached,
        logging=not cached,
    )
    if isinstance(model, ModelLoadError):
        raise model
    logger.debug("Classifying context ....")

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
    entries: list[RawEntry], config: ModelConfig, prefer_onnx: bool, cached: bool
):
    model = _load_pipeline(
        model_name=config.model_name,
        prefer_onnx=prefer_onnx,
        cached=cached,
        logging=not cached,
    )
    if isinstance(model, ModelLoadError):
        raise model
    logger.debug("Classifying topics ....")

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
    prefer_onnx: bool,
    cached: bool,
):
    model = _load_pipeline(
        model_name=config.model_name,
        prefer_onnx=prefer_onnx,
        cached=cached,
        logging=not cached,
    )
    if isinstance(model, ModelLoadError):
        raise model

    logger.debug("Classifying content for topic=%s", topic)

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
