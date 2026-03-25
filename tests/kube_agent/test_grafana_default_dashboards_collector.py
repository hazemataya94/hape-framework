from datetime import UTC, datetime

from services.kube_agent.investigation.evidence.collectors.grafana_default_dashboards_collector import GrafanaDefaultDashboardsCollector
from services.kube_agent.investigation.evidence.evidence_models import EvidenceItem
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class _FakeGrafanaClient:
    def __init__(self) -> None:
        self.base_url = "http://grafana.local"

    def list_dashboards(self) -> list[dict]:
        return [
            {"title": "Kubernetes / Compute Resources / Pod", "url": "/d/k8s-pod"},
            {"title": "Kubernetes / Compute Resources / Namespace (Pods)", "url": "/d/k8s-namespace-pods"},
            {"title": "Kubernetes / Networking / Pod", "url": "/d/k8s-networking-pod"},
            {"title": "Kubernetes / Compute Resources / Node (Pods)", "url": "/d/k8s-node-pods"},
            {"title": "Node Exporter / Nodes", "url": "/d/node-exporter-nodes"},
            {"title": "Kubernetes / Views / Pods", "url": "/d/k8s-views-pods"},
            {"title": "Kubernetes / Views / Nodes", "url": "/d/k8s-views-nodes"},
        ]


def test_collect_pod_dashboards_with_context_vars() -> None:
    collector = GrafanaDefaultDashboardsCollector()
    trigger = Trigger(type="pod", cluster="demo", namespace="payments", name="api")
    evidence_items = [
        EvidenceItem(
            key="kubernetes.pod.events",
            source="kubernetes",
            resource_ref="pod/payments/api",
            value=[{"reason": "Killing", "message": "Container was OOMKilled"}],
            observed_at=datetime.now(UTC),
            metadata={},
        )
    ]
    links = collector.collect(trigger=trigger, evidence_items=evidence_items, grafana_client=_FakeGrafanaClient())
    assert "Kubernetes Pod Resources" in links
    assert "var-namespace=payments" in links["Kubernetes Pod Resources"]
    assert "var-pod=api" in links["Kubernetes Pod Resources"]
    assert "Kubernetes Pods Overview" in links


def test_collect_node_dashboards_for_scheduling_signals() -> None:
    collector = GrafanaDefaultDashboardsCollector()
    trigger = Trigger(type="node", cluster="demo", namespace=None, name="node-1")
    evidence_items = [
        EvidenceItem(
            key="kubernetes.pod.scheduling_failures",
            source="kubernetes",
            resource_ref="pod/payments/api",
            value=[{"reason": "FailedScheduling", "message": "Insufficient memory"}],
            observed_at=datetime.now(UTC),
            metadata={},
        )
    ]
    links = collector.collect(trigger=trigger, evidence_items=evidence_items, grafana_client=_FakeGrafanaClient())
    assert "Kubernetes Node Resources" in links
    assert "var-node=node-1" in links["Kubernetes Node Resources"]
    assert "Node Exporter Nodes" in links


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main(["-q", __file__]))
