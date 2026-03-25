from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StoredIncident:
    incident_id: str
    fingerprint: str
    first_seen: datetime
    last_seen: datetime
    occurrence_count: int
    latest_summary: str
    latest_likely_cause: str | None
    latest_findings_hash: str


@dataclass(frozen=True)
class InvestigationRun:
    run_id: str
    incident_id: str
    trigger_summary: str
    evidence_hash: str
    case_hash: str
    ai_used: bool
    created_at: datetime


if __name__ == "__main__":
    print(StoredIncident)
