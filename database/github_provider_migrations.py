from __future__ import annotations

import sqlite3


def apply_github_provider_migrations(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS destinations (
            destination_id TEXT PRIMARY KEY,
            mode TEXT NOT NULL,
            tenant_subject TEXT,
            registration_id TEXT NOT NULL,
            installation_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            account_login TEXT NOT NULL,
            account_type TEXT NOT NULL,
            repository_selection TEXT NOT NULL,
            configuration_revision TEXT NOT NULL,
            permission_fingerprint TEXT NOT NULL,
            status TEXT NOT NULL,
            verified_at TEXT NOT NULL,
            last_observed_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS repositories (
            repository_id TEXT PRIMARY KEY,
            destination_id TEXT NOT NULL,
            ownership_mode TEXT NOT NULL,
            tenant_subject TEXT NOT NULL,
            provider_repository_id INTEGER,
            repository_name TEXT NOT NULL UNIQUE,
            owner_account_id INTEGER NOT NULL,
            owner_login TEXT NOT NULL,
            visibility TEXT NOT NULL,
            default_branch TEXT NOT NULL,
            source_snapshot_digest TEXT NOT NULL,
            baseline_sha TEXT,
            result_sha TEXT,
            status TEXT NOT NULL,
            FOREIGN KEY(destination_id) REFERENCES destinations(destination_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS operations (
            operation_id TEXT PRIMARY KEY,
            subject_id TEXT NOT NULL,
            tenant_subject TEXT NOT NULL,
            operation TEXT NOT NULL,
            idempotency_key TEXT NOT NULL,
            canonical_request_hash TEXT NOT NULL,
            grant_jti TEXT NOT NULL,
            target_binding_id TEXT NOT NULL,
            repository_id TEXT,
            state TEXT NOT NULL,
            attempt_count INTEGER NOT NULL,
            provider_marker TEXT NOT NULL,
            last_error_code TEXT NOT NULL,
            retry_class TEXT NOT NULL,
            reserved_at TEXT NOT NULL,
            started_at TEXT,
            completed_at TEXT,
            reconciled_at TEXT,
            UNIQUE(tenant_subject, operation, idempotency_key)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS receipts (
            receipt_id TEXT PRIMARY KEY,
            envelope_version TEXT NOT NULL,
            operation_id TEXT NOT NULL,
            operation TEXT NOT NULL,
            subject_id TEXT NOT NULL,
            target_binding_id TEXT NOT NULL,
            repository_id TEXT,
            input_digest TEXT NOT NULL,
            output_digest TEXT NOT NULL,
            status TEXT NOT NULL,
            issued_at TEXT NOT NULL,
            completed_at TEXT,
            safe_provider_ids TEXT NOT NULL,
            retry_class TEXT NOT NULL,
            customer_safe_error_code TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS used_grants (
            jti TEXT PRIMARY KEY,
            issuer TEXT NOT NULL,
            grant_sub TEXT NOT NULL,
            operation TEXT NOT NULL,
            input_digest TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            consumed_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS setup_states (
            state TEXT PRIMARY KEY,
            tenant_subject TEXT NOT NULL,
            code_challenge TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            consumed_at TEXT
        )
        """
    )
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS destinations_hape_active ON destinations(mode) WHERE mode = 'hape_organization' AND status = 'active'")
    connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS destinations_customer_installation ON destinations(installation_id) WHERE mode != 'hape_organization' AND status = 'active'")
    connection.commit()


if __name__ == "__main__":
    connection = sqlite3.connect(":memory:")
    apply_github_provider_migrations(connection)
    print("ok")
