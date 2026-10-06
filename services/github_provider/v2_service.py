from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from core.config import Config
from repositories.sqlite_github_provider_repository import SqliteGitHubProviderRepository
from services.github_provider.canonical import request_digest, sha256_hex
from services.github_provider.destination_service import DestinationService
from services.github_provider.errors import GitHubV2Error
from services.github_provider.fixture_provider import FixtureGitHubProvider
from services.github_provider.grant_verifier import GrantVerifier
from services.github_provider.models import FORBIDDEN_CAMEL_ALIASES, FORBIDDEN_PRODUCT_KEYS, ManagedRepository, ProviderOperation, VerificationKey, collect_forbidden_keys
from services.github_provider.publication_service import PublicationService
from services.github_provider.receipt_service import ReceiptService
from services.github_provider.reconciliation_service import ReconciliationService


class GitHubV2Service:
    def __init__(self, repository: SqliteGitHubProviderRepository, provider: FixtureGitHubProvider, verifier: GrantVerifier) -> None:
        self._repository = repository
        self._provider = provider
        self._verifier = verifier
        self._destinations = DestinationService(repository, provider)
        self._publication = PublicationService(repository, provider)
        self._receipts = ReceiptService()
        self._reconciliation = ReconciliationService(repository, provider)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _reject_forbidden(self, payload: dict[str, Any]) -> None:
        if collect_forbidden_keys(payload):
            raise GitHubV2Error("policy_denied")
        for key in payload:
            if key in FORBIDDEN_PRODUCT_KEYS or key in FORBIDDEN_CAMEL_ALIASES:
                raise GitHubV2Error("policy_denied")

    def _manifest(self, files: list[dict[str, Any]]) -> list[dict[str, Any]]:
        items = []
        for item in files:
            content = item.get("bytes")
            if content is None and item.get("hex_bytes"):
                content = bytes.fromhex(str(item["hex_bytes"]))
            elif isinstance(content, str):
                content = content.encode("utf-8")
            if isinstance(content, (bytes, bytearray)):
                digest = sha256_hex(bytes(content))
                size = len(content)
            else:
                digest = str(item.get("digest") or "")
                size = int(item.get("size") or 0)
            items.append({"digest": digest, "mode": str(item.get("mode") or "100644"), "path": str(item.get("path") or ""), "size": size})
        return sorted(items, key=lambda item: item["path"])

    def _digest_payload(self, request: dict[str, Any]) -> dict[str, Any]:
        payload = {key: value for key, value in request.items() if key != "authorization_grant" and value not in (None, "", [], {})}
        if "files" in payload:
            payload["files"] = self._manifest(list(payload["files"]))
        return payload

    def _request_digest(self, request: dict[str, Any]) -> str:
        return request_digest(self._digest_payload(request))

    def _verify(self, operation: str, request: dict[str, Any]) -> dict[str, Any]:
        self._reject_forbidden(request)
        grant = self._verifier.verify(str(request.get("authorization_grant") or ""), operation)
        request_operation_id = str(request.get("operation_id") or "")
        if request_operation_id and request_operation_id != str(grant.get("operation_id") or ""):
            raise GitHubV2Error("policy_denied")
        digest = self._request_digest(request)
        if str(grant.get("input_digest") or "") != digest:
            raise GitHubV2Error("digest_mismatch")
        constraints = grant.get("resource_constraints") or {}
        for key, value in constraints.items():
            if key not in request:
                continue
            if request.get(key) != value:
                raise GitHubV2Error("target_mismatch")
        return grant

    def _reserve(self, grant: dict[str, Any], request: dict[str, Any], operation: str) -> tuple[ProviderOperation, Any]:
        tenant = str(grant["tenant_id"])
        key = str(request.get("idempotency_key") or "")
        if not key:
            raise GitHubV2Error("invalid_resource_constraints")
        digest = str(grant["input_digest"])
        existing = self._repository.find_operation(tenant, operation, key)
        prior = self._repository.get_operation(str(grant["operation_id"]))
        if existing is not None:
            if existing.canonical_request_hash != digest:
                raise GitHubV2Error("conflict")
            receipt = self._repository.get_latest_receipt(existing.operation_id)
            if receipt is None:
                raise GitHubV2Error("reconciliation_required")
            return existing, receipt
        if prior is not None:
            raise GitHubV2Error("conflict")
        consumed_at = self._now()
        self._repository.consume_grant(str(grant["jti"]), str(grant["iss"]), str(grant["sub"]), operation, digest, str(grant["exp"]), consumed_at)
        record = ProviderOperation(
            operation_id=str(grant["operation_id"]),
            subject_id=str(request.get("subject_id") or ""),
            tenant_subject=tenant,
            operation=operation,
            idempotency_key=key,
            canonical_request_hash=digest,
            grant_jti=str(grant["jti"]),
            target_binding_id=str(request.get("target_binding_id") or ""),
            repository_id=request.get("repository_id"),
            state="reserved",
            attempt_count=1,
            provider_marker="",
            last_error_code="",
            retry_class="none",
            reserved_at=consumed_at,
            started_at=consumed_at,
            completed_at=None,
            reconciled_at=None,
        )
        self._repository.upsert_operation(record)
        return record, None

    def _store_receipt(self, fields: dict[str, Any]) -> dict[str, Any]:
        receipt = self._receipts.build(fields)
        self._repository.append_receipt(receipt)
        return self._receipts.to_public(receipt)

    def _complete(self, operation: ProviderOperation, state: str, retry_class: str, error_code: str = "") -> None:
        operation.state = state
        operation.retry_class = retry_class
        operation.last_error_code = error_code
        operation.completed_at = self._now()
        if state == "reconciled":
            operation.reconciled_at = operation.completed_at
        self._repository.upsert_operation(operation)

    def _fail(self, operation: ProviderOperation, request: dict[str, Any], grant: dict[str, Any], error: GitHubV2Error) -> dict[str, Any]:
        retry = "reconcile_then_retry" if error.code == "operation_unknown" else "none"
        state = "unknown" if error.code == "operation_unknown" else "failed"
        self._complete(operation, state, retry, error.code)
        return self._store_receipt(
            {
                "operation_id": operation.operation_id,
                "operation": operation.operation,
                "subject_id": operation.subject_id,
                "target_binding_id": operation.target_binding_id,
                "repository_id": operation.repository_id,
                "input_digest": str(grant["input_digest"]),
                "output_digest": "",
                "status": state,
                "retry_class": retry,
                "customer_safe_error_code": error.code,
            }
        )

    def _success(self, operation: ProviderOperation, grant: dict[str, Any], output_digest: str, safe_ids: dict[str, Any]) -> dict[str, Any]:
        self._complete(operation, "succeeded", "idempotent_replay")
        return self._store_receipt(
            {
                "operation_id": operation.operation_id,
                "operation": operation.operation,
                "subject_id": operation.subject_id,
                "target_binding_id": operation.target_binding_id,
                "repository_id": operation.repository_id,
                "input_digest": str(grant["input_digest"]),
                "output_digest": output_digest,
                "status": "succeeded",
                "retry_class": "idempotent_replay",
                "safe_provider_ids": safe_ids,
            }
        )

    def _require(self, request: dict[str, Any], keys: tuple[str, ...]) -> None:
        missing = [key for key in keys if not request.get(key)]
        if missing:
            raise GitHubV2Error("invalid_resource_constraints")

    def _files(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        files = []
        for item in request.get("files") or []:
            raw = item.get("bytes")
            if raw is None and item.get("hex_bytes"):
                raw = bytes.fromhex(str(item["hex_bytes"]))
            elif isinstance(raw, str):
                raw = raw.encode("utf-8")
            files.append({"path": item.get("path"), "mode": item.get("mode") or "100644", "bytes": raw})
        return files

    def _tag_name(self, subject_id: str, operation_id: str) -> str:
        return "hape-tag-" + sha256_hex(f"{subject_id}:{operation_id}")[:16]

    def _destination_payload(self, destination_id: str) -> dict[str, Any]:
        return self._destinations.status(destination_id)

    def destination_status(self, request: dict[str, Any]) -> dict[str, Any]:
        grant = self._verify("managed_destination.status", request)
        self._repository.begin()
        try:
            self._repository.consume_grant(str(grant["jti"]), str(grant["iss"]), str(grant["sub"]), "managed_destination.status", str(grant["input_digest"]), str(grant["exp"]), self._now())
            payload = self._destination_payload(str(request["destination_id"]))
            self._repository.commit()
            return payload
        except Exception:
            self._repository.rollback()
            raise

    def target_setup_url(self, request: dict[str, Any]) -> dict[str, Any]:
        grant = self._verify("managed_target.setup_url", request)
        self._repository.begin()
        try:
            operation, replayed = self._reserve(grant, request, "managed_target.setup_url")
            if replayed is not None:
                self._repository.commit()
                return self._receipts.to_public(replayed)
            payload = self._destinations.setup_url(str(grant["tenant_id"]), str(request.get("code_verifier") or ""))
            receipt = self._success(operation, grant, str(grant["input_digest"]), {"setup_state": payload["setup_state"]})
            receipt["setup_url"] = payload["setup_url"]
            receipt["setup_state"] = payload["setup_state"]
            self._repository.commit()
            return receipt
        except GitHubV2Error:
            self._repository.rollback()
            raise
        except Exception:
            self._repository.rollback()
            raise

    def target_verify(self, request: dict[str, Any]) -> dict[str, Any]:
        grant = self._verify("managed_target.verify", request)
        self._repository.begin()
        try:
            operation, replayed = self._reserve(grant, request, "managed_target.verify")
            if replayed is not None:
                self._repository.commit()
                return self._receipts.to_public(replayed)
            destination = self._destinations.verify(str(grant["tenant_id"]), request)
            operation.target_binding_id = destination.destination_id
            receipt = self._success(operation, grant, destination.destination_id, {"destination_id": destination.destination_id, "mode": destination.mode})
            self._repository.commit()
            return receipt
        except GitHubV2Error:
            self._repository.rollback()
            raise

    def target_status(self, request: dict[str, Any]) -> dict[str, Any]:
        grant = self._verify("managed_target.status", request)
        destination = self._destinations.resolve(str(grant["tenant_id"]), str(request.get("destination_mode") or ""), str(request["target_binding_id"]))
        return self._destination_payload(destination.destination_id)

    def create_private(self, request: dict[str, Any]) -> dict[str, Any]:
        grant = self._verify("managed_repository.create_private", request)
        self._require(request, ("subject_id", "operation_id", "destination_mode", "source_snapshot_digest", "idempotency_key"))
        files = self._files(request)
        admitted, digest = self._publication.admit_files(files) if files else ([], str(request["source_snapshot_digest"]))
        if files and digest != str(request["source_snapshot_digest"]):
            raise GitHubV2Error("digest_mismatch")
        operation = None
        replayed = None
        self._repository.begin()
        try:
            operation, replayed = self._reserve(grant, request, "managed_repository.create_private")
            if replayed is not None:
                self._repository.commit()
                return self._receipts.to_public(replayed)
            destination = self._destinations.resolve(str(grant["tenant_id"]), str(request["destination_mode"]), request.get("target_binding_id"))
            operation.target_binding_id = destination.destination_id
            name = self._publication.generate_name()
            operation.provider_marker = name
            created = self._publication.create_repository(destination, name, str((grant.get("resource_constraints") or {}).get("collaborator_login") or ""))
            repository_id = str(uuid.uuid4())
            managed = ManagedRepository(
                repository_id=repository_id,
                destination_id=destination.destination_id,
                ownership_mode=destination.mode,
                tenant_subject=str(grant["tenant_id"]),
                provider_repository_id=int(created["provider_repository_id"]),
                repository_name=name,
                owner_account_id=destination.account_id,
                owner_login=destination.account_login,
                visibility="private",
                default_branch="main",
                source_snapshot_digest=str(request["source_snapshot_digest"]),
                baseline_sha=None,
                result_sha=None,
                status="created",
            )
            self._repository.upsert_repository(managed)
            if files:
                self._publication.store_snapshot(str(grant["tenant_id"]), digest, admitted)
            operation.repository_id = repository_id
            receipt = self._success(operation, grant, digest, {"repository_id": repository_id, "repository_name": name})
            self._repository.commit()
            return receipt
        except GitHubV2Error as error:
            if operation is not None and replayed is None:
                receipt = self._fail(operation, request, grant, error)
                self._repository.commit()
                if error.code == "operation_unknown":
                    return receipt
                raise
            self._repository.rollback()
            raise

    def publish_baseline(self, request: dict[str, Any]) -> dict[str, Any]:
        grant = self._verify("managed_repository.publish_baseline", request)
        self._require(request, ("subject_id", "operation_id", "repository_id", "idempotency_key"))
        operation = None
        replayed = None
        self._repository.begin()
        try:
            operation, replayed = self._reserve(grant, request, "managed_repository.publish_baseline")
            if replayed is not None:
                self._repository.commit()
                return self._receipts.to_public(replayed)
            managed = self._repository.get_repository(str(request["repository_id"]))
            if managed is None or managed.tenant_subject != grant["tenant_id"]:
                raise GitHubV2Error("repository_not_found")
            files = self._files(request)
            if files:
                admitted, digest = self._publication.admit_files(files)
                self._publication.store_snapshot(str(grant["tenant_id"]), digest, admitted)
            else:
                admitted = self._publication.load_snapshot(str(grant["tenant_id"]), managed.source_snapshot_digest)
                digest = managed.source_snapshot_digest
            if digest != managed.source_snapshot_digest:
                raise GitHubV2Error("digest_mismatch")
            sha = self._publication.publish_commit(managed, digest, f"baseline:{operation.operation_id}", None)
            managed.baseline_sha = sha
            managed.status = "baselined"
            self._repository.upsert_repository(managed)
            operation.repository_id = managed.repository_id
            operation.provider_marker = sha
            operation.target_binding_id = managed.destination_id
            receipt = self._success(operation, grant, digest, {"commit_sha": sha})
            self._repository.commit()
            return receipt
        except GitHubV2Error as error:
            if operation is not None and replayed is None:
                receipt = self._fail(operation, request, grant, error)
                self._repository.commit()
                if error.code == "operation_unknown":
                    return receipt
                raise
            self._repository.rollback()
            raise

    def publish_artifact(self, request: dict[str, Any]) -> dict[str, Any]:
        grant = self._verify("managed_repository.publish_artifact", request)
        self._require(request, ("subject_id", "operation_id", "repository_id", "artifact_digest", "expected_parent", "idempotency_key"))
        operation = None
        replayed = None
        self._repository.begin()
        try:
            operation, replayed = self._reserve(grant, request, "managed_repository.publish_artifact")
            if replayed is not None:
                self._repository.commit()
                return self._receipts.to_public(replayed)
            managed = self._repository.get_repository(str(request["repository_id"]))
            if managed is None or managed.tenant_subject != grant["tenant_id"]:
                raise GitHubV2Error("repository_not_found")
            admitted, digest = self._publication.admit_files(self._files(request))
            if digest != str(request["artifact_digest"]):
                raise GitHubV2Error("digest_mismatch")
            current = self._publication.current_parent(managed)
            if current != str(request["expected_parent"]):
                raise GitHubV2Error("parent_mismatch")
            sha = self._publication.publish_commit(managed, digest, f"artifact:{operation.operation_id}", current)
            managed.result_sha = sha
            managed.status = "published"
            self._repository.upsert_repository(managed)
            operation.repository_id = managed.repository_id
            operation.provider_marker = sha
            operation.target_binding_id = managed.destination_id
            receipt = self._success(operation, grant, digest, {"commit_sha": sha})
            self._repository.commit()
            return receipt
        except GitHubV2Error as error:
            if operation is not None and replayed is None:
                receipt = self._fail(operation, request, grant, error)
                self._repository.commit()
                if error.code == "operation_unknown":
                    return receipt
                raise
            self._repository.rollback()
            raise

    def publish_tag(self, request: dict[str, Any]) -> dict[str, Any]:
        grant = self._verify("managed_repository.publish_tag", request)
        self._require(request, ("subject_id", "operation_id", "repository_id", "idempotency_key"))
        operation = None
        replayed = None
        self._repository.begin()
        try:
            operation, replayed = self._reserve(grant, request, "managed_repository.publish_tag")
            if replayed is not None:
                self._repository.commit()
                return self._receipts.to_public(replayed)
            managed = self._repository.get_repository(str(request["repository_id"]))
            if managed is None or managed.tenant_subject != grant["tenant_id"]:
                raise GitHubV2Error("repository_not_found")
            sha = managed.result_sha or managed.baseline_sha
            if not sha:
                raise GitHubV2Error("repository_not_found")
            tag_name = self._tag_name(str(request["subject_id"]), str(request["operation_id"]))
            self._publication.publish_tag(managed, tag_name, sha)
            operation.repository_id = managed.repository_id
            operation.provider_marker = tag_name
            operation.target_binding_id = managed.destination_id
            receipt = self._success(operation, grant, sha, {"tag": tag_name, "commit_sha": sha})
            self._repository.commit()
            return receipt
        except GitHubV2Error as error:
            if operation is not None and replayed is None:
                receipt = self._fail(operation, request, grant, error)
                self._repository.commit()
                if error.code == "operation_unknown":
                    return receipt
                raise
            self._repository.rollback()
            raise

    def dispose(self, request: dict[str, Any]) -> dict[str, Any]:
        grant = self._verify("managed_repository.dispose", request)
        self._require(request, ("subject_id", "operation_id", "repository_id", "idempotency_key"))
        operation = None
        replayed = None
        self._repository.begin()
        try:
            operation, replayed = self._reserve(grant, request, "managed_repository.dispose")
            if replayed is not None:
                self._repository.commit()
                return self._receipts.to_public(replayed)
            managed = self._repository.get_repository(str(request["repository_id"]))
            if managed is None or managed.tenant_subject != grant["tenant_id"]:
                raise GitHubV2Error("repository_not_found")
            managed.status = "disposal_requested"
            self._repository.upsert_repository(managed)
            self._publication.dispose(managed)
            managed.status = "disposed"
            self._repository.upsert_repository(managed)
            operation.repository_id = managed.repository_id
            operation.provider_marker = managed.repository_name
            operation.target_binding_id = managed.destination_id
            receipt = self._success(operation, grant, managed.source_snapshot_digest, {"repository_id": managed.repository_id})
            self._repository.commit()
            return receipt
        except GitHubV2Error as error:
            if operation is not None and replayed is None:
                receipt = self._fail(operation, request, grant, error)
                self._repository.commit()
                if error.code == "operation_unknown":
                    return receipt
                raise
            self._repository.rollback()
            raise

    def get_operation(self, request: dict[str, Any]) -> dict[str, Any]:
        grant = self._verify("provider_operation.get", request)
        record = self._repository.get_operation(str(request["operation_id"]))
        if record is None or record.tenant_subject != grant["tenant_id"]:
            raise GitHubV2Error("target_not_found")
        return {
            "operation_id": record.operation_id,
            "operation": record.operation,
            "subject_id": record.subject_id,
            "state": record.state,
            "retry_class": record.retry_class,
            "repository_id": record.repository_id,
            "target_binding_id": record.target_binding_id,
        }

    def get_receipt(self, request: dict[str, Any]) -> dict[str, Any]:
        grant = self._verify("provider_receipt.get", request)
        receipt = self._repository.get_receipt(str(request["receipt_id"]))
        if receipt is None:
            raise GitHubV2Error("target_not_found")
        operation = self._repository.get_operation(receipt.operation_id)
        if operation is None or operation.tenant_subject != grant["tenant_id"]:
            raise GitHubV2Error("target_not_found")
        return self._receipts.to_public(receipt)

    def reconcile(self, request: dict[str, Any]) -> dict[str, Any]:
        grant = self._verify("provider_operation.get", request)
        self._repository.begin()
        try:
            record = self._repository.get_operation(str(request["operation_id"]))
            if record is None or record.tenant_subject != grant["tenant_id"]:
                raise GitHubV2Error("target_not_found")
            if record.state != "unknown":
                receipt = self._repository.get_latest_receipt(record.operation_id)
                self._repository.commit()
                return self._receipts.to_public(receipt) if receipt else {"operation_id": record.operation_id, "state": record.state}
            managed = self._repository.get_repository(record.repository_id) if record.repository_id else None
            inspection = self._reconciliation.inspect(record, managed)
            if inspection["confirmed"]:
                record.state = "reconciled"
                record.retry_class = "idempotent_replay"
                record.reconciled_at = self._now()
                record.completed_at = record.reconciled_at
                self._repository.upsert_operation(record)
                receipt = self._store_receipt(
                    {
                        "operation_id": record.operation_id,
                        "operation": record.operation,
                        "subject_id": record.subject_id,
                        "target_binding_id": record.target_binding_id,
                        "repository_id": record.repository_id,
                        "input_digest": record.canonical_request_hash,
                        "output_digest": str(inspection.get("marker") or ""),
                        "status": "reconciled",
                        "retry_class": "idempotent_replay",
                    }
                )
                self._repository.commit()
                return receipt
            if inspection["absent"] and record.operation == "managed_repository.dispose":
                record.state = "reconciled"
                record.retry_class = "none"
                record.reconciled_at = self._now()
                self._repository.upsert_operation(record)
                receipt = self._store_receipt(
                    {
                        "operation_id": record.operation_id,
                        "operation": record.operation,
                        "subject_id": record.subject_id,
                        "target_binding_id": record.target_binding_id,
                        "repository_id": record.repository_id,
                        "input_digest": record.canonical_request_hash,
                        "status": "reconciled",
                        "retry_class": "none",
                    }
                )
                self._repository.commit()
                return receipt
            record.retry_class = "manual"
            self._repository.upsert_operation(record)
            self._repository.commit()
            raise GitHubV2Error("reconciliation_required")
        except GitHubV2Error:
            self._repository.rollback()
            raise


def create_github_v2_service(sqlite_path: str = "", keys: list[VerificationKey] | None = None, provider: FixtureGitHubProvider | None = None) -> GitHubV2Service:
    path = sqlite_path or Config.get_github_provider_sqlite_path()
    return GitHubV2Service(SqliteGitHubProviderRepository(path), provider or FixtureGitHubProvider(), GrantVerifier(keys or []))


if __name__ == "__main__":
    print(GitHubV2Service.__name__)
