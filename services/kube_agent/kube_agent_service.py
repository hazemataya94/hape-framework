from typing import Any

from services.kube_agent.investigation.findings.findings_models import Findings
from services.kube_agent.investigation.incidents_service import IncidentsService
from services.kube_agent.investigation.investigation_service import InvestigationService
from services.kube_agent.investigation.memory.models import StoredIncident


class KubeAgentService:
    DEFAULT_INVESTIGATION_SERVICE: InvestigationService | None = None
    DEFAULT_INCIDENTS_SERVICE: IncidentsService | None = None

    def __init__(self, investigation_service: InvestigationService | None = DEFAULT_INVESTIGATION_SERVICE, incidents_service: IncidentsService | None = DEFAULT_INCIDENTS_SERVICE) -> None:
        self.investigation_service = investigation_service or InvestigationService()
        self.incidents_service = incidents_service or IncidentsService(
            incident_memory_service=self.investigation_service.runtime.incident_memory_service
        )

    def investigate(self, raw_trigger: dict[str, Any], use_ai: bool | None = None) -> Findings:
        return self.investigation_service.investigate(raw_trigger=raw_trigger, use_ai=use_ai)

    def list_incidents(self) -> list[StoredIncident]:
        return self.incidents_service.list_incidents()

    def get_incident(self, incident_id: str) -> StoredIncident | None:
        return self.incidents_service.get_incident(incident_id=incident_id)


if __name__ == "__main__":
    print(KubeAgentService())
