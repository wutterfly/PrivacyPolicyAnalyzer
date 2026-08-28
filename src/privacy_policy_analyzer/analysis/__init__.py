from privacy_policy_analyzer.analysis.attributes import (
    AttributePatterns,
    DatePattern,
    DurationPattern,
    EmailPattern,
    extract_attributes,
    extract_date,
    extract_duration,
    extract_email,
)
from privacy_policy_analyzer.analysis.classification import (
    ModelConfig,
    ModelConfigs,
    classify_content,
    classify_context,
    classify_topics,
)
from privacy_policy_analyzer.shared.annotation import RawEntry
from privacy_policy_analyzer.shared.logging import get_logger

logger = get_logger(__name__)


def collect_information(
    entries: list[RawEntry],
    model_config: ModelConfigs,
    pattern_config: AttributePatterns,
    duration_pattern_config: DurationPattern,
    date_pattern_config: DatePattern,
    email_pattern_config: EmailPattern,
    onnx: bool,
    cached: bool,
):
    # classify contexts, topics, and contents
    logger.debug(
        "Classifying contexts, topics, and contents for entries=%d", len(entries)
    )
    classify_context(entries, model_config.context, onnx, cached)
    classify_topics(entries, model_config.topic, onnx, cached)
    classify_content(entries, "Audience", model_config.audience, onnx, cached)
    classify_content(entries, "Contact", model_config.contact, onnx, cached)
    classify_content(entries, "Control", model_config.control, onnx, cached)
    classify_content(entries, "Deletion", model_config.deletion, onnx, cached)
    classify_content(entries, "LegalBasis", model_config.legal_basis, onnx, cached)
    classify_content(entries, "Policy", model_config.policy, onnx, cached)
    classify_content(entries, "Processing", model_config.processing, onnx, cached)
    classify_content(entries, "Purpose", model_config.purpose, onnx, cached)
    classify_content(entries, "Retention", model_config.retention, onnx, cached)
    classify_content(
        entries, "Security/Privacy", model_config.security_privacy, onnx, cached
    )
    classify_content(entries, "Selling", model_config.selling, onnx, cached)
    classify_content(entries, "Sharing", model_config.sharing, onnx, cached)
    classify_content(entries, "ThirdParty", model_config.third_party, onnx, cached)
    classify_content(entries, "UserRights", model_config.user_rights, onnx, cached)
    logger.debug("Classifications completed")

    logger.debug("Extracting attributes")
    # extract attributes
    extract_attributes(
        entries,
        topic=["Processing", "Retention", "Sharing", "Deletion", "Selling"],
        content="DataType",
        patterns=pattern_config.data_type,
    )
    extract_attributes(
        entries,
        topic=["Processing"],
        content="Method/Source",
        patterns=pattern_config.method_source,
    )
    extract_attributes(
        entries,
        topic=["Processing"],
        content="Tracking/Conversion",
        patterns=pattern_config.track_conv,
    )
    extract_attributes(
        entries,
        topic=["ThirdParty"],
        content="Descriptive",
        patterns=pattern_config.descriptive,
    )
    extract_attributes(
        entries,
        topic=["ThirdParty"],
        content="Company",
        patterns=pattern_config.company,
    )
    extract_attributes(
        entries,
        topic=["ThirdParty"],
        content="Official",
        patterns=pattern_config.official,
    )
    extract_attributes(
        entries,
        topic=["ThirdParty"],
        content="Chosen",
        patterns=pattern_config.chosen,
    )
    extract_attributes(
        entries,
        topic=["Retention", "Sharing", "Contact"],
        content="Country",
        patterns=pattern_config.country,
    )
    extract_attributes(
        entries,
        topic=["Audience"],
        content="Country",
        patterns=pattern_config.country,
    )
    extract_attributes(
        entries,
        topic=["Purpose"],
        content="ProvideService",
        patterns=pattern_config.provide_service,
    )
    extract_attributes(
        entries,
        topic=["Purpose"],
        content="Communication",
        patterns=pattern_config.communication,
    )
    extract_attributes(
        entries,
        topic=["Security/Privacy"],
        content="TechnicalPrivacyMeasures",
        patterns=pattern_config.tech_priv,
    )
    extract_attributes(
        entries,
        topic=["Security/Privacy"],
        content="TechnicalSecurityMeasures",
        patterns=pattern_config.tech_sec,
    )
    extract_attributes(
        entries,
        topic=["Security/Privacy"],
        content="ContractualSecurityMeasures",
        patterns=pattern_config.cont_sec,
    )
    extract_attributes(
        entries,
        topic=["Security/Privacy"],
        content="Certifications",
        patterns=pattern_config.certifications,
    )

    extract_duration(
        entries,
        topic=["Retention"],
        content="StorageDuration",
        patterns=duration_pattern_config,
    )
    extract_duration(
        entries,
        topic=["Deletion"],
        content="Inactivity",
        patterns=duration_pattern_config,
    )
    extract_duration(
        entries,
        topic=["Deletion"],
        content="WithinTimePeriod",
        patterns=duration_pattern_config,
    )
    extract_date(
        entries,
        topic=["Policy"],
        content="Change",
        patterns=date_pattern_config,
    )

    extract_email(
        entries,
        topic=["Contact"],
        content="Email",
        patterns=email_pattern_config,
    )

    logger.debug("Attribute extraction completed")


DEFAULT_MODEL_CONFIGS_EN: ModelConfigs = ModelConfigs(
    context=ModelConfig(
        model_name="Wravn/roberta-privacy-policy-context",
        thresholds={},
    ),
    topic=ModelConfig(
        model_name="Wravn/privbert-privacy-policy-topic",
        thresholds={
            "Purpose": 0.4,
            "Sharing": 0.6,
            "ThirdParty": 0.6,
            "Selling": 0.65,
            "Audience": 0.7,
        },
    ),
    audience=ModelConfig(
        model_name="Wravn/albert-privacy-policy-content-audience",
        thresholds={"Country": 0.4},
    ),
    contact=ModelConfig(
        model_name="Wravn/roberta-privacy-policy-content-contact",
        thresholds={"Website": 0.4},
    ),
    control=ModelConfig(
        model_name="Wravn/privbert-privacy-policy-content-control",
        thresholds={},
    ),
    deletion=ModelConfig(
        model_name="Wravn/distilbert-privacy-policy-content-deletion",
        thresholds={},
    ),
    legal_basis=ModelConfig(
        model_name="Wravn/privbert-privacy-policy-content-legalbasis",
        thresholds={},
    ),
    policy=ModelConfig(
        model_name="Wravn/roberta-privacy-policy-content-policy",
        thresholds={"Change": 0.4, "External": 0.65},
    ),
    processing=ModelConfig(
        model_name="Wravn/albert-privacy-policy-content-processing",
        thresholds={"Method/Source": 0.4},
    ),
    purpose=ModelConfig(
        model_name="Wravn/privbert-privacy-policy-content-purpose",
        thresholds={},
    ),
    retention=ModelConfig(
        model_name="Wravn/roberta-privacy-policy-content-retention",
        thresholds={"StorageDuration": 0.4},
    ),
    security_privacy=ModelConfig(
        model_name="Wravn/privbert-privacy-policy-content-securityprivacy",
        thresholds={"SecurityHints": 0.4},
    ),
    selling=ModelConfig(
        model_name="Wravn/roberta-privacy-policy-content-selling",
        thresholds={"NotSelling": 0.90},
    ),
    sharing=ModelConfig(
        model_name="Wravn/roberta-privacy-policy-content-sharing",
        thresholds={},
    ),
    third_party=ModelConfig(
        model_name="Wravn/privbert-privacy-policy-content-thirdparty",
        thresholds={"Company": 0.3, "Descriptive": 0.4},
    ),
    user_rights=ModelConfig(
        model_name="Wravn/privbert-privacy-policy-content-userrights",
        thresholds={},
    ),
)
"""
Default english model configurations for privacy policy analysis."""


DEFAULT_MODEL_CONFIGS_DE: ModelConfigs = ModelConfigs(
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
            "Event/Program": 0.55
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
            "Selling": 0.1
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
            "Bystanders": 0.15
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
            "Appeal": 0.2
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
            "CancelService": 0.5
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
            "WithinTimePeriod": 0.75
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
            "EmploymentProcedure": 0.1
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
            "External": 0.65
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
            "Method/Source": 0.1
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
            "Analytics": 0.1
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
            "CloudStorage": 0.35
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
            "Certifications": 0.1
        },
    ),
    selling=ModelConfig(
        model_name="Immerwinter/roberta-wechsel-privacy-policy-content-selling",
        thresholds={
            "Other": 0.4,
            "NotSelling": 0.45,
            "DataType": 0.25,
            "Merger/Acquisition": 0.2,
            "Insolvency": 0.2
        },
    ),
    sharing=ModelConfig(
        model_name="Immerwinter/gottbert-privacy-policy-content-sharing",
        thresholds={
            "Other": 0.4,
            "NotSharing": 0.15,
            "ByThirdParty": 0.45,
            "DataType": 0.65,
            "Country": 0.8
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
            "OtherUser": 0.1
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
            "NotBeDiscriminated": 0.15
        },
    ),
)
"""
Default german model configurations for privacy policy analysis."""
