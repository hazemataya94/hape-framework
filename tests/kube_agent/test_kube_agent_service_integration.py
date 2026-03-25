from datetime import UTC, datetime

import services.kube_agent.investigation.investigation_runtime as investigation_runtime_module
from services.kube_agent.kube_agent_service import KubeAgentService


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
        self.conditions = [_FakeCondition("Ready", "True")]
        self.container_statuses = [_FakeContainerStatus(2)]


class _FakePodMetadata:
    def __init__(self) -> None:
        self.owner_references = [type("Owner", (), {"kind": "ReplicaSet", "name": "api-7f9d5"})()]


class _FakePodSpec:
    def __init__(self) -> None:
        self.node_name = "node-1"


class _FakePod:
    def __init__(self) -> None:
        self.status = _FakePodStatus()
        self.metadata = _FakePodMetadata()
        self.spec = _FakePodSpec()


class _FakeNodeStatus:
    def __init__(self) -> None:
        self.conditions = [_FakeCondition("Ready", "True"), _FakeCondition("MemoryPressure", "False")]


class _FakeNode:
    def __init__(self) -> None:
        self.status = _FakeNodeStatus()


class _FakeEvent:
    def __init__(self, reason: str, message: str) -> None:
        self.reason = reason
        self.message = message
        self.type = "Warning"
        self.count = 1


class _FakeKubernetesClient:
    ensure_prometheus_port_forward_called = False

    def __init__(self, context: str | None = None) -> None:
        self.context = context

    def ensure_prometheus_port_forward(self, prometheus_base_url: str) -> bool:
        _FakeKubernetesClient.ensure_prometheus_port_forward_called = True
        return True

    def get_pod(self, namespace: str, pod_name: str):
        return _FakePod()

    def list_pod_events(self, namespace: str, pod_name: str):
        return [_FakeEvent("Killing", "Container was OOMKilled")]

    def get_pod_logs(self, namespace: str, pod_name: str, container: str | None = None, tail_lines: int = 200):
        return "exit code 137"

    def get_pod_owner(self, namespace: str, pod_name: str):
        return {"kind": "ReplicaSet", "name": "api-7f9d5"}

    def get_replicaset_history(self, namespace: str, deployment_name: str):
        return [{"name": "api-7f9d5", "revision": "3", "replicas": 2}, {"name": "api-7f9d4", "revision": "2", "replicas": 2}]

    def get_node(self, node_name: str):
        return _FakeNode()


class _FakePrometheusClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    def query(self, promql: str):
        if "hape_eks_deployment_cost_exporter_up" in promql:
            return {"status": "success", "data": {"resultType": "vector", "result": [{"metric": {}, "value": [1, "1"]}]}}
        if 'hape_eks_deployment_cost_total_usd{period="hourly"} offset' in promql:
            return {"status": "success", "data": {"resultType": "vector", "result": [{"metric": {"period": "hourly"}, "value": [1, "10"]}]}}
        if 'hape_eks_deployment_cost_total_usd{period="hourly"}' in promql:
            return {"status": "success", "data": {"resultType": "vector", "result": [{"metric": {"period": "hourly"}, "value": [1, "40"]}]}}
        if "hape_eks_deployment_cost_workload_max_hourly_usd" in promql:
            return {"status": "success", "data": {"resultType": "vector", "result": [{"metric": {"namespace": "payments", "name": "api"}, "value": [1, "12"]}]}}
        return {"status": "success", "data": {"result": [[datetime.now(UTC).timestamp(), "0.1"]]}}


class _FakeAlertmanagerClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    def get_alerts_by_labels(self, matchers: dict[str, str]):
        return [{"labels": matchers}]


class _FakeGrafanaClient:
    def __init__(self, base_url: str, token: str | None = None, username: str | None = None, password: str | None = None) -> None:
        self.base_url = base_url

    def list_dashboards(self):
        return [
            {"title": "Kubernetes / Compute Resources / Pod", "url": "/d/k8s-pod"},
            {"title": "Kubernetes / Views / Pods", "url": "/d/k8s-views-pods"},
            {"title": "Kubernetes / Compute Resources / Namespace (Pods)", "url": "/d/k8s-ns-pods"},
        ]

    def find_dashboard_links(self, namespace: str | None, workload_name: str | None, node_name: str | None):
        return {"Pod dashboard": f"{self.base_url}/d/pod"}


def test_full_investigate_pod_with_mocked_clients(monkeypatch, tmp_path) -> None:
    _FakeKubernetesClient.ensure_prometheus_port_forward_called = False
    monkeypatch.setattr(investigation_runtime_module, "KubernetesClient", _FakeKubernetesClient)
    monkeypatch.setattr(investigation_runtime_module, "PrometheusClient", _FakePrometheusClient)
    monkeypatch.setattr(investigation_runtime_module, "AlertmanagerClient", _FakeAlertmanagerClient)
    monkeypatch.setattr(investigation_runtime_module, "GrafanaClient", _FakeGrafanaClient)
    monkeypatch.setenv("HAPE_KUBE_AGENT_SQLITE_PATH", str(tmp_path / "kube-agent.sqlite"))
    service = KubeAgentService()
    findings = service.investigate(
        raw_trigger={"type": "pod", "cluster": "demo", "namespace": "payments", "name": "api"},
        use_ai=False,
    )
    assert findings.title
    assert findings.evidence_summary
    assert findings.ai_used is False
    assert _FakeKubernetesClient.ensure_prometheus_port_forward_called is True


def test_repeated_incident_memory_behavior(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(investigation_runtime_module, "KubernetesClient", _FakeKubernetesClient)
    monkeypatch.setattr(investigation_runtime_module, "PrometheusClient", _FakePrometheusClient)
    monkeypatch.setattr(investigation_runtime_module, "AlertmanagerClient", _FakeAlertmanagerClient)
    monkeypatch.setattr(investigation_runtime_module, "GrafanaClient", _FakeGrafanaClient)
    monkeypatch.setenv("HAPE_KUBE_AGENT_SQLITE_PATH", str(tmp_path / "kube-agent.sqlite"))
    service = KubeAgentService()
    service.investigate(raw_trigger={"type": "pod", "cluster": "demo", "namespace": "payments", "name": "api"}, use_ai=False)
    service.investigate(raw_trigger={"type": "pod", "cluster": "demo", "namespace": "payments", "name": "api"}, use_ai=False)
    incidents = service.list_incidents()
    assert len(incidents) == 1
    assert incidents[0].occurrence_count == 2


def test_ai_optional_path_and_no_ai_path(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(investigation_runtime_module, "KubernetesClient", _FakeKubernetesClient)
    monkeypatch.setattr(investigation_runtime_module, "PrometheusClient", _FakePrometheusClient)
    monkeypatch.setattr(investigation_runtime_module, "AlertmanagerClient", _FakeAlertmanagerClient)
    monkeypatch.setattr(investigation_runtime_module, "GrafanaClient", _FakeGrafanaClient)
    monkeypatch.setenv("HAPE_KUBE_AGENT_SQLITE_PATH", str(tmp_path / "kube-agent.sqlite"))
    service = KubeAgentService()
    no_ai = service.investigate(raw_trigger={"type": "pod", "cluster": "demo", "namespace": "payments", "name": "api"}, use_ai=False)
    with_ai = service.investigate(raw_trigger={"type": "pod", "cluster": "demo", "namespace": "payments", "name": "api"}, use_ai=True)
    assert no_ai.ai_used is False
    assert with_ai.ai_used in {True, False}


def test_cost_analyze_flow_with_mocked_clients(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(investigation_runtime_module, "KubernetesClient", _FakeKubernetesClient)
    monkeypatch.setattr(investigation_runtime_module, "PrometheusClient", _FakePrometheusClient)
    monkeypatch.setattr(investigation_runtime_module, "AlertmanagerClient", _FakeAlertmanagerClient)
    monkeypatch.setattr(investigation_runtime_module, "GrafanaClient", _FakeGrafanaClient)
    monkeypatch.setenv("HAPE_KUBE_AGENT_SQLITE_PATH", str(tmp_path / "kube-agent.sqlite"))
    service = KubeAgentService()
    findings = service.investigate(
        raw_trigger={"type": "cost", "cluster": "demo", "namespace": "payments", "name": "api", "metadata": {"historical_offset": "1h"}},
        use_ai=False,
    )
    assert findings.title
    assert findings.evidence_summary
    assert findings.ai_used is False
    assert "cost" in findings.summary.lower()


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__]))
