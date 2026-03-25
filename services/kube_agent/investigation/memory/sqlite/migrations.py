import sqlite3


def apply_migrations(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS incidents (
            incident_id TEXT PRIMARY KEY,
            fingerprint TEXT NOT NULL UNIQUE,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            latest_summary TEXT NOT NULL,
            latest_likely_cause TEXT NULL,
            latest_findings_hash TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS investigation_runs (
            run_id TEXT PRIMARY KEY,
            incident_id TEXT NOT NULL,
            trigger_summary TEXT NOT NULL,
            evidence_hash TEXT NOT NULL,
            case_hash TEXT NOT NULL,
            ai_used INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (incident_id) REFERENCES incidents (incident_id)
        )
        """
    )
    connection.commit()


if __name__ == "__main__":
    print(apply_migrations)
