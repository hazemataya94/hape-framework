from datetime import UTC, datetime

from services.kube_agent.investigation.evidence.collectors.pod_events_collector import PodEventsCollector
from services.kube_agent.investigation.evidence.collectors.pod_logs_collector import PodLogsCollector
from services.kube_agent.investigation.evidence.collectors.pod_metrics_collector import PodMetricsCollector
from services.kube_agent.investigation.evidence.collectors.pod_status_collector import PodStatusCollector
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class _FakeCondition:
    def __init__(self, condition_type: str, status: str, reason: str = "", message: str = "") -> None:
        self.type = condition_type
        self.status = status
        self.reason = reason
        self.message = message


class _FakeContainerStatus:
    def __init__(self, restart_count: int) -> None:
        self.restart_count = restart_count


class _FakePodStatus:
    def __init__(self) -> None:
        self.phase = "Running"
        self.conditions = [_FakeCondition("Ready", "True", "ContainersReady", "all good")]
        self.container_statuses = [_FakeContainerStatus(2), _FakeContainerStatus(1)]


class _FakePodSpec:
    def __init__(self) -> None:
        self.node_name = "node-1"


class _FakePod:
    def __init__(self) -> None:
        self.status = _FakePodStatus()
        self.spec = _FakePodSpec()


class _FakeEvent:
    def __init__(self, reason: str, message: str, event_type: str = "Warning", count: int = 1) -> None:
        self.reason = reason
        self.message = message
        self.type = event_type
        self.count = count


class _FakeKubernetesClient:
    def __init__(self) -> None:
        self.last_tail_lines = 0

    def get_pod(self, namespace: str, pod_name: str):
        return _FakePod()

    def list_pod_events(self, namespace: str, pod_name: str) -> list[_FakeEvent]:
        return [_FakeEvent("Killing", "Container was OOMKilled", count=3)]

    def get_pod_logs(self, namespace: str, pod_name: str, container: str | None = None, tail_lines: int = 200) -> str:
        self.last_tail_lines = tail_lines
        return "line1\nline2\nline3"


class _FakePrometheusClient:
    def query(self, promql: str) -> dict:
        return {"status": "success", "data": {"resultType": "vector", "result": [{"value": [datetime.now(UTC).timestamp(), "0.1"]}]}}


def test_pod_status_evidence_normalization() -> None:
    trigger = Trigger(type="pod", cluster="demo", namespace="payments", name="api")
    collector = PodStatusCollector()
    items = collector.collect(trigger=trigger, kubernetes_client=_FakeKubernetesClient())
    assert len(items) == 1
    assert items[0].key == "kubernetes.pod.status"
    assert items[0].value["phase"] == "Running"
    assert items[0].value["restart_count"] == 3


def test_pod_events_evidence_normalization() -> None:
    trigger = Trigger(type="pod", cluster="demo", namespace="payments", name="api")
    collector = PodEventsCollector()
    items = collector.collect(trigger=trigger, kubernetes_client=_FakeKubernetesClient())
    assert len(items) == 1
    assert items[0].key == "kubernetes.pod.events"
    assert items[0].value[0]["reason"] == "Killing"
    assert items[0].metadata["event_count"] == 1


def test_pod_logs_truncation_behavior() -> None:
    trigger = Trigger(type="pod", cluster="demo", namespace="payments", name="api")
    kubernetes_client = _FakeKubernetesClient()
    collector = PodLogsCollector()
    items = collector.collect(trigger=trigger, kubernetes_client=kubernetes_client, tail_lines=42)
    assert len(items) == 1
    assert items[0].metadata["tail_lines"] == 42
    assert kubernetes_client.last_tail_lines == 42


def test_prometheus_metric_normalization() -> None:
    trigger = Trigger(type="pod", cluster="demo", namespace="payments", name="api")
    collector = PodMetricsCollector()
    items = collector.collect(trigger=trigger, prometheus_client=_FakePrometheusClient())
    assert len(items) == 1
    assert items[0].key == "prometheus.pod.restarts.rate"
    assert "promql" in items[0].metadata


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main(["-q", __file__]))
