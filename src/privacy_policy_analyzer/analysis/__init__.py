from privacy_policy_analyzer.analysis.attributes import (
    AttributePatterns,
    DatePattern,
    DurationPattern,
    EmailPattern,
    PhonePattern,
    UrlPattern,
    extract_attributes,
    extract_date,
    extract_duration,
    extract_email,
    extract_phone,
    extract_url,
)
from privacy_policy_analyzer.analysis.classification import (
    ModelConfigs,
    classify_content,
    classify_scope,
    classify_topics,
)
from privacy_policy_analyzer.analysis.err import ModelLoadError
from privacy_policy_analyzer.analysis.ner import NERModelConfigs, extract_entities
from privacy_policy_analyzer.shared.annotation import RawEntry
from privacy_policy_analyzer.shared.logging import get_logger

logger = get_logger(__name__)


def classify_scopes_and_topics(
    entries: list[RawEntry],
    model_config: ModelConfigs,
    prefer_onnx: bool,
    cached: bool,
) -> ModelLoadError | None:
    """Classify scopes and topics only (no contents, no attributes) - the
    first stage, run before header propagation so content classification can
    later see topics inherited from parent headers."""
    try:
        logger.debug("Classifying scopes and topics for entries=%d", len(entries))
        classify_scope(entries, model_config.scope, prefer_onnx, cached)
        classify_topics(entries, model_config.topic, prefer_onnx, cached)
    except ModelLoadError as e:
        return e

    return None


def classify_contents(
    entries: list[RawEntry],
    model_config: ModelConfigs,
    prefer_onnx: bool,
    cached: bool,
) -> ModelLoadError | None:
    """Classify contents for every topic - run after header propagation has
    filled in topics on entries that only had them via a parent header, and
    before header propagation runs again so those contents also propagate."""
    try:
        logger.debug("Classifying contents for entries=%d", len(entries))
        for topic, content_config in model_config.content_models().items():
            classify_content(entries, topic, content_config, prefer_onnx, cached)
        logger.debug("Content classification completed")
    except ModelLoadError as e:
        return e

    return None


def extract_all_attributes(
    entries: list[RawEntry],
    pattern_config: AttributePatterns,
    duration_pattern_config: DurationPattern,
    date_pattern_config: DatePattern,
    email_pattern_config: EmailPattern,
    url_pattern_config: UrlPattern,
    phone_pattern_config: PhonePattern,
    ner_model_config: NERModelConfigs,
    use_ner_for_company: bool,
    prefer_onnx: bool,
    cached: bool,
) -> ModelLoadError | None:
    """Extract attributes for every content - the final stage, run after
    both header propagation passes so it sees the fully propagated topics
    and contents."""
    try:
        logger.debug("Extracting attributes")
        extract_attributes(
            entries,
            topic=["Processing", "Retention", "Sharing", "Deletion", "Selling"],
            content="DataType",
            patterns=pattern_config.data_type,
        )
        extract_attributes(
            entries,
            topic=["Processing"],
            content="Source",
            patterns=pattern_config.method_source,
        )
        extract_attributes(
            entries,
            topic=["Processing", "Sharing"],
            content="TriggerCondition",
            patterns=pattern_config.trigger_condition,
        )
        extract_attributes(
            entries,
            topic=["Control"],
            content="Consequences",
            patterns=pattern_config.consequences,
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
        extract_attributes(
            entries,
            topic=["ThirdParty"],
            content="PluginIntegration",
            patterns=pattern_config.plugin_integration,
        )
        if use_ner_for_company:
            extract_entities(
                entries,
                topic=["ThirdParty"],
                content="Company",
                config=ner_model_config.company,
                prefer_onnx=prefer_onnx,
                cached=cached,
            )
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
            content="ChosenIndividual",
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
        extract_attributes(
            entries,
            topic=["Policy"],
            content="UserResponsibility",
            patterns=pattern_config.user_responsibility,
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

        extract_url(
            entries,
            topic=["Contact"],
            content="Website",
            patterns=url_pattern_config,
        )

        extract_phone(
            entries,
            topic=["Contact"],
            content="Phone",
            patterns=phone_pattern_config,
        )

        logger.debug("Attribute extraction completed")
    except ModelLoadError as e:
        return e

    return None
