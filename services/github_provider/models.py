from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


FORBIDDEN_PRODUCT_KEYS = {
    "runId",
    "run_id",
    "reviewId",
    "review_id",
    "decisionId",
    "decision_id",
    "appId",
    "app_id",
}
FORBIDDEN_CAMEL_ALIASES = {"subject", "operationId", "targetId", "receiptId"}
ALLOWED_CONSTRAINT_KEYS = {
    "destination_mode",
    "target_binding_id",
    "repository_id",
    "collaborator_login",
    "artifact_digest",
    "expected_parent",
}
DESTINATION_MODES = {"hape_organization", "customer_organization", "customer_personal"}
RETRY_CLASSES = {"none", "idempotent_replay", "reconcile_then_retry", "manual"}
REQUIRED_GRANT_CLAIMS = (
    "jti",
    "iss",
    "aud",
    "sub",
    "tenant_id",
    "operation",
    "operation_id",
    "resource_constraints",
    "input_digest",
    "iat",
    "nbf",
    "exp",
    "kid",
)
REPO_NAME_PREFIX = "hape-mgr-"
REPO_NAME_HEX_LENGTH = 16
MAX_NAME_RETRIES = 8
GRANT_MAX_LIFETIME_SECONDS = 300
RECEIPT_ENVELOPE_VERSION = "github.v2"


@dataclass
class VerificationKey:
    kid: str
    public_pem: str
    status: str = "active"


@dataclass
class ManagedDestination:
    destination_id: str
    mode: str
    tenant_subject: str | None
    registration_id: str
    installation_id: int
    account_id: int
    account_login: str
    account_type: str
    repository_selection: str
    configuration_revision: str
    permission_fingerprint: str
    status: str
    verified_at: str
    last_observed_at: str


@dataclass
class ManagedRepository:
    repository_id: str
    destination_id: str
    ownership_mode: str
    tenant_subject: str
    provider_repository_id: int | None
    repository_name: str
    owner_account_id: int
    owner_login: str
    visibility: str
    default_branch: str
    source_snapshot_digest: str
    baseline_sha: str | None
    result_sha: str | None
    status: str


@dataclass
class ProviderOperation:
    operation_id: str
    subject_id: str
    tenant_subject: str
    operation: str
    idempotency_key: str
    canonical_request_hash: str
    grant_jti: str
    target_binding_id: str
    repository_id: str | None
    state: str
    attempt_count: int
    provider_marker: str
    last_error_code: str
    retry_class: str
    reserved_at: str
    started_at: str | None
    completed_at: str | None
    reconciled_at: str | None


@dataclass
class ProviderReceipt:
    receipt_id: str
    envelope_version: str
    operation_id: str
    operation: str
    subject_id: str
    target_binding_id: str
    repository_id: str | None
    input_digest: str
    output_digest: str
    status: str
    issued_at: str
    completed_at: str | None
    safe_provider_ids: dict[str, Any] = field(default_factory=dict)
    retry_class: str = "none"
    customer_safe_error_code: str = ""


def collect_forbidden_keys(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FORBIDDEN_PRODUCT_KEYS or key in FORBIDDEN_CAMEL_ALIASES:
                found.append(str(key))
            found.extend(collect_forbidden_keys(nested))
    elif isinstance(value, list):
        for item in value:
            found.extend(collect_forbidden_keys(item))
    return found


if __name__ == "__main__":
    print(RECEIPT_ENVELOPE_VERSION)
    print(collect_forbidden_keys({"runId": "x"}))
