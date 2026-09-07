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
    ModelConfigs,
    classify_content,
    classify_context,
    classify_topics,
)
from privacy_policy_analyzer.analysis.err import ModelLoadError
from privacy_policy_analyzer.analysis.ner import NERModelConfigs, extract_entities
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
    ner_model_config: NERModelConfigs,
    use_ner_for_company: bool,
    prefer_onnx: bool,
    cached: bool,
) -> ModelLoadError | None:
    try:
        # classify contexts, topics, and contents
        logger.debug(
            "Classifying contexts, topics, and contents for entries=%d", len(entries)
        )
        classify_context(entries, model_config.context, prefer_onnx, cached)
        classify_topics(entries, model_config.topic, prefer_onnx, cached)
        classify_content(
            entries, "Audience", model_config.audience, prefer_onnx, cached
        )
        classify_content(entries, "Contact", model_config.contact, prefer_onnx, cached)
        classify_content(entries, "Control", model_config.control, prefer_onnx, cached)
        classify_content(
            entries, "Deletion", model_config.deletion, prefer_onnx, cached
        )
        classify_content(
            entries, "LegalBasis", model_config.legal_basis, prefer_onnx, cached
        )
        classify_content(entries, "Policy", model_config.policy, prefer_onnx, cached)
        classify_content(
            entries, "Processing", model_config.processing, prefer_onnx, cached
        )
        classify_content(entries, "Purpose", model_config.purpose, prefer_onnx, cached)
        classify_content(
            entries, "Retention", model_config.retention, prefer_onnx, cached
        )
        classify_content(
            entries,
            "Security/Privacy",
            model_config.security_privacy,
            prefer_onnx,
            cached,
        )
        classify_content(entries, "Selling", model_config.selling, prefer_onnx, cached)
        classify_content(entries, "Sharing", model_config.sharing, prefer_onnx, cached)
        classify_content(
            entries, "ThirdParty", model_config.third_party, prefer_onnx, cached
        )
        classify_content(
            entries, "UserRights", model_config.user_rights, prefer_onnx, cached
        )
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
            topic=["Processing"],
            content="Profiling",
            patterns=pattern_config.profiling,
        )
        extract_attributes(
            entries,
            topic=["Processing"],
            content="AutomatedDecisionMaking",
            patterns=pattern_config.automated_decision,
        )
        extract_attributes(
            entries,
            topic=["ThirdParty"],
            content="Descriptive",
            patterns=pattern_config.descriptive,
        )
        if use_ner_for_company:
            extract_entities(entries, ner_model_config.company, prefer_onnx, cached)
        else:
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
    except ModelLoadError as e:
        return e

    return None
