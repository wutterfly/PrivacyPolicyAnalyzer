from dataclasses import dataclass

from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    TokenClassificationPipeline,
    pipeline,
)
from transformers import (
    logging as hf_logging,
)

from privacy_policy_analyzer.analysis.err import ModelLoadError
from privacy_policy_analyzer.shared.annotation import RawEntry
from privacy_policy_analyzer.shared.logging import get_logger
from privacy_policy_analyzer.shared.util import cleanup_memory, get_device

logger = get_logger(__name__)
hf_logging.set_verbosity_error()
hf_logging.disable_progress_bar()

try:
    from optimum.onnxruntime import ORTModelForTokenClassification

    ONNX_AVAILABLE = True
    ONNX_IMPORT_ERROR = None
except ImportError as e:
    # commonly caused by an installed `optimum` that doesn't support the
    # currently installed `transformers` version, not by a missing package
    ONNX_AVAILABLE = False
    ONNX_IMPORT_ERROR = str(e)


@dataclass
class LoadedNERModel:
    ner: TokenClassificationPipeline

    def __del__(self):
        del self.ner
        cleanup_memory()


@dataclass
class NERModelConfig:
    model_name: str

    # score threshold per entity group (e.g. "ORG", "PER", "LOC", "MISC").
    # an entity group missing from this dict is not extracted at all, unlike
    # ModelConfig.thresholds in classification.py, since not every entity
    # group found by the model is necessarily wanted.
    thresholds: dict[str, float]

    # matched words to drop regardless of score (case-insensitive, exact
    # match), for post-processing model quirks - e.g. this NER model tags
    # bare domain endings like "com"/"info" as "ORG".
    excluded_terms: list[str]

    # matched words shorter than this (in characters) are dropped.
    min_length: int


@dataclass
class NERModelConfigs:
    """Configuration for all NER models used in the pipeline, one per
    extraction target. Add a new field here (and a matching extract_entities
    call in analysis/__init__.py) to plug in another NER model."""

    company: NERModelConfig

    def _get_model_configs(self) -> list[tuple[str, NERModelConfig]]:
        """Return all model configs with their display names."""
        return [
            ("Company", self.company),
        ]

    def test_load_models(self, prefer_onnx: bool):
        for name, config in self._get_model_configs():
            loaded = _load_pipeline(config.model_name, prefer_onnx, cached=False)
            if isinstance(loaded, ModelLoadError):
                raise loaded
            del loaded
            logger.debug(
                "NER model loaded successfully: name=%s model=%s",
                name,
                config.model_name,
            )


def _load_pipeline(
    model_name: str, prefer_onnx: bool, cached: bool, logging: bool = True
) -> LoadedNERModel | ModelLoadError:
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
            model = ORTModelForTokenClassification.from_pretrained(
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
            model = AutoModelForTokenClassification.from_pretrained(
                model_name, local_files_only=cached
            )
        # ONNX Runtime models always run on CPU here - GPU execution providers
        # aren't wired up, so device selection would silently be wrong.
        device = "cpu" if loaded_onnx else get_device()

        return LoadedNERModel(
            pipeline(
                "ner",
                model=model,
                tokenizer=tokenizer,
                aggregation_strategy="simple",
                device=device,
                batch_size=16,
            )
        )
    except Exception as e:
        logger.error("Failed to load model=%s: %s", model_name, e)
        return ModelLoadError(model_name, str(e))


def extract_entities(
    entries: list[RawEntry],
    topic: list[str],
    content: str,
    config: NERModelConfig,
    prefer_onnx: bool,
    cached: bool,
):
    """Run named entity recognition and merge matches into each entry's
    `topic` -> `content` content attributes.

    Only entries that already have one of the given topics with a matching
    `content` block are processed (mirroring classify_content's and
    extract_attributes' filtering) - this augments existing attributes, it
    does not create new topic/content annotations. Mutates `entries` in
    place, matching extract_attributes' contract in attributes.py.
    """
    filtered_indices = []
    texts = []
    for i, entry in enumerate(entries):
        has_matching_content = any(
            tpc.topic in topic and any(cnt.content == content for cnt in tpc.contents)
            for tpc in entry.topics
        )
        if has_matching_content:
            filtered_indices.append(i)
            texts.append(entry.text)

    if len(texts) == 0:
        return

    model = _load_pipeline(
        model_name=config.model_name,
        prefer_onnx=prefer_onnx,
        cached=cached,
        logging=not cached,
    )
    if isinstance(model, ModelLoadError):
        raise model
    logger.debug(
        "Extracting entities with model=%s entries=%d", config.model_name, len(texts)
    )

    predictions = model.ner(texts, batch_size=16)

    excluded_terms = {term.lower() for term in config.excluded_terms}

    for idx, prediction in zip(filtered_indices, predictions):
        assert isinstance(prediction, list)

        matched_words = []
        for pred in prediction:
            pred: dict = pred

            entity_group: str = pred["entity_group"]
            score: float = pred["score"]
            word: str = pred["word"].strip()

            threshold = config.thresholds.get(entity_group)
            if threshold is None or score < threshold:
                continue

            if len(word) < config.min_length:
                continue

            if word.lower() in excluded_terms:
                continue

            matched_words.append(word)

        if not matched_words:
            continue

        for tpc in entries[idx].topics:
            if tpc.topic not in topic:
                continue
            for cnt in tpc.contents:
                if cnt.content == content:
                    cnt.attributes.extend(matched_words)

    del model
