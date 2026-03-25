import pytest

from core.errors.exceptions import HapeValidationError
from services.kube_agent.investigation.triggers.trigger_resolver import TriggerResolver


def test_resolve_valid_pod_trigger() -> None:
    trigger_resolver = TriggerResolver()
    trigger = trigger_resolver.resolve({"type": "pod", "cluster": "demo", "namespace": "payments", "pod": "api-7f9d5", "source": "cli"})
    assert trigger.type == "pod"
    assert trigger.cluster == "demo"
    assert trigger.namespace == "payments"
    assert trigger.name == "api-7f9d5"


def test_resolve_invalid_pod_trigger_missing_namespace() -> None:
    trigger_resolver = TriggerResolver()
    with pytest.raises(HapeValidationError) as raised_error:
        trigger_resolver.resolve({"type": "pod", "cluster": "demo", "pod": "api-7f9d5"})
    assert raised_error.value.code == "KUBE_AGENT_TRIGGER_NAMESPACE_REQUIRED"


def test_resolve_valid_alert_trigger_label_mapping() -> None:
    trigger_resolver = TriggerResolver()
    trigger = trigger_resolver.resolve({
        "type": "alert",
        "cluster": "demo",
        "alertname": "KubePodCrashLooping",
        "labels": {"severity": "warning", "namespace": "payments"},
        "annotations": {"summary": "Pod restarted frequently."},
    })
    assert trigger.type == "alert"
    assert trigger.name == "KubePodCrashLooping"
    assert trigger.labels["severity"] == "warning"


def test_resolve_valid_cost_trigger() -> None:
    trigger_resolver = TriggerResolver()
    trigger = trigger_resolver.resolve({
        "type": "cost",
        "cluster": "demo",
        "namespace": "payments",
        "deployment": "api",
        "metadata": {"historical_offset": "1h"},
    })
    assert trigger.type == "cost"
    assert trigger.name == "api"
    assert trigger.namespace == "payments"


def test_resolve_invalid_cost_trigger_missing_namespace() -> None:
    trigger_resolver = TriggerResolver()
    with pytest.raises(HapeValidationError) as raised_error:
        trigger_resolver.resolve({"type": "cost", "cluster": "demo", "deployment": "api"})
    assert raised_error.value.code == "KUBE_AGENT_TRIGGER_NAMESPACE_REQUIRED"


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", __file__]))
