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

from privacy_policy_analyzer.shared.annotation import RawEntry
from privacy_policy_analyzer.shared.logging import get_logger
from privacy_policy_analyzer.shared.util import cleanup_memory, get_device

logger = get_logger(__name__)
hf_logging.set_verbosity_error()
hf_logging.disable_progress_bar()


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

    def test_load_models(self, onnx: bool):
        for name, config in self._get_model_configs():
            loaded = _load_pipeline(config.model_name, onnx, cached=False)
            del loaded
            logger.debug(
                "NER model loaded successfully: name=%s model=%s",
                name,
                config.model_name,
            )


def _load_pipeline(model_name: str, use_onnx: bool, cached: bool) -> LoadedNERModel:
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=cached)

    model = None
    device = None

    if use_onnx:
        device = "cpu"
        assert False, "ONNX models are currently not supported yet"

    else:
        model = AutoModelForTokenClassification.from_pretrained(
            model_name, local_files_only=cached
        )
        device = get_device()

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


def extract_entities(
    entries: list[RawEntry], config: NERModelConfig, use_onnx: bool, cached: bool
):
    """Run named entity recognition and merge matches into each entry's
    ThirdParty -> Company content attributes.

    Only entries that already have a "ThirdParty" topic with a "Company"
    content block are processed (mirroring classify_content's filtering) -
    this augments existing Company attributes, it does not create new
    ThirdParty/Company annotations. Mutates `entries` in place, matching
    extract_attributes' contract in attributes.py.
    """
    filtered_indices = []
    texts = []
    for i, entry in enumerate(entries):
        has_company_content = any(
            tpc.topic == "ThirdParty"
            and any(cnt.content == "Company" for cnt in tpc.contents)
            for tpc in entry.topics
        )
        if has_company_content:
            filtered_indices.append(i)
            texts.append(entry.text)

    if len(texts) == 0:
        return

    model = _load_pipeline(
        model_name=config.model_name, use_onnx=use_onnx, cached=cached
    )
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
            if tpc.topic != "ThirdParty":
                continue
            for cnt in tpc.contents:
                if cnt.content == "Company":
                    cnt.attributes.extend(matched_words)

    del model
