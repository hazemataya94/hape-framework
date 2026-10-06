from __future__ import annotations

import json
import os
import sqlite3

from database.github_provider_migrations import apply_github_provider_migrations
from services.github_provider.errors import GitHubV2Error
from services.github_provider.models import ManagedDestination, ManagedRepository, ProviderOperation, ProviderReceipt


class SqliteGitHubProviderRepository:
    def __init__(self, sqlite_path: str) -> None:
        self.sqlite_path = os.path.expanduser(sqlite_path)
        directory = os.path.dirname(self.sqlite_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._connection = sqlite3.connect(self.sqlite_path, check_same_thread=False, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        apply_github_provider_migrations(self._connection)

    def _destination_from_row(self, row: sqlite3.Row) -> ManagedDestination:
        return ManagedDestination(
            destination_id=row["destination_id"],
            mode=row["mode"],
            tenant_subject=row["tenant_subject"],
            registration_id=row["registration_id"],
            installation_id=int(row["installation_id"]),
            account_id=int(row["account_id"]),
            account_login=row["account_login"],
            account_type=row["account_type"],
            repository_selection=row["repository_selection"],
            configuration_revision=row["configuration_revision"],
            permission_fingerprint=row["permission_fingerprint"],
            status=row["status"],
            verified_at=row["verified_at"],
            last_observed_at=row["last_observed_at"],
        )

    def _repository_from_row(self, row: sqlite3.Row) -> ManagedRepository:
        return ManagedRepository(
            repository_id=row["repository_id"],
            destination_id=row["destination_id"],
            ownership_mode=row["ownership_mode"],
            tenant_subject=row["tenant_subject"],
            provider_repository_id=row["provider_repository_id"],
            repository_name=row["repository_name"],
            owner_account_id=int(row["owner_account_id"]),
            owner_login=row["owner_login"],
            visibility=row["visibility"],
            default_branch=row["default_branch"],
            source_snapshot_digest=row["source_snapshot_digest"],
            baseline_sha=row["baseline_sha"],
            result_sha=row["result_sha"],
            status=row["status"],
        )

    def _operation_from_row(self, row: sqlite3.Row) -> ProviderOperation:
        return ProviderOperation(
            operation_id=row["operation_id"],
            subject_id=row["subject_id"],
            tenant_subject=row["tenant_subject"],
            operation=row["operation"],
            idempotency_key=row["idempotency_key"],
            canonical_request_hash=row["canonical_request_hash"],
            grant_jti=row["grant_jti"],
            target_binding_id=row["target_binding_id"],
            repository_id=row["repository_id"],
            state=row["state"],
            attempt_count=int(row["attempt_count"]),
            provider_marker=row["provider_marker"],
            last_error_code=row["last_error_code"],
            retry_class=row["retry_class"],
            reserved_at=row["reserved_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            reconciled_at=row["reconciled_at"],
        )

    def _receipt_from_row(self, row: sqlite3.Row) -> ProviderReceipt:
        return ProviderReceipt(
            receipt_id=row["receipt_id"],
            envelope_version=row["envelope_version"],
            operation_id=row["operation_id"],
            operation=row["operation"],
            subject_id=row["subject_id"],
            target_binding_id=row["target_binding_id"],
            repository_id=row["repository_id"],
            input_digest=row["input_digest"],
            output_digest=row["output_digest"],
            status=row["status"],
            issued_at=row["issued_at"],
            completed_at=row["completed_at"],
            safe_provider_ids=json.loads(row["safe_provider_ids"]),
            retry_class=row["retry_class"],
            customer_safe_error_code=row["customer_safe_error_code"],
        )

    def get_destination(self, destination_id: str) -> ManagedDestination | None:
        row = self._connection.execute("SELECT * FROM destinations WHERE destination_id = ?", (destination_id,)).fetchone()
        return self._destination_from_row(row) if row else None

    def get_hape_destination(self) -> ManagedDestination | None:
        row = self._connection.execute("SELECT * FROM destinations WHERE mode = 'hape_organization' AND status = 'active'").fetchone()
        return self._destination_from_row(row) if row else None

    def find_destination_by_installation(self, installation_id: int) -> ManagedDestination | None:
        row = self._connection.execute(
            "SELECT * FROM destinations WHERE installation_id = ? AND status = 'active'",
            (installation_id,),
        ).fetchone()
        return self._destination_from_row(row) if row else None

    def find_customer_destination(self, tenant_subject: str, installation_id: int) -> ManagedDestination | None:
        row = self._connection.execute(
            "SELECT * FROM destinations WHERE tenant_subject = ? AND installation_id = ?",
            (tenant_subject, installation_id),
        ).fetchone()
        return self._destination_from_row(row) if row else None

    def upsert_destination(self, destination: ManagedDestination) -> None:
        self._connection.execute(
            """
            INSERT INTO destinations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(destination_id) DO UPDATE SET
                status=excluded.status,
                last_observed_at=excluded.last_observed_at,
                permission_fingerprint=excluded.permission_fingerprint
            """,
            (
                destination.destination_id,
                destination.mode,
                destination.tenant_subject,
                destination.registration_id,
                destination.installation_id,
                destination.account_id,
                destination.account_login,
                destination.account_type,
                destination.repository_selection,
                destination.configuration_revision,
                destination.permission_fingerprint,
                destination.status,
                destination.verified_at,
                destination.last_observed_at,
            ),
        )

    def get_repository(self, repository_id: str) -> ManagedRepository | None:
        row = self._connection.execute("SELECT * FROM repositories WHERE repository_id = ?", (repository_id,)).fetchone()
        return self._repository_from_row(row) if row else None

    def find_repository_by_name(self, repository_name: str) -> ManagedRepository | None:
        row = self._connection.execute("SELECT * FROM repositories WHERE repository_name = ?", (repository_name,)).fetchone()
        return self._repository_from_row(row) if row else None

    def upsert_repository(self, repository: ManagedRepository) -> None:
        self._connection.execute(
            """
            INSERT INTO repositories VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(repository_id) DO UPDATE SET
                provider_repository_id=excluded.provider_repository_id,
                baseline_sha=excluded.baseline_sha,
                result_sha=excluded.result_sha,
                status=excluded.status
            """,
            (
                repository.repository_id,
                repository.destination_id,
                repository.ownership_mode,
                repository.tenant_subject,
                repository.provider_repository_id,
                repository.repository_name,
                repository.owner_account_id,
                repository.owner_login,
                repository.visibility,
                repository.default_branch,
                repository.source_snapshot_digest,
                repository.baseline_sha,
                repository.result_sha,
                repository.status,
            ),
        )

    def get_operation(self, operation_id: str) -> ProviderOperation | None:
        row = self._connection.execute("SELECT * FROM operations WHERE operation_id = ?", (operation_id,)).fetchone()
        return self._operation_from_row(row) if row else None

    def find_operation(self, tenant_subject: str, operation: str, idempotency_key: str) -> ProviderOperation | None:
        row = self._connection.execute(
            "SELECT * FROM operations WHERE tenant_subject = ? AND operation = ? AND idempotency_key = ?",
            (tenant_subject, operation, idempotency_key),
        ).fetchone()
        return self._operation_from_row(row) if row else None

    def upsert_operation(self, operation: ProviderOperation) -> None:
        self._connection.execute(
            """
            INSERT INTO operations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(operation_id) DO UPDATE SET
                state=excluded.state,
                attempt_count=excluded.attempt_count,
                provider_marker=excluded.provider_marker,
                last_error_code=excluded.last_error_code,
                retry_class=excluded.retry_class,
                started_at=excluded.started_at,
                completed_at=excluded.completed_at,
                reconciled_at=excluded.reconciled_at,
                repository_id=excluded.repository_id
            """,
            (
                operation.operation_id,
                operation.subject_id,
                operation.tenant_subject,
                operation.operation,
                operation.idempotency_key,
                operation.canonical_request_hash,
                operation.grant_jti,
                operation.target_binding_id,
                operation.repository_id,
                operation.state,
                operation.attempt_count,
                operation.provider_marker,
                operation.last_error_code,
                operation.retry_class,
                operation.reserved_at,
                operation.started_at,
                operation.completed_at,
                operation.reconciled_at,
            ),
        )

    def grant_consumed(self, jti: str) -> bool:
        row = self._connection.execute("SELECT jti FROM used_grants WHERE jti = ?", (jti,)).fetchone()
        return row is not None

    def consume_grant(self, jti: str, issuer: str, grant_sub: str, operation: str, input_digest: str, expires_at: str, consumed_at: str) -> None:
        if self.grant_consumed(jti):
            raise GitHubV2Error("grant_replayed")
        self._connection.execute(
            "INSERT INTO used_grants VALUES (?, ?, ?, ?, ?, ?, ?)",
            (jti, issuer, grant_sub, operation, input_digest, expires_at, consumed_at),
        )

    def append_receipt(self, receipt: ProviderReceipt) -> None:
        self._connection.execute(
            "INSERT INTO receipts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                receipt.receipt_id,
                receipt.envelope_version,
                receipt.operation_id,
                receipt.operation,
                receipt.subject_id,
                receipt.target_binding_id,
                receipt.repository_id,
                receipt.input_digest,
                receipt.output_digest,
                receipt.status,
                receipt.issued_at,
                receipt.completed_at,
                json.dumps(receipt.safe_provider_ids, sort_keys=True),
                receipt.retry_class,
                receipt.customer_safe_error_code,
            ),
        )

    def get_receipt(self, receipt_id: str) -> ProviderReceipt | None:
        row = self._connection.execute("SELECT * FROM receipts WHERE receipt_id = ?", (receipt_id,)).fetchone()
        return self._receipt_from_row(row) if row else None

    def get_latest_receipt(self, operation_id: str) -> ProviderReceipt | None:
        row = self._connection.execute(
            "SELECT * FROM receipts WHERE operation_id = ? ORDER BY issued_at DESC LIMIT 1",
            (operation_id,),
        ).fetchone()
        return self._receipt_from_row(row) if row else None

    def put_setup_state(self, state: str, tenant_subject: str, code_challenge: str, expires_at: str) -> None:
        self._connection.execute("INSERT INTO setup_states VALUES (?, ?, ?, ?, NULL)", (state, tenant_subject, code_challenge, expires_at))

    def consume_setup_state(self, state: str, tenant_subject: str, now: str) -> str | None:
        row = self._connection.execute("SELECT * FROM setup_states WHERE state = ? AND tenant_subject = ?", (state, tenant_subject)).fetchone()
        if row is None:
            return None
        if row["consumed_at"] is not None or row["expires_at"] < now:
            return None
        self._connection.execute("UPDATE setup_states SET consumed_at = ? WHERE state = ?", (now, state))
        return str(row["code_challenge"])

    def reserve_name(self, repository_name: str) -> bool:
        existing = self.find_repository_by_name(repository_name)
        return existing is None

    def begin(self) -> None:
        self._connection.execute("BEGIN IMMEDIATE")

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()


if __name__ == "__main__":
    repository = SqliteGitHubProviderRepository(":memory:")
    print(repository.get_hape_destination())
