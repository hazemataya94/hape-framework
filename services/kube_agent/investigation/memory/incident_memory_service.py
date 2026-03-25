from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta

from services.kube_agent.investigation.case.incident_case_models import IncidentCase
from services.kube_agent.investigation.findings.findings_models import Findings
from services.kube_agent.investigation.memory.incident_fingerprint import IncidentFingerprint
from services.kube_agent.investigation.memory.incident_repository import IncidentRepository
from services.kube_agent.investigation.memory.models import InvestigationRun, StoredIncident
from services.kube_agent.investigation.memory.sqlite.sqlite_incident_repository import SqliteIncidentRepository
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class IncidentMemoryService:
    def __init__(self, repository: IncidentRepository | None = None, sqlite_path: str = "~/.hape/kube-agent.sqlite", ai_stale_after_hours: int = 6) -> None:
        self.repository = repository or SqliteIncidentRepository(sqlite_path=sqlite_path)
        self.ai_stale_after_hours = ai_stale_after_hours

    @staticmethod
    def _normalize_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @staticmethod
    def _hash_payload(value: object) -> str:
        return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()

    @staticmethod
    def _build_trigger_summary(trigger: Trigger) -> str:
        if trigger.namespace:
            return f"{trigger.type}:{trigger.cluster}:{trigger.namespace}:{trigger.name}"
        return f"{trigger.type}:{trigger.cluster}:{trigger.name}"

    def find_existing(self, trigger: Trigger, incident_case: IncidentCase | None = None) -> StoredIncident | None:
        fingerprint = IncidentFingerprint.build(trigger=trigger, incident_case=incident_case)
        return self.repository.find_incident_by_fingerprint(fingerprint=fingerprint)

    def should_run_ai(self, trigger: Trigger, incident_case: IncidentCase, previous_incident: StoredIncident | None) -> bool:
        if not previous_incident:
            return True
        current_fingerprint = IncidentFingerprint.build(trigger=trigger, incident_case=incident_case)
        if current_fingerprint != previous_incident.fingerprint:
            return True
        now = datetime.now(UTC)
        last_seen = self._normalize_utc(previous_incident.last_seen)
        return (now - last_seen) > timedelta(hours=self.ai_stale_after_hours)

    def save(self, trigger: Trigger, incident_case: IncidentCase, findings: Findings) -> None:
        now = datetime.now(UTC)
        fingerprint = IncidentFingerprint.build(trigger=trigger, incident_case=incident_case)
        findings_hash = self._hash_payload(value=findings.__dict__)
        existing_incident = self.repository.find_incident_by_fingerprint(fingerprint=fingerprint)
        if existing_incident:
            stored_incident = StoredIncident(
                incident_id=existing_incident.incident_id,
                fingerprint=fingerprint,
                first_seen=existing_incident.first_seen,
                last_seen=now,
                occurrence_count=existing_incident.occurrence_count + 1,
                latest_summary=findings.summary,
                latest_likely_cause=findings.likely_root_cause,
                latest_findings_hash=findings_hash,
            )
        else:
            stored_incident = StoredIncident(
                incident_id=str(uuid.uuid4()),
                fingerprint=fingerprint,
                first_seen=now,
                last_seen=now,
                occurrence_count=1,
                latest_summary=findings.summary,
                latest_likely_cause=findings.likely_root_cause,
                latest_findings_hash=findings_hash,
            )
        self.repository.upsert_incident(incident=stored_incident)
        investigation_run = InvestigationRun(
            run_id=str(uuid.uuid4()),
            incident_id=stored_incident.incident_id,
            trigger_summary=self._build_trigger_summary(trigger=trigger),
            evidence_hash=self._hash_payload(value=incident_case.evidence.links),
            case_hash=self._hash_payload(value=incident_case.summary),
            ai_used=findings.ai_used,
            created_at=now,
        )
        self.repository.save_investigation_run(run=investigation_run)

    def list_incidents(self) -> list[StoredIncident]:
        return self.repository.list_incidents()

    def get_incident(self, incident_id: str) -> StoredIncident | None:
        return self.repository.get_incident_by_id(incident_id=incident_id)


if __name__ == "__main__":
    print(IncidentMemoryService)
