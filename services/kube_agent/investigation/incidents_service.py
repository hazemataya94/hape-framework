from core.errors import HapeError, HapeExternalError, HapeValidationError
from core.logging import LocalLogging
from services.kube_agent.investigation.memory.incident_memory_service import IncidentMemoryService
from services.kube_agent.investigation.memory.models import StoredIncident


class IncidentsService:
    DEFAULT_INCIDENT_MEMORY_SERVICE: IncidentMemoryService | None = None

    def __init__(self, incident_memory_service: IncidentMemoryService | None = DEFAULT_INCIDENT_MEMORY_SERVICE) -> None:
        self.incident_memory_service = incident_memory_service or IncidentMemoryService()
        self.logger = LocalLogging.get_logger("hape.incidents_service")

    def _validate_incident_id(self, incident_id: str) -> None:
        if not incident_id.strip():
            raise HapeValidationError(
                code="KUBE_AGENT_INCIDENT_ID_REQUIRED",
                message="incident_id is required.",
                context={"service": "IncidentsService"},
            )

    def list_incidents(self) -> list[StoredIncident]:
        self.logger.debug("list_incidents()")
        try:
            return self.incident_memory_service.list_incidents()
        except HapeError:
            raise
        except Exception as exc:
            raise HapeExternalError(
                code="KUBE_AGENT_INCIDENTS_LIST_FAILED",
                message="Failed to list kube-agent incidents.",
                context={"service": "IncidentsService"},
            ) from exc

    def get_incident(self, incident_id: str) -> StoredIncident | None:
        self.logger.debug("get_incident(incident_id: <str>)")
        self._validate_incident_id(incident_id=incident_id)
        try:
            return self.incident_memory_service.get_incident(incident_id=incident_id)
        except HapeError:
            raise
        except Exception as exc:
            raise HapeExternalError(
                code="KUBE_AGENT_INCIDENTS_GET_FAILED",
                message="Failed to fetch kube-agent incident.",
                context={"service": "IncidentsService", "incident_id": incident_id},
            ) from exc


if __name__ == "__main__":
    incidents_service = IncidentsService()
    print(incidents_service.__class__.__name__)
