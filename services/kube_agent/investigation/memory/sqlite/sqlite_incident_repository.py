import os
import sqlite3
from datetime import datetime

from services.kube_agent.investigation.memory.incident_repository import IncidentRepository
from services.kube_agent.investigation.memory.models import InvestigationRun, StoredIncident
from services.kube_agent.investigation.memory.sqlite.migrations import apply_migrations


class SqliteIncidentRepository(IncidentRepository):
    def __init__(self, sqlite_path: str) -> None:
        self.sqlite_path = os.path.expanduser(sqlite_path)
        os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)
        with self._connect() as connection:
            apply_migrations(connection=connection)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.sqlite_path)

    @staticmethod
    def _row_to_stored_incident(row: tuple) -> StoredIncident:
        return StoredIncident(
            incident_id=row[0],
            fingerprint=row[1],
            first_seen=datetime.fromisoformat(row[2]),
            last_seen=datetime.fromisoformat(row[3]),
            occurrence_count=int(row[4]),
            latest_summary=row[5],
            latest_likely_cause=row[6],
            latest_findings_hash=row[7],
        )

    def get_incident_by_id(self, incident_id: str) -> StoredIncident | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT incident_id, fingerprint, first_seen, last_seen, occurrence_count, latest_summary, latest_likely_cause, latest_findings_hash FROM incidents WHERE incident_id = ?",
                (incident_id,),
            ).fetchone()
        if not row:
            return None
        return self._row_to_stored_incident(row=row)

    def find_incident_by_fingerprint(self, fingerprint: str) -> StoredIncident | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT incident_id, fingerprint, first_seen, last_seen, occurrence_count, latest_summary, latest_likely_cause, latest_findings_hash FROM incidents WHERE fingerprint = ?",
                (fingerprint,),
            ).fetchone()
        if not row:
            return None
        return self._row_to_stored_incident(row=row)

    def list_incidents(self) -> list[StoredIncident]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT incident_id, fingerprint, first_seen, last_seen, occurrence_count, latest_summary, latest_likely_cause, latest_findings_hash FROM incidents ORDER BY last_seen DESC"
            ).fetchall()
        return [self._row_to_stored_incident(row=row) for row in rows]

    def upsert_incident(self, incident: StoredIncident) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO incidents (incident_id, fingerprint, first_seen, last_seen, occurrence_count, latest_summary, latest_likely_cause, latest_findings_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(incident_id) DO UPDATE SET
                    fingerprint=excluded.fingerprint,
                    first_seen=excluded.first_seen,
                    last_seen=excluded.last_seen,
                    occurrence_count=excluded.occurrence_count,
                    latest_summary=excluded.latest_summary,
                    latest_likely_cause=excluded.latest_likely_cause,
                    latest_findings_hash=excluded.latest_findings_hash
                """,
                (
                    incident.incident_id,
                    incident.fingerprint,
                    incident.first_seen.isoformat(),
                    incident.last_seen.isoformat(),
                    incident.occurrence_count,
                    incident.latest_summary,
                    incident.latest_likely_cause,
                    incident.latest_findings_hash,
                ),
            )
            connection.commit()

    def save_investigation_run(self, run: InvestigationRun) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO investigation_runs (run_id, incident_id, trigger_summary, evidence_hash, case_hash, ai_used, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.incident_id,
                    run.trigger_summary,
                    run.evidence_hash,
                    run.case_hash,
                    int(run.ai_used),
                    run.created_at.isoformat(),
                ),
            )
            connection.commit()


if __name__ == "__main__":
    print(SqliteIncidentRepository)
