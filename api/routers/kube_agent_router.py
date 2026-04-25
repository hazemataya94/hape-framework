from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from services.kube_agent.cost.cost_analysis_service import CostAnalysisService
from services.kube_agent.investigation.findings.json_formatter import JsonFormatter
from services.kube_agent.investigation.findings.markdown_formatter import MarkdownFormatter
from services.kube_agent.investigation.findings.slack_formatter import SlackFormatter
from services.kube_agent.kube_agent_service import KubeAgentService

router = APIRouter(prefix="/kube-agent", tags=["kube-agent"])


def _parse_bool_text(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _render_findings(findings, output: str) -> dict[str, object]:
    if output == "json":
        return {"output": JsonFormatter.format(findings=findings)}
    if output == "markdown":
        markdown_formatter = MarkdownFormatter()
        return {"output": markdown_formatter.format(findings=findings)}
    if output == "slack":
        slack_formatter = SlackFormatter()
        return {"output": slack_formatter.format(findings=findings)}
    return {"output": findings.summary}


class InvestigatePodRequest(BaseModel):
    kube_context: str
    namespace: str
    pod: str
    output: str = "text"
    use_ai: str = "false"


class InvestigateDeploymentRequest(BaseModel):
    kube_context: str
    namespace: str
    deployment: str
    output: str = "text"
    use_ai: str = "false"


class InvestigateNodeRequest(BaseModel):
    kube_context: str
    node: str
    output: str = "text"
    use_ai: str = "false"


class InvestigateAlertRequest(BaseModel):
    kube_context: str
    alertname: str
    namespace: str | None = None
    pod: str | None = None
    node: str | None = None
    output: str = "text"
    use_ai: str = "false"


class CostAnalyzeRequest(BaseModel):
    kube_context: str
    namespace: str
    deployment: str | None = None
    all_workloads: bool = False
    historical_offset: str = "1h"
    output: str = "text"
    use_ai: str = "false"


class IncidentsListRequest(BaseModel):
    output: str = "text"


class IncidentsShowRequest(BaseModel):
    incident_id: str
    output: str = "text"


@router.post("/investigate/pod")
def investigate_pod(payload: InvestigatePodRequest) -> dict[str, object]:
    service = KubeAgentService()
    findings = service.investigate(
        raw_trigger={"type": "pod", "cluster": payload.kube_context, "name": payload.pod, "namespace": payload.namespace, "source": "api"},
        use_ai=_parse_bool_text(payload.use_ai),
    )
    return _render_findings(findings=findings, output=payload.output)


@router.post("/investigate/deployment")
def investigate_deployment(payload: InvestigateDeploymentRequest) -> dict[str, object]:
    service = KubeAgentService()
    findings = service.investigate(
        raw_trigger={"type": "deployment", "cluster": payload.kube_context, "name": payload.deployment, "namespace": payload.namespace, "source": "api"},
        use_ai=_parse_bool_text(payload.use_ai),
    )
    return _render_findings(findings=findings, output=payload.output)


@router.post("/investigate/node")
def investigate_node(payload: InvestigateNodeRequest) -> dict[str, object]:
    service = KubeAgentService()
    findings = service.investigate(
        raw_trigger={"type": "node", "cluster": payload.kube_context, "name": payload.node, "source": "api"},
        use_ai=_parse_bool_text(payload.use_ai),
    )
    return _render_findings(findings=findings, output=payload.output)


@router.post("/investigate/alert")
def investigate_alert(payload: InvestigateAlertRequest) -> dict[str, object]:
    service = KubeAgentService()
    labels: dict[str, str] = {}
    if payload.namespace:
        labels["namespace"] = payload.namespace
    if payload.pod:
        labels["pod"] = payload.pod
    if payload.node:
        labels["node"] = payload.node
    findings = service.investigate(
        raw_trigger={
            "type": "alert",
            "cluster": payload.kube_context,
            "name": payload.alertname,
            "source": "api",
            "labels": labels,
            "namespace": payload.namespace,
        },
        use_ai=_parse_bool_text(payload.use_ai),
    )
    return _render_findings(findings=findings, output=payload.output)


@router.post("/cost-analyze")
def cost_analyze(payload: CostAnalyzeRequest) -> dict[str, object]:
    service = CostAnalysisService()
    findings = service.analyze(
        kube_context=payload.kube_context,
        namespace=payload.namespace,
        deployment=payload.deployment,
        all_workloads=payload.all_workloads,
        historical_offset=payload.historical_offset,
        use_ai=_parse_bool_text(payload.use_ai),
    )
    return _render_findings(findings=findings, output=payload.output)


@router.post("/incidents/list")
def incidents_list(payload: IncidentsListRequest) -> dict[str, object]:
    service = KubeAgentService()
    incidents = service.list_incidents()
    if payload.output == "json":
        return {"incidents": [item.__dict__ for item in incidents]}
    rows = [f"{incident.incident_id} | {incident.last_seen.isoformat()} | {incident.latest_likely_cause or 'unknown'}" for incident in incidents]
    return {"lines": rows}


@router.post("/incidents/show")
def incidents_show(payload: IncidentsShowRequest) -> dict[str, object]:
    service = KubeAgentService()
    incident = service.get_incident(incident_id=payload.incident_id)
    if incident is None:
        return {"message": f"Incident not found: {payload.incident_id}"}
    if payload.output == "json":
        return {"incident": incident.__dict__}
    return {
        "incident_id": incident.incident_id,
        "fingerprint": incident.fingerprint,
        "first_seen": incident.first_seen.isoformat(),
        "last_seen": incident.last_seen.isoformat(),
        "occurrence_count": incident.occurrence_count,
        "latest_likely_cause": incident.latest_likely_cause or "unknown",
    }
