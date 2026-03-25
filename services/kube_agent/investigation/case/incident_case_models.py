from dataclasses import dataclass, field

from services.kube_agent.investigation.checks.diagnostic_check_models import CheckResult
from services.kube_agent.investigation.evidence.evidence_models import EvidenceBundle
from services.kube_agent.investigation.triggers.trigger_models import Trigger


@dataclass(frozen=True)
class IncidentCase:
    case_id: str
    title: str
    summary: str
    trigger: Trigger
    evidence: EvidenceBundle
    check_results: list[CheckResult]
    likely_causes: list[str] = field(default_factory=list)
    hypotheses: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    related_resources: list[str] = field(default_factory=list)
    dashboard_links: dict[str, str] = field(default_factory=dict)


if __name__ == "__main__":
    print("IncidentCase model loaded.")
