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


DEFAULT_MODEL_CONFIGS: ModelConfigs = ModelConfigs(
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
Default model configurations for privacy policy analysis."""
