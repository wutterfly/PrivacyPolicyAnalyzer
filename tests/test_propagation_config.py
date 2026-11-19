import pytest

from privacy_policy_analyzer.analysis.classification import ModelConfig, ModelConfigs
from privacy_policy_analyzer.config import (
    DEFAULT_CONFIGURATIONS,
    PipelineConfiguration,
    PropagationConfig,
)


def make_model_configs(
    context: dict[str, float] | None = None,
    topic: dict[str, float] | None = None,
    sharing: dict[str, float] | None = None,
) -> ModelConfigs:
    configs = {
        name: ModelConfig(name, {})
        for name in (
            "audience",
            "contact",
            "control",
            "deletion",
            "legal_basis",
            "policy",
            "processing",
            "purpose",
            "retention",
            "security_privacy",
            "selling",
            "third_party",
            "user_rights",
        )
    }
    return ModelConfigs(
        context=ModelConfig("context", context or {}),
        topic=ModelConfig("topic", topic or {}),
        sharing=ModelConfig("sharing", sharing or {}),
        **configs,
    )


def test_default_config_propagates_everything_without_a_gate():
    config = PropagationConfig()
    assert config.enabled
    assert not config.gated
    assert config.build_gate(make_model_configs()) is None


def test_any_positive_value_turns_the_gate_on():
    assert PropagationConfig(topic_floor_ratio=0.1).gated
    assert PropagationConfig(min_score=0.05).gated


def test_disabled_propagation_has_no_gate_whatever_the_ratios_are():
    config = PropagationConfig(enabled=False, topic_floor_ratio=0.5, min_score=0.2)
    assert not config.enabled
    assert not config.gated
    assert config.build_gate(make_model_configs()) is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"context_floor_ratio": -0.1},
        {"topic_floor_ratio": 1.5},
        {"content_floor_ratio": 2},
        {"min_score": -1},
    ],
)
def test_values_outside_zero_to_one_are_rejected(kwargs):
    with pytest.raises(ValueError):
        PropagationConfig(**kwargs)


def test_floor_is_ratio_times_the_threshold_of_the_label():
    gate = PropagationConfig(topic_floor_ratio=0.5).build_gate(
        make_model_configs(topic={"Sharing": 0.6, "Contact": 0.3})
    )
    assert gate is not None
    assert gate.topics.get("Sharing") == pytest.approx(0.3)
    assert gate.topics.get("Contact") == pytest.approx(0.15)


def test_labels_without_a_threshold_use_the_default_threshold():
    gate = PropagationConfig(context_floor_ratio=0.5).build_gate(make_model_configs())
    assert gate is not None
    assert gate.contexts.get("Website") == pytest.approx(0.25)  # 0.5 * 0.5


def test_ratios_apply_per_kind_of_label():
    gate = PropagationConfig(topic_floor_ratio=1.0).build_gate(
        make_model_configs(topic={"Sharing": 0.6})
    )
    assert gate is not None
    assert gate.topics.get("Sharing") == pytest.approx(0.6)
    assert gate.contexts.get("Website") == 0.0
    assert gate.contents["Sharing"].get("DataType") == 0.0


def test_min_score_is_a_lower_bound_for_the_floor():
    gate = PropagationConfig(topic_floor_ratio=0.5, min_score=0.2).build_gate(
        make_model_configs(topic={"Sharing": 0.6, "Contact": 0.1})
    )
    assert gate is not None
    assert gate.topics.get("Sharing") == pytest.approx(0.3)
    assert gate.topics.get("Contact") == pytest.approx(0.2)  # 0.05 raised to 0.2


def test_content_floors_come_from_the_model_of_the_topic():
    gate = PropagationConfig(content_floor_ratio=0.5).build_gate(
        make_model_configs(sharing={"Country": 0.8})
    )
    assert gate is not None
    assert gate.contents["Sharing"].get("Country") == pytest.approx(0.4)
    assert gate.contents["Retention"].get("Country") == pytest.approx(0.25)
    assert len(gate.contents) == 14


def test_default_configurations_propagate_without_a_gate():
    for config in DEFAULT_CONFIGURATIONS.values():
        assert isinstance(config, PipelineConfiguration)
        assert config.propagation.enabled
        assert not config.propagation.gated
