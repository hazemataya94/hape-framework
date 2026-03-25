from abc import ABC, abstractmethod

from services.kube_agent.investigation.memory.models import InvestigationRun, StoredIncident


class IncidentRepository(ABC):
    @abstractmethod
    def get_incident_by_id(self, incident_id: str) -> StoredIncident | None:
        raise NotImplementedError

    @abstractmethod
    def find_incident_by_fingerprint(self, fingerprint: str) -> StoredIncident | None:
        raise NotImplementedError

    @abstractmethod
    def list_incidents(self) -> list[StoredIncident]:
        raise NotImplementedError

    @abstractmethod
    def upsert_incident(self, incident: StoredIncident) -> None:
        raise NotImplementedError

    @abstractmethod
    def save_investigation_run(self, run: InvestigationRun) -> None:
        raise NotImplementedError


if __name__ == "__main__":
    print(IncidentRepository)
