from dataclasses import dataclass

from privacy_policy_analyzer import Language
from privacy_policy_analyzer.analysis.attributes import (
    AttributePatterns,
    DatePattern,
    DurationPattern,
    EmailPattern,
)
from privacy_policy_analyzer.analysis.classification import ModelConfig, ModelConfigs
from privacy_policy_analyzer.analysis.ner import NERModelConfig, NERModelConfigs
from privacy_policy_analyzer.crawl.splitter import SplitterPattern
from privacy_policy_analyzer.patterns import DEFAULT_EMAIL_PATTERN_CONFIG
from privacy_policy_analyzer.patterns.de import (
    DE_DATE_PATTERN_CONFIG,
    DE_DURATION_PATTERN_CONFIG,
    DE_PATTERN_CONFIG,
    DE_SPLITTER_CONFIG,
)
from privacy_policy_analyzer.patterns.en import (
    EN_DATE_PATTERN_CONFIG,
    EN_DURATION_PATTERN_CONFIG,
    EN_PATTERN_CONFIG,
    EN_SPLITTER_CONFIG,
)


@dataclass
class PipelineConfiguration:
    """Bundles all language-dependent and model configuration needed to run
    the Pipeline for a single language.

    To support another language, add a DEFAULT_<LANG>_CONFIGURATION below
    (with language-specific pattern configs, and model configs once trained)
    and register it in DEFAULT_CONFIGURATIONS.
    """

    language: Language

    model_configs: ModelConfigs
    ner_model_config: NERModelConfigs
    use_ner_for_company: bool

    splitter_configs: SplitterPattern
    pattern_configs: AttributePatterns
    duration_pattern_configs: DurationPattern
    date_pattern_config: DatePattern
    email_pattern_config: EmailPattern


# common domain endings the NER model mistakenly tags as "ORG"
COMMON_DOMAIN_ENDINGS: list[str] = [
    "com",
    "org",
    "net",
    "info",
    "biz",
    "co",
    "io",
    "de",
    "eu",
]

COMMON_ORG_EXCLUDED_TERMS: list[str] = [
    "Inc",
    "Ltd",
    "LLC",
    "GmbH",
    "AG",
    "Company",
    "Corporation",
    "Limited",
    "Incorporated",
    "LLP",
    "PLC",
]


# --------- EN defaults ---------

EN_DEFAULT_MODEL_CONFIGS: ModelConfigs = ModelConfigs(
    context=ModelConfig(
        model_name="Wravn/privacy-policy-context",
        thresholds={},
    ),
    topic=ModelConfig(
        model_name="Wravn/privacy-policy-topic",
        thresholds={
            "Purpose": 0.4,
            "Sharing": 0.6,
            "ThirdParty": 0.6,
            "Selling": 0.65,
            "Audience": 0.7,
        },
    ),
    audience=ModelConfig(
        model_name="Wravn/privacy-policy-content-audience",
        thresholds={"Country": 0.4},
    ),
    contact=ModelConfig(
        model_name="Wravn/privacy-policy-content-contact",
        thresholds={"Website": 0.4},
    ),
    control=ModelConfig(
        model_name="Wravn/privacy-policy-content-control",
        thresholds={},
    ),
    deletion=ModelConfig(
        model_name="Wravn/privacy-policy-content-deletion",
        thresholds={},
    ),
    legal_basis=ModelConfig(
        model_name="Wravn/privacy-policy-content-legalbasis",
        thresholds={},
    ),
    policy=ModelConfig(
        model_name="Wravn/privacy-policy-content-policy",
        thresholds={"Change": 0.4, "External": 0.65},
    ),
    processing=ModelConfig(
        model_name="Wravn/privacy-policy-content-processing",
        thresholds={"Method/Source": 0.4},
    ),
    purpose=ModelConfig(
        model_name="Wravn/privacy-policy-content-purpose",
        thresholds={},
    ),
    retention=ModelConfig(
        model_name="Wravn/privacy-policy-content-retention",
        thresholds={"StorageDuration": 0.4},
    ),
    security_privacy=ModelConfig(
        model_name="Wravn/privacy-policy-content-securityprivacy",
        thresholds={"SecurityHints": 0.4},
    ),
    selling=ModelConfig(
        model_name="Wravn/privacy-policy-content-selling",
        thresholds={"NotSelling": 0.90},
    ),
    sharing=ModelConfig(
        model_name="Wravn/privacy-policy-content-sharing",
        thresholds={},
    ),
    third_party=ModelConfig(
        model_name="Wravn/privacy-policy-content-thirdparty",
        thresholds={"Company": 0.3, "Descriptive": 0.4},
    ),
    user_rights=ModelConfig(
        model_name="Wravn/privacy-policy-content-userrights",
        thresholds={},
    ),
)


EN_DEFAULT_NER_MODEL_CONFIGS: NERModelConfigs = NERModelConfigs(
    company=NERModelConfig(
        model_name="FacebookAI/xlm-roberta-large-finetuned-conll03-english",
        thresholds={"ORG": 0.85},
        excluded_terms=COMMON_DOMAIN_ENDINGS + COMMON_ORG_EXCLUDED_TERMS,
        min_length=2,
    ),
)


EN_DEFAULT_CONFIGURATION: PipelineConfiguration = PipelineConfiguration(
    language=Language.EN,
    model_configs=EN_DEFAULT_MODEL_CONFIGS,
    ner_model_config=EN_DEFAULT_NER_MODEL_CONFIGS,
    use_ner_for_company=True,
    splitter_configs=EN_SPLITTER_CONFIG,
    pattern_configs=EN_PATTERN_CONFIG,
    duration_pattern_configs=EN_DURATION_PATTERN_CONFIG,
    date_pattern_config=EN_DATE_PATTERN_CONFIG,
    email_pattern_config=DEFAULT_EMAIL_PATTERN_CONFIG,
)


# --------- DE defaults ---------

DE_DEFAULT_MODEL_CONFIGS: ModelConfigs = ModelConfigs(
    context=ModelConfig(
        model_name="Immerwinter/gbert-large-privacy-policy-context",
        thresholds={},
    ),
    topic=ModelConfig(
        model_name="Immerwinter/gbert-large-privacy-policy-topic",
        thresholds={
            "Purpose": 0.4,
            "Sharing": 0.6,
            "ThirdParty": 0.6,
            "Selling": 0.65,
            "Audience": 0.7,
        },
    ),
    audience=ModelConfig(
        model_name="Immerwinter/gelectra-large-privacy-policy-content-audience",
        thresholds={"Country": 0.4},
    ),
    contact=ModelConfig(
        model_name="Immerwinter/gbert-large-privacy-policy-content-control",
        thresholds={"Website": 0.4},
    ),
    control=ModelConfig(
        model_name="Immerwinter/google-bert-privacy-policy-content-contact",
        thresholds={},
    ),
    deletion=ModelConfig(
        model_name="Immerwinter/gbert-large-privacy-policy-content-deletion",
        thresholds={},
    ),
    legal_basis=ModelConfig(
        model_name="Immerwinter/gbert-large-privacy-policy-content-legalbasis",
        thresholds={},
    ),
    policy=ModelConfig(
        model_name="Immerwinter/gelectra-large-privacy-policy-content-policy",
        thresholds={"Change": 0.4, "External": 0.65},
    ),
    processing=ModelConfig(
        model_name="Immerwinter/gbert-large-privacy-policy-content-processing",
        thresholds={"Method/Source": 0.4},
    ),
    purpose=ModelConfig(
        model_name="Immerwinter/gelectra-large-privacy-policy-content-purpose",
        thresholds={},
    ),
    retention=ModelConfig(
        model_name="Immerwinter/roberta-wechsel-privacy-policy-content-retention",
        thresholds={"StorageDuration": 0.4},
    ),
    security_privacy=ModelConfig(
        model_name="Immerwinter/gbert-large-privacy-policy-content-securityprivacy",
        thresholds={"SecurityHints": 0.4},
    ),
    selling=ModelConfig(
        model_name="Immerwinter/roberta-wechsel-privacy-policy-content-selling",
        thresholds={"NotSelling": 0.90},
    ),
    sharing=ModelConfig(
        model_name="Immerwinter/gottbert-privacy-policy-content-sharing",
        thresholds={},
    ),
    third_party=ModelConfig(
        model_name="Immerwinter/gbert-large-privacy-policy-content-thirdparty",
        thresholds={"Company": 0.3, "Descriptive": 0.4},
    ),
    user_rights=ModelConfig(
        model_name="Immerwinter/gbert-large-privacy-policy-content-userrights",
        thresholds={},
    ),
)


DE_DEFAULT_NER_MODEL_CONFIGS: NERModelConfigs = NERModelConfigs(
    company=NERModelConfig(
        model_name="FacebookAI/xlm-roberta-large-finetuned-conll03-german",
        thresholds={"ORG": 0.85},
        excluded_terms=COMMON_DOMAIN_ENDINGS + COMMON_ORG_EXCLUDED_TERMS,
        min_length=2,
    ),
)


DE_DEFAULT_CONFIGURATION: PipelineConfiguration = PipelineConfiguration(
    language=Language.DE,
    model_configs=DE_DEFAULT_MODEL_CONFIGS,
    ner_model_config=DE_DEFAULT_NER_MODEL_CONFIGS,
    use_ner_for_company=True,
    splitter_configs=DE_SPLITTER_CONFIG,
    pattern_configs=DE_PATTERN_CONFIG,
    duration_pattern_configs=DE_DURATION_PATTERN_CONFIG,
    date_pattern_config=DE_DATE_PATTERN_CONFIG,
    email_pattern_config=DEFAULT_EMAIL_PATTERN_CONFIG,
)


# --------- Default configurations ---------

DEFAULT_CONFIGURATIONS: dict[Language, PipelineConfiguration] = {
    Language.EN: EN_DEFAULT_CONFIGURATION,
    Language.DE: DE_DEFAULT_CONFIGURATION,
}
