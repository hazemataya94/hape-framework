from pathlib import Path

import pytest

import services.kube_agent.investigation.investigation_runtime as investigation_runtime_module
from services.kube_agent.investigation.findings.json_formatter import JsonFormatter
from services.kube_agent.investigation.findings.markdown_formatter import MarkdownFormatter
from services.kube_agent.investigation.findings.slack_formatter import SlackFormatter
from services.kube_agent.kube_agent_service import KubeAgentService
from utils.test_artifacts_utils import print_artifacts_directory


class _FakePrometheusClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    def query(self, promql: str) -> dict:
        return {"status": "success", "data": {"resultType": "vector", "result": []}}


class _FakeAlertmanagerClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    def get_alerts_by_labels(self, matchers: dict[str, str]) -> list[dict]:
        return []


class _FakeGrafanaClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    def list_dashboards(self) -> list[dict]:
        return [
            {"title": "Kubernetes / Compute Resources / Pod", "url": "/d/k8s-pod"},
            {"title": "Kubernetes / Compute Resources / Namespace (Pods)", "url": "/d/k8s-namespace-pods"},
            {"title": "Kubernetes / Views / Pods", "url": "/d/k8s-views-pods"},
        ]

    def find_dashboard_links(self, namespace: str | None, workload_name: str | None, node_name: str | None) -> dict[str, str]:
        return {"Kubernetes Pods Overview": f"{self.base_url}/d/k8s-views-pods"}


def _write_findings_artifacts(findings, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_formatter = MarkdownFormatter()
    slack_formatter = SlackFormatter()
    artifacts = {
        "summary_text_path": output_dir / "kube-agent-findings-summary.txt",
        "findings_json_path": output_dir / "kube-agent-findings.json",
        "findings_markdown_path": output_dir / "kube-agent-findings.md",
        "findings_slack_path": output_dir / "kube-agent-findings-slack.txt",
    }
    artifacts["summary_text_path"].write_text(findings.summary + "\n", encoding="utf-8")
    artifacts["findings_json_path"].write_text(JsonFormatter.format(findings=findings) + "\n", encoding="utf-8")
    artifacts["findings_markdown_path"].write_text(markdown_formatter.format(findings=findings), encoding="utf-8")
    artifacts["findings_slack_path"].write_text(slack_formatter.format(findings=findings) + "\n", encoding="utf-8")
    return artifacts


def test_kube_agent_investigate_pod_on_kind_cluster(apply_kube_agent_test_manifests: dict[str, str | None], monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(investigation_runtime_module, "PrometheusClient", _FakePrometheusClient)
    monkeypatch.setattr(investigation_runtime_module, "AlertmanagerClient", _FakeAlertmanagerClient)
    monkeypatch.setattr(investigation_runtime_module, "GrafanaClient", _FakeGrafanaClient)
    monkeypatch.setenv("HAPE_KUBE_AGENT_SQLITE_PATH", str(tmp_path / "kube-agent-functional.sqlite"))
    service = KubeAgentService()
    findings = service.investigate(
        raw_trigger={
            "type": "pod",
            "cluster": str(apply_kube_agent_test_manifests["kube_context"]),
            "namespace": str(apply_kube_agent_test_manifests["namespace"]),
            "name": str(apply_kube_agent_test_manifests["pod"]),
            "source": "cli",
        },
        use_ai=False,
    )
    assert findings.incident_id
    assert findings.title
    assert findings.summary
    assert findings.ai_used is False
    assert isinstance(findings.evidence_summary, list)
    assert findings.dashboard_links

    artifacts_dir = tmp_path / "kube-agent-functional-artifacts"
    artifact_paths = _write_findings_artifacts(findings=findings, output_dir=artifacts_dir)
    for artifact_name, artifact_path in artifact_paths.items():
        assert artifact_path.exists(), f"Expected artifact file does not exist: {artifact_name}"
        assert artifact_path.read_text(encoding="utf-8").strip(), f"Expected non-empty artifact file: {artifact_name}"

    incidents = service.list_incidents()
    assert incidents
    assert incidents[0].occurrence_count >= 1
    print_artifacts_directory(artifacts_directory=artifacts_dir)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
