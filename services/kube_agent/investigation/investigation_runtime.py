from typing import Any

from clients.alertmanager_client import AlertmanagerClient
from clients.grafana_client import GrafanaClient
from clients.kubernetes_client import KubernetesClient
from clients.prometheus_client import PrometheusClient
from services.kube_agent.ai.ai_explainer import AiExplainer
from services.kube_agent.investigation.case.incident_case_builder import IncidentCaseBuilder
from services.kube_agent.investigation.checks.diagnostic_check_engine import DiagnosticCheckEngine
from services.kube_agent.config.kube_agent_config import KubeAgentConfig
from services.kube_agent.investigation.evidence.evidence_collector import EvidenceCollector
from services.kube_agent.investigation.findings.findings_builder import FindingsBuilder
from services.kube_agent.investigation.findings.findings_models import Findings
from services.kube_agent.investigation.memory.incident_memory_service import IncidentMemoryService
from services.kube_agent.investigation.triggers.trigger_resolver import TriggerResolver


class InvestigationRuntime:
    DEFAULT_TRIGGER_RESOLVER: TriggerResolver | None = None
    DEFAULT_EVIDENCE_COLLECTOR: EvidenceCollector | None = None
    DEFAULT_DIAGNOSTIC_CHECK_ENGINE: DiagnosticCheckEngine | None = None
    DEFAULT_INCIDENT_CASE_BUILDER: IncidentCaseBuilder | None = None
    DEFAULT_FINDINGS_BUILDER: FindingsBuilder | None = None
    DEFAULT_AI_EXPLAINER: AiExplainer | None = None
    DEFAULT_INCIDENT_MEMORY_SERVICE: IncidentMemoryService | None = None
    DEFAULT_CONFIG: KubeAgentConfig | None = None

    def __init__(
        self,
        trigger_resolver: TriggerResolver | None = DEFAULT_TRIGGER_RESOLVER,
        evidence_collector: EvidenceCollector | None = DEFAULT_EVIDENCE_COLLECTOR,
        diagnostic_check_engine: DiagnosticCheckEngine | None = DEFAULT_DIAGNOSTIC_CHECK_ENGINE,
        incident_case_builder: IncidentCaseBuilder | None = DEFAULT_INCIDENT_CASE_BUILDER,
        findings_builder: FindingsBuilder | None = DEFAULT_FINDINGS_BUILDER,
        ai_explainer: AiExplainer | None = DEFAULT_AI_EXPLAINER,
        incident_memory_service: IncidentMemoryService | None = DEFAULT_INCIDENT_MEMORY_SERVICE,
        config: KubeAgentConfig | None = DEFAULT_CONFIG,
    ) -> None:
        self.config = config or KubeAgentConfig.load()
        self.trigger_resolver = trigger_resolver or TriggerResolver()
        self.evidence_collector = evidence_collector or EvidenceCollector()
        self.diagnostic_check_engine = diagnostic_check_engine or DiagnosticCheckEngine()
        self.incident_case_builder = incident_case_builder or IncidentCaseBuilder()
        self.findings_builder = findings_builder or FindingsBuilder()
        self.ai_explainer = ai_explainer or AiExplainer()
        self.incident_memory_service = incident_memory_service or IncidentMemoryService(
            sqlite_path=self.config.sqlite_path,
            ai_stale_after_hours=self.config.stale_ai_hours,
        )

    def investigate(self, raw_trigger: dict[str, Any], use_ai: bool | None = None) -> Findings:
        trigger = self.trigger_resolver.resolve(raw_trigger=raw_trigger)
        previous_incident = self.incident_memory_service.find_existing(trigger=trigger)
        kubernetes_client = KubernetesClient(context=trigger.cluster)
        ensure_port_forward = getattr(kubernetes_client, "ensure_prometheus_port_forward", None)
        if callable(ensure_port_forward):
            ensure_port_forward(prometheus_base_url=self.config.prometheus_base_url)
        ensure_grafana_port_forward = getattr(kubernetes_client, "ensure_grafana_port_forward", None)
        if callable(ensure_grafana_port_forward):
            ensure_grafana_port_forward(grafana_base_url=self.config.grafana_base_url)
        prometheus_client = PrometheusClient(base_url=self.config.prometheus_base_url)
        alertmanager_client = AlertmanagerClient(base_url=self.config.alertmanager_base_url)
        grafana_client = GrafanaClient(
            base_url=self.config.grafana_base_url,
            token=self.config.grafana_token,
            username=self.config.grafana_username,
            password=self.config.grafana_password,
        )
        evidence = self.evidence_collector.collect(
            trigger=trigger,
            kubernetes_client=kubernetes_client,
            prometheus_client=prometheus_client,
            alertmanager_client=alertmanager_client,
            grafana_client=grafana_client,
        )
        check_results = self.diagnostic_check_engine.run(trigger=trigger, evidence=evidence)
        incident_case = self.incident_case_builder.build(trigger=trigger, evidence=evidence, check_results=check_results)
        resolved_use_ai = self.config.default_use_ai if use_ai is None else use_ai
        should_run_ai = resolved_use_ai and self.incident_memory_service.should_run_ai(
            trigger=trigger,
            incident_case=incident_case,
            previous_incident=previous_incident,
        )
        ai_explanation = self.ai_explainer.explain(incident_case=incident_case) if should_run_ai else None
        findings = self.findings_builder.build(incident_case=incident_case, ai_explanation=ai_explanation)
        self.incident_memory_service.save(trigger=trigger, incident_case=incident_case, findings=findings)
        return findings


if __name__ == "__main__":
    investigation_runtime = InvestigationRuntime()
    print(investigation_runtime.__class__.__name__)
