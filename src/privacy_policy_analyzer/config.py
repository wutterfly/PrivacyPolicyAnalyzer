from dataclasses import dataclass, field

from privacy_policy_analyzer import Language
from privacy_policy_analyzer.analysis.attributes import (
    AttributePatterns,
    DatePattern,
    DurationPattern,
    EmailPattern,
    PhonePattern,
    UrlPattern,
)
from privacy_policy_analyzer.analysis.classification import (
    DEFAULT_THRESHOLD,
    ModelConfig,
    ModelConfigs,
)
from privacy_policy_analyzer.analysis.ner import NERModelConfig, NERModelConfigs
from privacy_policy_analyzer.analysis.post_processing import (
    LabelFloors,
    PropagationGate,
)
from privacy_policy_analyzer.crawl.splitter import SplitterPattern
from privacy_policy_analyzer.patterns import (
    DEFAULT_EMAIL_PATTERN_CONFIG,
    DEFAULT_PHONE_PATTERN_CONFIG,
    DEFAULT_URL_PATTERN_CONFIG,
)
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


@dataclass(frozen=True)
class PropagationConfig:
    """How strictly header propagation is gated.

    With `enabled=False`, headers do not propagate anything.

    Otherwise a label that a heading carries is only propagated to a sentence
    if the sentence's own model score for that label is at least

        max(min_score, floor_ratio * threshold of that label)

    where `floor_ratio` is the one of the label's kind (scope, topic or
    content) and the threshold is the one used for classification. A ratio of
    0.5 lets a sentence inherit a label it nearly reached on its own, and
    keeps clearly unrelated sentences from picking it up. Sentences that
    already have a label are not affected.

    All ratios at 0 mean there is no gate: every label a heading carries is
    propagated to all sentences below it (within the limits below).

    `scopes_only_into_unspecified` lets only sentences whose own Scope is
    `Unspecified` inherit Scopes, and `nearest_scope` takes them only from the
    nearest heading above the sentence that has a Scope (a subsection
    narrows the Scope of its section). `topics=False` stops headings from passing
    on topics, and `contents=False` lets them pass on topics but not their
    contents, which the content models then decide. The defaults follow the
    in-context evaluation of the added labels (Section 6.4 of the paper):
    Scopes inherited by Unspecified sentences were mostly correct, while
    Scopes added to sentences with a Scope of their own, inherited topics
    (also under a strict gate), and inherited contents were mostly wrong.
    """

    enabled: bool = True
    scopes_only_into_unspecified: bool = True
    nearest_scope: bool = True
    topics: bool = False
    contents: bool = False
    scope_floor_ratio: float = 0.0
    topic_floor_ratio: float = 0.0
    content_floor_ratio: float = 0.0
    min_score: float = 0.0

    def __post_init__(self):
        for name in (
            "scope_floor_ratio",
            "topic_floor_ratio",
            "content_floor_ratio",
            "min_score",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1, got {value}")

    @property
    def gated(self) -> bool:
        """Whether propagation is conditional on the scores of the sentences."""
        return self.enabled and any(
            value > 0.0
            for value in (
                self.scope_floor_ratio,
                self.topic_floor_ratio,
                self.content_floor_ratio,
                self.min_score,
            )
        )

    def build_gate(self, model_configs: ModelConfigs) -> PropagationGate | None:
        """The gate for the thresholds of `model_configs`; None if there is no gate."""
        if not self.gated:
            return None

        def floors(config: ModelConfig | None, ratio: float) -> LabelFloors:
            return LabelFloors(
                default=max(self.min_score, ratio * DEFAULT_THRESHOLD),
                by_label={
                    label: max(self.min_score, ratio * threshold)
                    for label, threshold in (
                        config.thresholds.items() if config is not None else ()
                    )
                },
            )

        return PropagationGate(
            scopes=floors(model_configs.scope, self.scope_floor_ratio),
            topics=floors(model_configs.topic, self.topic_floor_ratio),
            contents={
                topic: floors(content_config, self.content_floor_ratio)
                for topic, content_config in model_configs.content_models().items()
            },
            default_contents=floors(None, self.content_floor_ratio),
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
    phone_pattern_config: PhonePattern
    url_pattern_config: UrlPattern

    propagation: PropagationConfig = field(default_factory=PropagationConfig)


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

# Best model per task of the by-policy training run of 2026-11-23 (selected by test
# macro-F1, see privpolicydata/scripts/upload.py). No label overrides the default
# threshold of 0.5, the threshold the models were evaluated at.
EN_DEFAULT_MODEL_CONFIGS: ModelConfigs = ModelConfigs(
    scope=ModelConfig(
        model_name="Wravn/PrivaScope-scope",
        thresholds={},
    ),
    topic=ModelConfig(
        model_name="Wravn/PrivaScope-topic",
        thresholds={},
    ),
    audience=ModelConfig(
        model_name="Wravn/PrivaScope-content-audience",
        thresholds={},
    ),
    contact=ModelConfig(
        model_name="Wravn/PrivaScope-content-contact",
        thresholds={},
    ),
    control=ModelConfig(
        model_name="Wravn/PrivaScope-content-control",
        thresholds={},
    ),
    deletion=ModelConfig(
        model_name="Wravn/PrivaScope-content-deletion",
        thresholds={},
    ),
    legal_basis=ModelConfig(
        model_name="Wravn/PrivaScope-content-legalbasis",
        thresholds={},
    ),
    policy=ModelConfig(
        model_name="Wravn/PrivaScope-content-policy",
        thresholds={},
    ),
    processing=ModelConfig(
        model_name="Wravn/PrivaScope-content-processing",
        thresholds={},
    ),
    purpose=ModelConfig(
        model_name="Wravn/PrivaScope-content-purpose",
        thresholds={},
    ),
    retention=ModelConfig(
        model_name="Wravn/PrivaScope-content-retention",
        thresholds={},
    ),
    security_privacy=ModelConfig(
        model_name="Wravn/PrivaScope-content-securityprivacy",
        thresholds={},
    ),
    selling=ModelConfig(
        model_name="Wravn/PrivaScope-content-selling",
        thresholds={},
    ),
    sharing=ModelConfig(
        model_name="Wravn/PrivaScope-content-sharing",
        thresholds={},
    ),
    third_party=ModelConfig(
        model_name="Wravn/PrivaScope-content-thirdparty",
        thresholds={},
    ),
    user_rights=ModelConfig(
        model_name="Wravn/PrivaScope-content-userrights",
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
    phone_pattern_config=DEFAULT_PHONE_PATTERN_CONFIG,
    url_pattern_config=DEFAULT_URL_PATTERN_CONFIG,
)


# --------- DE defaults ---------

DE_DEFAULT_MODEL_CONFIGS: ModelConfigs = ModelConfigs(
    scope=ModelConfig(
        model_name="Immerwinter/gbert-large-privacy-policy-context",
        thresholds={
            "Unspecified": 0.6,
            "Website": 0.6,
            "App": 0.1,
            "Device": 0.85,
            "Store": 0.1,
            "BackendService": 0.75,
            "Recruitment": 0.15,
            "Communication": 0.2,
            "Account": 0.6,
            "Services": 0.25,
            "Event/Program": 0.55,
        },
    ),
    topic=ModelConfig(
        model_name="Immerwinter/gbert-large-privacy-policy-topic",
        thresholds={
            "Other": 0.55,
            "UserRights": 0.1,
            "Processing": 0.55,
            "Retention": 0.45,
            "Deletion": 0.1,
            "Purpose": 0.1,
            "Sharing": 0.2,
            "LegalBasis": 0.85,
            "Security/Privacy": 0.9,
            "ThirdParty": 0.5,
            "Contact": 0.1,
            "Policy": 0.2,
            "Audience": 0.35,
            "Control": 0.65,
            "Selling": 0.1,
        },
    ),
    audience=ModelConfig(
        model_name="Immerwinter/gelectra-large-privacy-policy-content-audience",
        thresholds={
            "Other": 0.5,
            "Children": 0.2,
            "BetaTester": 0.1,
            "BusinessCustomer": 0.1,
            "Country": 0.2,
            "Bystanders": 0.15,
        },
    ),
    contact=ModelConfig(
        model_name="Immerwinter/google-bert-privacy-policy-content-contact",
        thresholds={
            "Other": 0.15,
            "Address": 0.1,
            "Email": 0.4,
            "Phone": 0.2,
            "Website": 0.6,
            "Country": 0.4,
            "Appeal": 0.2,
        },
    ),
    control=ModelConfig(
        model_name="Immerwinter/gbert-large-privacy-policy-content-control",
        thresholds={
            "Other": 0.75,
            "OptIn": 0.55,
            "OptOut": 0.4,
            "Preferences/Settings": 0.3,
            "Unsubscribe": 0.3,
            "NoControl": 0.25,
            "GPCSignal": 0.55,
            "CancelService": 0.5,
        },
    ),
    deletion=ModelConfig(
        model_name="Immerwinter/gbert-large-privacy-policy-content-deletion",
        thresholds={
            "Other": 0.1,
            "NotDeletion": 0.2,
            "DataType": 0.45,
            "WeakDeletion": 0.25,
            "Inactivity": 0.1,
            "Automatically": 0.45,
            "WithinTimePeriod": 0.75,
        },
    ),
    legal_basis=ModelConfig(
        model_name="Immerwinter/gbert-large-privacy-policy-content-legalbasis",
        thresholds={
            "Other": 0.1,
            "Consent": 0.3,
            "Contract": 0.1,
            "LegalObligation": 0.25,
            "PublicInterests": 0.1,
            "VitalInterests": 0.1,
            "LegitimateInterests": 0.1,
            "EmploymentProcedure": 0.1,
        },
    ),
    policy=ModelConfig(
        model_name="Immerwinter/gelectra-large-privacy-policy-content-policy",
        thresholds={
            "Other": 0.5,
            "Change": 0.25,
            "Definition": 0.35,
            "ResponsiblePerson": 0.4,
            "DataProtectionOfficer": 0.15,
            "External": 0.65,
        },
    ),
    processing=ModelConfig(
        model_name="Immerwinter/gbert-large-privacy-policy-content-processing",
        thresholds={
            "Other": 0.2,
            "NotProcessing": 0.6,
            "ByThirdParty": 0.1,
            "DataType": 0.5,
            "Tracking/Conversion": 0.1,
            "Profiling": 0.15,
            "AutomatedDecisionMaking": 0.1,
            "Source": 0.1,
        },
    ),
    purpose=ModelConfig(
        model_name="Immerwinter/gelectra-large-privacy-policy-content-purpose",
        thresholds={
            "Other": 0.1,
            "ImproveService": 0.1,
            "ProvideService": 0.3,
            "Security": 0.2,
            "Compliance": 0.35,
            "CustomerAcquisition": 0.6,
            "Communication": 0.3,
            "Operational": 0.1,
            "Unspecified": 0.1,
            "SignificantEffects": 0.1,
            "Analytics": 0.1,
        },
    ),
    retention=ModelConfig(
        model_name="Immerwinter/roberta-wechsel-privacy-policy-content-retention",
        thresholds={
            "Other": 0.1,
            "NotRetention": 0.15,
            "ByThirdParty": 0.2,
            "DataType": 0.65,
            "StorageDuration": 0.1,
            "StatutoryRetention": 0.35,
            "LegalBasisDuration": 0.25,
            "Necessity": 0.65,
            "Country": 0.15,
            "LocalStorage": 0.1,
            "CloudStorage": 0.35,
        },
    ),
    security_privacy=ModelConfig(
        model_name="Immerwinter/gbert-large-privacy-policy-content-securityprivacy",
        thresholds={
            "Other": 0.15,
            "TransmissionSecurity": 0.5,
            "ContractualSecurityMeasures": 0.35,
            "TechnicalSecurityMeasures": 0.45,
            "TechnicalPrivacyMeasures": 0.2,
            "PhysicalSecurityMeasures": 0.2,
            "OrganisationalSecurityMeasures": 0.7,
            "SecurityHints": 0.75,
            "Certifications": 0.1,
        },
    ),
    selling=ModelConfig(
        model_name="Immerwinter/roberta-wechsel-privacy-policy-content-selling",
        thresholds={
            "Other": 0.4,
            "NotSelling": 0.45,
            "DataType": 0.25,
            "Merger/Acquisition": 0.2,
            "Insolvency": 0.2,
        },
    ),
    sharing=ModelConfig(
        model_name="Immerwinter/gottbert-privacy-policy-content-sharing",
        thresholds={
            "Other": 0.4,
            "NotSharing": 0.15,
            "ByThirdParty": 0.45,
            "DataType": 0.65,
            "Country": 0.8,
        },
    ),
    third_party=ModelConfig(
        model_name="Immerwinter/gbert-large-privacy-policy-content-thirdparty",
        thresholds={
            "Other": 0.1,
            "Company": 0.35,
            "Official": 0.1,
            "SameCompany": 0.1,
            "Descriptive": 0.15,
            "ChosenIndividual": 0.1,
            "Public": 0.15,
            "OtherUser": 0.1,
        },
    ),
    user_rights=ModelConfig(
        model_name="Immerwinter/gbert-large-privacy-policy-content-userrights",
        thresholds={
            "Other": 0.1,
            "RevokeConsent": 0.2,
            "DataAccess": 0.1,
            "DataPortability": 0.1,
            "DataErasure": 0.15,
            "DataRectification": 0.15,
            "BeInformed": 0.4,
            "RestrictProcessing": 0.25,
            "Object": 0.9,
            "Complain": 0.1,
            "NotBeDiscriminated": 0.15,
        },
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
    phone_pattern_config=DEFAULT_PHONE_PATTERN_CONFIG,
    url_pattern_config=DEFAULT_URL_PATTERN_CONFIG,
)


# --------- Default configurations ---------

DEFAULT_CONFIGURATIONS: dict[Language, PipelineConfiguration] = {
    Language.EN: EN_DEFAULT_CONFIGURATION,
    Language.DE: DE_DEFAULT_CONFIGURATION,
}
