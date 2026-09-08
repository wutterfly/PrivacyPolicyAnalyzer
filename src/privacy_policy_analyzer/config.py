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
        thresholds={
            "Other": 0.6,
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
            "Method/Source": 0.1,
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
)


# --------- Default configurations ---------

DEFAULT_CONFIGURATIONS: dict[Language, PipelineConfiguration] = {
    Language.EN: EN_DEFAULT_CONFIGURATION,
    Language.DE: DE_DEFAULT_CONFIGURATION,
}
