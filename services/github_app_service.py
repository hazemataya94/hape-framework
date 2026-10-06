from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import base64
import hashlib
import json
import re
import secrets
import unicodedata
import uuid
from typing import Any, Callable, Protocol
from urllib.parse import urlparse

from clients.github_app_client import GitHubAppClient, GitHubAppClientError, GitHubAppRegistration
from core.config import Config
from core.logging import LocalLogging


ERROR_HTTP = {
    "unauthorized": 401,
    "policy_denied": 403,
    "not_found": 404,
    "expired_state": 401,
    "replay_denied": 403,
    "conflict": 409,
    "digest_mismatch": 409,
    "parent_mismatch": 409,
    "snapshot_rejected": 422,
    "organization_mismatch": 403,
    "provider_unavailable": 503,
    "rate_limited": 429,
    "disposal_blocked": 409,
    "legal_hold_unsupported": 403,
    "unknown_operation": 403,
    "grant_expired": 401,
    "grant_replayed": 403,
    "write_collaborator_required": 422,
    "write_collaborator_failed": 409,
}
ERROR_MESSAGES = {
    "unauthorized": "A bearer token or local account is required.",
    "policy_denied": "The authenticated subject cannot perform this action.",
    "not_found": "The requested resource was not found.",
    "conflict": "The request conflicts with an existing receipt or revision.",
    "snapshot_rejected": "The snapshot failed admission.",
    "rate_limited": "The provider is rate limited. Retry later.",
    "provider_unavailable": "The provider is temporarily unavailable.",
    "expired_state": "The installation state is no longer valid.",
    "replay_denied": "The installation state was already used.",
    "digest_mismatch": "The request digest does not match the sealed input.",
    "parent_mismatch": "The expected parent revision does not match.",
    "organization_mismatch": "The organization is outside the configured HAPE boundary.",
    "disposal_blocked": "Disposal cannot be completed.",
    "legal_hold_unsupported": "Legal hold is not supported.",
    "unknown_operation": "The requested operation is not allowed.",
    "grant_expired": "The authorization grant has expired.",
    "grant_replayed": "The authorization grant was already used.",
    "write_collaborator_required": "A write collaborator email or login is required when creating a private repository.",
    "write_collaborator_failed": "The write collaborator could not be added to the private repository.",
}
SOURCE_OPERATIONS = {
    "installation.setup_url",
    "installation.verify",
    "installation.status",
    "repository.discover",
    "revision.resolve",
    "snapshot.read",
    "receipt.get",
}
MANAGED_OPERATIONS = {
    "repository.create_private",
    "commit.publish_baseline",
    "commit.publish_artifact",
    "tag.publish_annotated",
    "repository.dispose",
    "receipt.get",
}
REQUIRED_GRANT_FIELDS = (
    "grantId",
    "iss",
    "aud",
    "sub",
    "tenantId",
    "appId",
    "operation",
    "resourceConstraints",
    "inputDigest",
    "nonce",
    "iat",
    "exp",
    "decisionId",
)
FORBIDDEN_RECEIPT_TOKENS = (
    "provider_credential",
    "source_body",
    "private_endpoint",
    "raw_provider_error",
    "private_key_path",
    "authorization_header",
    "token",
    "api_key",
    "password",
    "secret",
    "authorization",
    "credential",
    "private_key",
    "authorizationcode",
    "codeverifier",
    "clientsecret",
    "accesstoken",
    "refreshtoken",
)
HIGH_CONFIDENCE_SECRET_PATTERNS = (
    re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"ghs_[A-Za-z0-9]{20,}"),
    re.compile(r"ghu_[A-Za-z0-9]{20,}"),
    re.compile(r"ghr_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"x-access-token"),
)
LFS_POINTER_PREFIX = "version https://git-lfs.github.com/spec/v1"
FAIL_CLOSED_REASONS = {
    "path_traversal",
    "absolute_path",
    "backslash_separator",
    "nul_byte",
    "dot_git_segment",
    "empty_segment",
    "dot_or_dotdot_segment",
    "case_collision",
    "unicode_nfc_mismatch",
    "symlink",
    "submodule",
    "gitlink",
    "lfs_pointer",
    "unsupported_mode",
    "archive_expansion",
    "oversized_file",
    "oversized_tree",
    "too_many_files",
    "high_confidence_secret",
}
NON_ENUMERATING_CLASSES = {"hidden", "missing", "unauthorized", "revoked", "cross_tenant"}


class GitHubAppError(Exception):
    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        self.message = message or ERROR_MESSAGES.get(code, ERROR_MESSAGES["policy_denied"])
        self.http_status = ERROR_HTTP.get(code, 403)
        super().__init__(self.message)


@dataclass
class VaultAgentMemoryCredentialSink:
    memory: dict[str, GitHubAppRegistration] = field(default_factory=dict)

    def get_registration(self, role: str) -> GitHubAppRegistration:
        registration = self.memory.get(role)
        if registration is None:
            raise GitHubAppError("provider_unavailable")
        return registration


class GitHubAppCredentialSink(Protocol):
    def get_registration(self, role: str) -> GitHubAppRegistration: ...


class GitHubAppService:
    RECEIPT_ENVELOPE_VERSION = "1.20.0"
    INSTALLATION_STATE_TTL_SECONDS = 600
    GRANT_TTL_SECONDS = 300
    INSTALLATION_TOKEN_TTL_SECONDS = 300
    MAX_FILES = 2000
    MAX_FILE_BYTES = 1048576
    MAX_TOTAL_BYTES = 52428800
    MAX_PATH_BYTES = 255
    MAX_PATH_SEGMENTS = 20
    MAX_TREE_DEPTH = 20
    MAX_RECURSIVE_RETRIES = 3
    SETUP_STATE_MIN_BYTES = 32
    MAX_USER_INSTALLATION_PAGES = 20
    SOURCE_IMPORT_REGISTRATION_ID = "source-import"
    REPO_NAME_PATTERN = re.compile(r"^hape-mc-[a-z0-9]{8}$")
    TAG_NAME_PATTERN = re.compile(r"^hape-pub-[a-f0-9]{32}-[a-f0-9]{8}$")
    ALLOWED_MODES = {"100644", "100755"}

    def __init__(self, client: GitHubAppClient | None = None, credential_sink: GitHubAppCredentialSink | None = None, clock: Callable[[], datetime] | None = None) -> None:
        self.logger = LocalLogging.get_logger("hape.git_hub_app_service")
        self.client = client or GitHubAppClient()
        self.credential_sink = credential_sink or VaultAgentMemoryCredentialSink()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._used_grants: set[str] = set()
        self._used_authorization_codes: set[str] = set()
        self._idempotency: dict[tuple[str, str, str, str], dict[str, Any]] = {}
        self._receipts: dict[str, dict[str, Any]] = {}
        self._snapshots: dict[tuple[str, str], dict[str, Any]] = {}
        self._managed: dict[str, dict[str, Any]] = {}
        self._token_cache: dict[tuple[str, int, str, str], dict[str, Any]] = {}
        self._installations: dict[int, dict[str, Any]] = {}

    def _now(self) -> datetime:
        current = self._clock()
        if current.tzinfo is None:
            return current.replace(tzinfo=timezone.utc)
        return current

    def _now_iso(self) -> str:
        return self._now().replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _raise(self, code: str) -> None:
        raise GitHubAppError(code)

    def _sha256_hex(self, payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    def _canonical_json(self, payload: dict[str, Any]) -> bytes:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    def _request_hash(self, operation: str, body: dict[str, Any]) -> str:
        return self._sha256_hex(self._canonical_json({"operation": operation, **body}))

    def _redact(self, payload: Any) -> Any:
        if isinstance(payload, dict):
            redacted: dict[str, Any] = {}
            for key, value in payload.items():
                lowered = str(key).lower()
                if any(token in lowered for token in FORBIDDEN_RECEIPT_TOKENS):
                    continue
                redacted[str(key)] = self._redact(value)
            return redacted
        if isinstance(payload, list):
            return [self._redact(item) for item in payload]
        if isinstance(payload, str):
            lowered = payload.lower()
            if "begin " in lowered and "private key" in lowered:
                return "<REDACTED>"
            if payload.startswith(("ghp_", "ghs_", "ghu_", "ghr_", "github_pat_")):
                return "<REDACTED>"
        return payload

    def _receipt(
        self,
        operation: str,
        subject: str,
        resource_ids: dict[str, Any],
        input_digest: str,
        output_digest: str,
        status: str,
        safe_provider_ids: dict[str, Any],
        retry_class: str,
        error_code: str | None = None,
        issued_at: str | None = None,
    ) -> dict[str, Any]:
        completed_at = self._now_iso()
        receipt = {
            "receiptId": str(uuid.uuid4()),
            "envelopeVersion": self.RECEIPT_ENVELOPE_VERSION,
            "operation": operation,
            "subject": subject,
            "resourceIds": self._redact(resource_ids),
            "inputDigest": input_digest,
            "outputDigest": output_digest,
            "status": status,
            "issuedAt": issued_at or completed_at,
            "completedAt": completed_at,
            "safeProviderIds": self._redact(safe_provider_ids),
            "retryClass": retry_class,
            "customerSafeErrorCode": error_code,
        }
        stored = self._redact(receipt)
        self._receipts[str(stored["receiptId"])] = stored
        return stored

    def _fail_receipt(self, operation: str, grant: dict[str, Any], input_digest: str, code: str) -> None:
        self._receipt(
            operation=operation,
            subject=str(grant.get("tenantId", "")),
            resource_ids={},
            input_digest=input_digest,
            output_digest="",
            status="failed",
            safe_provider_ids={},
            retry_class="none",
            error_code=code,
        )
        self._raise(code)

    def _verify_grant(self, grant: dict[str, Any], operation: str, input_digest: str) -> dict[str, Any]:
        if not isinstance(grant, dict):
            self._raise("policy_denied")
        for field_name in REQUIRED_GRANT_FIELDS:
            if field_name not in grant:
                self._raise("policy_denied")
        if grant.get("iss") != "hape-platform-agent-authorization":
            self._raise("policy_denied")
        if grant.get("aud") != "hape-framework":
            self._raise("policy_denied")
        if grant.get("sub") != "hape-platform-agent-backend":
            self._raise("policy_denied")
        if grant.get("operation") != operation:
            self._raise("policy_denied")
        try:
            issued_at = int(grant["iat"])
            expires_at = int(grant["exp"])
        except (TypeError, ValueError):
            self._raise("policy_denied")
            raise
        if expires_at - issued_at > self.GRANT_TTL_SECONDS:
            self._raise("policy_denied")
        if int(self._now().timestamp()) >= expires_at:
            self._raise("grant_expired")
        grant_id = str(grant["grantId"])
        if grant_id in self._used_grants:
            self._raise("grant_replayed")
        if str(grant.get("inputDigest", "")) != input_digest:
            self._raise("digest_mismatch")
        constraints = grant.get("resourceConstraints")
        if not isinstance(constraints, dict):
            self._raise("policy_denied")
        if operation == "commit.publish_artifact" and not grant.get("expectedParent") and not constraints.get("expectedParentSha"):
            self._raise("policy_denied")
        if operation in {"commit.publish_artifact", "tag.publish_annotated"} and (not grant.get("runId") or not grant.get("reviewId")):
            self._raise("policy_denied")
        self._used_grants.add(grant_id)
        return grant

    def _role_for_operation(self, operation: str) -> str:
        if operation in SOURCE_OPERATIONS and operation not in MANAGED_OPERATIONS:
            return "source-read"
        if operation in MANAGED_OPERATIONS and operation not in SOURCE_OPERATIONS:
            return "managed-write"
        if operation == "receipt.get":
            return "source-read"
        self._raise("unknown_operation")
        raise GitHubAppError("unknown_operation")

    def _registration(self, role: str) -> GitHubAppRegistration:
        return self.credential_sink.get_registration(role)

    def _permission_fingerprint(self, permissions: dict[str, str]) -> str:
        return self._sha256_hex(self._canonical_json(permissions))

    def _permissions_match(self, actual: dict[str, str], expected: dict[str, str]) -> bool:
        for key, value in expected.items():
            if actual.get(key) != value:
                return False
        if actual.get("administration") not in (None, "none") and expected.get("administration") in (None, "none"):
            return False
        return True

    def _mint_token(self, role: str, installation_id: int) -> str:
        registration = self._registration(role)
        partition = (
            registration.registration_id,
            installation_id,
            "selected",
            self._permission_fingerprint(registration.expected_permissions),
        )
        cached = self._token_cache.get(partition)
        now_ts = int(self._now().timestamp())
        if cached and int(cached["expires_at"]) > now_ts:
            return str(cached["token"])
        try:
            minted = self.client.mint_installation_token(registration, installation_id)
        except GitHubAppClientError as exc:
            self._raise("rate_limited" if exc.code == "rate_limited" else "provider_unavailable")
            raise
        permissions = minted.get("permissions") or {}
        if not self._permissions_match(permissions, registration.expected_permissions):
            self._token_cache.pop(partition, None)
            self._raise("policy_denied")
        self._token_cache[partition] = {
            "token": minted["token"],
            "expires_at": now_ts + self.INSTALLATION_TOKEN_TTL_SECONDS,
            "permissions": permissions,
        }
        return str(minted["token"])

    def _map_client_error(self, exc: GitHubAppClientError, *, not_found_code: str = "not_found") -> None:
        if exc.code == "rate_limited":
            self._raise("rate_limited")
        if exc.code == "not_found":
            self._raise(not_found_code)
        if exc.code == "conflict":
            self._raise("conflict")
        self._raise("provider_unavailable")

    def _idempotency_key(self, grant: dict[str, Any], operation: str, idempotency_key: str) -> tuple[str, str, str, str]:
        return (str(grant["tenantId"]), str(grant["appId"]), operation, idempotency_key)

    def _replay_or_reserve(self, grant: dict[str, Any], operation: str, idempotency_key: str, request_hash: str) -> dict[str, Any] | None:
        key = self._idempotency_key(grant, operation, idempotency_key)
        existing = self._idempotency.get(key)
        if existing is None:
            self._idempotency[key] = {"hash": request_hash, "state": "executing", "receipt": None}
            return None
        if existing["hash"] != request_hash:
            self._raise("conflict")
        receipt = existing.get("receipt")
        if isinstance(receipt, dict):
            return receipt
        return None

    def _store_idempotent(self, grant: dict[str, Any], operation: str, idempotency_key: str, receipt: dict[str, Any], request_hash: str) -> dict[str, Any]:
        key = self._idempotency_key(grant, operation, idempotency_key)
        self._idempotency[key] = {"hash": request_hash, "state": "succeeded", "receipt": receipt}
        return receipt

    def _validate_path(self, path: str) -> str | None:
        if "\x00" in path:
            return "nul_byte"
        if path.startswith("/"):
            return "absolute_path"
        if "\\" in path:
            return "backslash_separator"
        if unicodedata.normalize("NFC", path) != path:
            return "unicode_nfc_mismatch"
        try:
            path.encode("utf-8")
        except UnicodeEncodeError:
            return "unicode_nfc_mismatch"
        if len(path.encode("utf-8")) > self.MAX_PATH_BYTES:
            return "oversized_tree"
        segments = path.split("/")
        if len(segments) > self.MAX_PATH_SEGMENTS:
            return "oversized_tree"
        for segment in segments:
            if segment == "":
                return "empty_segment"
            if segment in {".", ".."}:
                return "dot_or_dotdot_segment" if segment == "." else "path_traversal"
            if segment.lower() == ".git":
                return "dot_git_segment"
        return None

    def _detect_secret(self, content: bytes) -> bool:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("utf-8", errors="ignore")
        return any(pattern.search(text) for pattern in HIGH_CONFIDENCE_SECRET_PATTERNS)

    def _aggregate_digest(self, files: list[dict[str, Any]]) -> str:
        canonical = b""
        ordered = sorted(files, key=lambda item: str(item["path"]).encode("utf-8"))
        for item in ordered:
            path = str(item["path"])
            mode = str(item["mode"])
            content = item["bytes"]
            if not isinstance(content, (bytes, bytearray)):
                content = str(content).encode("utf-8")
            digest = self._sha256_hex(bytes(content))
            canonical += path.encode("utf-8") + b"\0" + mode.encode("ascii") + b"\0" + str(len(content)).encode("ascii") + b"\0" + digest.encode("ascii") + b"\n"
        return self._sha256_hex(canonical)

    def _admit_files(self, files: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
        if len(files) > self.MAX_FILES:
            self._raise("snapshot_rejected")
        seen_case: dict[str, str] = {}
        admitted: list[dict[str, Any]] = []
        total_bytes = 0
        for item in files:
            path = str(item.get("path", ""))
            mode = str(item.get("mode", ""))
            reason = self._validate_path(path)
            if reason:
                self.logger.info("snapshot_rejected reason=%s", reason)
                self._raise("snapshot_rejected")
            lowered = path.lower()
            if lowered in seen_case and seen_case[lowered] != path:
                self.logger.info("snapshot_rejected reason=case_collision")
                self._raise("snapshot_rejected")
            seen_case[lowered] = path
            if mode == "120000":
                self.logger.info("snapshot_rejected reason=symlink")
                self._raise("snapshot_rejected")
            if mode in {"160000", "040000"}:
                self.logger.info("snapshot_rejected reason=%s", "submodule" if mode == "160000" else "unsupported_mode")
                self._raise("snapshot_rejected")
            if mode not in self.ALLOWED_MODES:
                self.logger.info("snapshot_rejected reason=unsupported_mode")
                self._raise("snapshot_rejected")
            content = item.get("bytes", b"")
            if isinstance(content, str):
                content = content.encode("utf-8")
            if not isinstance(content, (bytes, bytearray)):
                self._raise("snapshot_rejected")
            raw = bytes(content)
            if len(raw) > self.MAX_FILE_BYTES:
                self.logger.info("snapshot_rejected reason=oversized_file")
                self._raise("snapshot_rejected")
            total_bytes += len(raw)
            if total_bytes > self.MAX_TOTAL_BYTES:
                self.logger.info("snapshot_rejected reason=oversized_tree")
                self._raise("snapshot_rejected")
            if raw.startswith(LFS_POINTER_PREFIX.encode("ascii")):
                self.logger.info("snapshot_rejected reason=lfs_pointer")
                self._raise("snapshot_rejected")
            if self._detect_secret(raw):
                self.logger.info("snapshot_rejected reason=high_confidence_secret")
                self._raise("snapshot_rejected")
            admitted.append({"path": path, "mode": mode, "bytes": raw, "digest": self._sha256_hex(raw), "size": len(raw)})
        return admitted, self._aggregate_digest(admitted)

    def _decode_blob(self, payload: dict[str, Any]) -> bytes:
        encoding = str(payload.get("encoding", "base64"))
        content = payload.get("content", "")
        if encoding == "base64":
            return base64.b64decode(str(content))
        if isinstance(content, str):
            return content.encode("utf-8")
        return b""

    def _walk_tree(self, token: str, owner: str, repo: str, tree_sha: str) -> list[dict[str, Any]]:
        retries = 0
        tree_payload: dict[str, Any] | None = None
        while retries < self.MAX_RECURSIVE_RETRIES:
            try:
                tree_payload = self.client.get_git_tree(token, owner, repo, tree_sha, recursive=True)
            except GitHubAppClientError as exc:
                self._map_client_error(exc)
            if tree_payload and not bool(tree_payload.get("truncated")):
                break
            retries += 1
        files: list[dict[str, Any]] = []
        if tree_payload and not bool(tree_payload.get("truncated")):
            entries = tree_payload.get("tree") or []
        else:
            try:
                files = self._walk_individual_trees(token, owner, repo, tree_sha, depth=0)
                return files
            except GitHubAppClientError as exc:
                if exc.code == "truncated":
                    self._raise("provider_unavailable")
                self._map_client_error(exc)
                return []
        if not isinstance(entries, list):
            self._raise("provider_unavailable")
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            entry_type = str(entry.get("type", ""))
            mode = str(entry.get("mode", ""))
            path = str(entry.get("path", ""))
            sha = str(entry.get("sha", ""))
            if entry_type == "tree":
                continue
            if entry_type != "blob":
                files.append({"path": path, "mode": mode, "bytes": b""})
                continue
            try:
                blob = self.client.get_git_blob(token, owner, repo, sha)
            except GitHubAppClientError as exc:
                self._map_client_error(exc)
                continue
            files.append({"path": path, "mode": mode, "bytes": self._decode_blob(blob)})
        return files

    def _walk_individual_trees(self, token: str, owner: str, repo: str, tree_sha: str, depth: int, prefix: str = "") -> list[dict[str, Any]]:
        if depth > self.MAX_TREE_DEPTH:
            raise GitHubAppClientError("truncated")
        payload = self.client.get_git_tree(token, owner, repo, tree_sha, recursive=False)
        if bool(payload.get("truncated")):
            raise GitHubAppClientError("truncated")
        files: list[dict[str, Any]] = []
        for entry in payload.get("tree") or []:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("path", ""))
            path = f"{prefix}{name}" if not prefix else f"{prefix}/{name}"
            mode = str(entry.get("mode", ""))
            sha = str(entry.get("sha", ""))
            entry_type = str(entry.get("type", ""))
            if entry_type == "tree":
                files.extend(self._walk_individual_trees(token, owner, repo, sha, depth + 1, path))
                continue
            if entry_type != "blob":
                files.append({"path": path, "mode": mode, "bytes": b""})
                continue
            blob = self.client.get_git_blob(token, owner, repo, sha)
            files.append({"path": path, "mode": mode, "bytes": self._decode_blob(blob)})
        return files

    def _publish_commit(self, token: str, owner: str, repo: str, files: list[dict[str, Any]], message: str, parents: list[str]) -> str:
        tree_entries: list[dict[str, str]] = []
        for item in files:
            content = bytes(item["bytes"])
            blob = self.client.create_git_blob(token, owner, repo, base64.b64encode(content).decode("ascii"))
            tree_entries.append({"path": str(item["path"]), "mode": str(item["mode"]), "type": "blob", "sha": str(blob["sha"])})
        tree = self.client.create_git_tree(token, owner, repo, tree_entries)
        commit = self.client.create_git_commit(token, owner, repo, message, str(tree["sha"]), parents)
        return str(commit["sha"])

    def _non_enumerating(self) -> None:
        self._raise("not_found")

    def _repo_eligibility(self, repo: dict[str, Any]) -> str | None:
        if bool(repo.get("archived")) or bool(repo.get("disabled")) or bool(repo.get("suspended")):
            return "fail_closed"
        size = repo.get("size")
        if size == 0 or bool(repo.get("empty")):
            return "fail_closed"
        visibility = str(repo.get("visibility") or ("private" if repo.get("private") else "public"))
        if visibility not in {"private", "public", "internal"}:
            return "fail_closed"
        return "fork" if bool(repo.get("fork")) else None

    def _public_github_host(self) -> str:
        raw_url = getattr(self.client, "oauth_base_url", "") or Config.get_github_app_oauth_url()
        parsed = urlparse(raw_url)
        return parsed.netloc or parsed.path or "github.example.com"

    def _validate_setup_state(self, setup_state: str) -> bytes:
        normalized = setup_state.strip().lower()
        if len(normalized) < self.SETUP_STATE_MIN_BYTES * 2 or len(normalized) % 2 != 0:
            self._raise("policy_denied")
        try:
            raw_state = bytes.fromhex(normalized)
        except ValueError:
            self._raise("policy_denied")
            raise
        if len(raw_state) < self.SETUP_STATE_MIN_BYTES:
            self._raise("policy_denied")
        return raw_state

    def _user_controls_installation(self, user_token: str, installation_id: int) -> bool:
        for page in range(1, self.MAX_USER_INSTALLATION_PAGES + 1):
            try:
                payload = self.client.list_user_installations(user_token, page=page, per_page=100)
            except GitHubAppClientError as exc:
                self._map_client_error(exc)
                raise
            installations = payload.get("installations") if isinstance(payload, dict) else None
            if not isinstance(installations, list):
                self._raise("provider_unavailable")
            for item in installations:
                if not isinstance(item, dict):
                    continue
                try:
                    item_id = int(item.get("id"))
                except (TypeError, ValueError):
                    continue
                if item_id == installation_id:
                    return True
            if len(installations) < 100:
                return False
        return False

    def create_setup_url(self, grant: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        operation = "installation.setup_url"
        constraints = grant.get("resourceConstraints") or {}
        setup_state = str(constraints.get("setupState") or "")
        body = {"returnPath": constraints.get("returnPath", "/"), "setupState": setup_state}
        input_digest = str(grant.get("inputDigest") or self._request_hash(operation, body))
        self._verify_grant(grant, operation, input_digest)
        replayed = self._replay_or_reserve(grant, operation, idempotency_key, input_digest)
        if replayed:
            return replayed
        if str(constraints.get("sourceImportRegistrationId") or self.SOURCE_IMPORT_REGISTRATION_ID) != self.SOURCE_IMPORT_REGISTRATION_ID:
            self._raise("not_found")
        raw_state = self._validate_setup_state(setup_state)
        registration = self._registration("source-read")
        slug = str(registration.slug or "").strip()
        client_id = str(registration.client_id or "").strip()
        if not slug or not client_id:
            self._raise("provider_unavailable")
        setup_host = self._public_github_host()
        setup_url = f"https://{setup_host}/apps/{slug}/installations/new?state={setup_state.strip().lower()}"
        receipt = self._receipt(
            operation=operation,
            subject=str(grant["tenantId"]),
            resource_ids={"stateHash": self._sha256_hex(raw_state)},
            input_digest=input_digest,
            output_digest=self._sha256_hex(setup_url.encode("utf-8")),
            status="succeeded",
            safe_provider_ids={"setupHost": setup_host, "clientId": client_id},
            retry_class="new_state",
        )
        receipt["setupUrl"] = setup_url
        return self._store_idempotent(grant, operation, idempotency_key, self._redact(receipt), input_digest)

    def verify_installation(
        self,
        grant: dict[str, Any],
        idempotency_key: str,
        authorization_code: str,
        code_verifier: str,
        installation_id: int,
        callback_url: str,
    ) -> dict[str, Any]:
        operation = "installation.verify"
        body = {"installationId": installation_id, "callbackUrl": callback_url}
        input_digest = str(grant.get("inputDigest") or self._request_hash(operation, body))
        self._verify_grant(grant, operation, input_digest)
        replayed = self._replay_or_reserve(grant, operation, idempotency_key, input_digest)
        if replayed:
            return replayed
        constraints = grant.get("resourceConstraints") or {}
        if str(constraints.get("sourceImportRegistrationId") or self.SOURCE_IMPORT_REGISTRATION_ID) != self.SOURCE_IMPORT_REGISTRATION_ID:
            self._raise("not_found")
        try:
            bound_installation_id = int(constraints.get("installationId"))
        except (TypeError, ValueError):
            self._raise("not_found")
            raise
        if bound_installation_id != installation_id:
            self._raise("not_found")
        if not authorization_code.strip() or not code_verifier.strip() or not callback_url.strip():
            self._raise("policy_denied")
        code_hash = self._sha256_hex(authorization_code.encode("utf-8"))
        if code_hash in self._used_authorization_codes:
            self._raise("replay_denied")
        existing = self._installations.get(installation_id)
        tenant_id = str(grant["tenantId"])
        if existing and existing.get("tenantId") != tenant_id:
            self._raise("not_found")
        registration = self._registration("source-read")
        user_access_token = ""
        refresh_token = ""
        try:
            exchanged = self.client.exchange_user_code(registration, authorization_code, callback_url, code_verifier)
            user_access_token = str(exchanged.get("access_token") or "")
            refresh_token = str(exchanged.get("refresh_token") or "")
            self.client.get_authenticated_user(user_access_token)
            if not self._user_controls_installation(user_access_token, installation_id):
                self._raise("not_found")
            installation = self.client.get_app_installation(registration, installation_id)
        except GitHubAppError:
            raise
        except GitHubAppClientError as exc:
            self._map_client_error(exc)
            raise
        finally:
            user_access_token = ""
            refresh_token = ""
            exchanged = None
        if str(installation.get("suspended_at") or "") or str(installation.get("target_type", "")).lower() == "revoked":
            self._raise("not_found")
        if str(installation.get("setup_action") or "").lower() == "request":
            self._raise("not_found")
        installation_app_id = installation.get("app_id")
        if installation_app_id is not None and str(installation_app_id) != str(registration.app_id):
            self._raise("not_found")
        self._mint_token("source-read", installation_id)
        self._used_authorization_codes.add(code_hash)
        account = installation.get("account") if isinstance(installation.get("account"), dict) else {}
        self._installations[installation_id] = {
            "tenantId": tenant_id,
            "accountId": account.get("id"),
            "status": "connected",
        }
        receipt = self._receipt(
            operation=operation,
            subject=tenant_id,
            resource_ids={"installationId": installation_id},
            input_digest=input_digest,
            output_digest=self._sha256_hex(str(installation_id).encode("utf-8")),
            status="succeeded",
            safe_provider_ids={"installationId": installation_id, "accountLogin": account.get("login")},
            retry_class="replay_denied",
        )
        return self._store_idempotent(grant, operation, idempotency_key, receipt, input_digest)

    def get_installation_status(self, grant: dict[str, Any], installation_id: int) -> dict[str, Any]:
        operation = "installation.status"
        input_digest = str(grant.get("inputDigest") or self._request_hash(operation, {"installationId": installation_id}))
        self._verify_grant(grant, operation, input_digest)
        record = self._installations.get(installation_id)
        if record is None or record.get("tenantId") != grant.get("tenantId"):
            self._raise("not_found")
        registration = self._registration("source-read")
        try:
            installation = self.client.get_app_installation(registration, installation_id)
        except GitHubAppClientError as exc:
            self._map_client_error(exc)
            raise
        status = "revoked" if installation.get("suspended_at") else "connected"
        if status == "revoked":
            self._raise("not_found")
        return self._receipt(
            operation=operation,
            subject=str(grant["tenantId"]),
            resource_ids={"installationId": installation_id},
            input_digest=input_digest,
            output_digest=self._sha256_hex(status.encode("utf-8")),
            status="succeeded",
            safe_provider_ids={"installationStatus": status},
            retry_class="none",
        )

    def discover_repositories(self, grant: dict[str, Any], idempotency_key: str, page: int = 1) -> dict[str, Any]:
        operation = "repository.discover"
        constraints = grant.get("resourceConstraints") or {}
        input_digest = str(grant.get("inputDigest") or self._request_hash(operation, {"page": page}))
        self._verify_grant(grant, operation, input_digest)
        replayed = self._replay_or_reserve(grant, operation, idempotency_key, input_digest)
        if replayed:
            return replayed
        installation_id = int(constraints["installationId"])
        token = self._mint_token("source-read", installation_id)
        try:
            payload = self.client.list_installation_repositories(token, page=page)
        except GitHubAppClientError as exc:
            self._map_client_error(exc)
            raise
        requested_id = constraints.get("repositoryDatabaseId")
        visible: list[dict[str, Any]] = []
        for repo in payload.get("repositories") or []:
            if not isinstance(repo, dict):
                continue
            classification = str(repo.get("hape_class") or "")
            if classification in NON_ENUMERATING_CLASSES:
                continue
            eligibility = self._repo_eligibility(repo)
            if eligibility == "fail_closed":
                continue
            item = {
                "repositoryDatabaseId": repo.get("id"),
                "name": repo.get("name"),
                "visibility": repo.get("visibility") or ("private" if repo.get("private") else "public"),
                "ownerAccountId": (repo.get("owner") or {}).get("id") if isinstance(repo.get("owner"), dict) else repo.get("owner_id"),
                "warning": "fork" if eligibility == "fork" else None,
            }
            visible.append(item)
        if requested_id is not None and all(item.get("repositoryDatabaseId") != requested_id for item in visible):
            self._non_enumerating()
        receipt = self._receipt(
            operation=operation,
            subject=str(grant["tenantId"]),
            resource_ids={"installationId": installation_id, "page": page},
            input_digest=input_digest,
            output_digest=self._sha256_hex(self._canonical_json({"ids": [item["repositoryDatabaseId"] for item in visible]})),
            status="succeeded",
            safe_provider_ids={"count": len(visible)},
            retry_class="same_not_found",
        )
        receipt["repositories"] = visible
        return self._store_idempotent(grant, operation, idempotency_key, self._redact(receipt), input_digest)

    def resolve_revision(self, grant: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        operation = "revision.resolve"
        constraints = grant.get("resourceConstraints") or {}
        input_digest = str(grant.get("inputDigest") or self._request_hash(operation, {"ref": constraints.get("ref")}))
        self._verify_grant(grant, operation, input_digest)
        replayed = self._replay_or_reserve(grant, operation, idempotency_key, input_digest)
        if replayed:
            return replayed
        installation_id = int(constraints["installationId"])
        owner = str(constraints["owner"])
        repo = str(constraints["repository"])
        ref = str(constraints.get("ref") or constraints.get("commitSha"))
        token = self._mint_token("source-read", installation_id)
        try:
            commit = self.client.get_commit(token, owner, repo, ref)
        except GitHubAppClientError as exc:
            self._map_client_error(exc)
            raise
        sha = str(commit.get("sha") or "")
        if not sha:
            self._raise("not_found")
        receipt = self._receipt(
            operation=operation,
            subject=str(grant["tenantId"]),
            resource_ids={"commitSha": sha, "repositoryDatabaseId": constraints.get("repositoryDatabaseId")},
            input_digest=input_digest,
            output_digest=sha,
            status="succeeded",
            safe_provider_ids={"commitSha": sha},
            retry_class="same_sha",
        )
        return self._store_idempotent(grant, operation, idempotency_key, receipt, input_digest)

    def read_snapshot(self, grant: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        operation = "snapshot.read"
        constraints = grant.get("resourceConstraints") or {}
        input_digest = str(grant.get("inputDigest") or self._request_hash(operation, {"commitSha": constraints.get("commitSha")}))
        self._verify_grant(grant, operation, input_digest)
        replayed = self._replay_or_reserve(grant, operation, idempotency_key, input_digest)
        if replayed:
            return replayed
        installation_id = int(constraints["installationId"])
        owner = str(constraints["owner"])
        repo = str(constraints["repository"])
        commit_sha = str(constraints["commitSha"])
        token = self._mint_token("source-read", installation_id)
        try:
            commit = self.client.get_commit(token, owner, repo, commit_sha)
            tree_sha = str((commit.get("commit") or {}).get("tree", {}).get("sha") or commit.get("tree_sha") or "")
            files = self._walk_tree(token, owner, repo, tree_sha)
            admitted, digest = self._admit_files(files)
        except GitHubAppError:
            raise
        except GitHubAppClientError as exc:
            self._map_client_error(exc)
            raise
        tenant_id = str(grant["tenantId"])
        self._snapshots[(tenant_id, digest)] = {"files": admitted, "commitSha": commit_sha}
        receipt = self._receipt(
            operation=operation,
            subject=tenant_id,
            resource_ids={"commitSha": commit_sha, "fileCount": len(admitted)},
            input_digest=input_digest,
            output_digest=digest,
            status="succeeded",
            safe_provider_ids={"aggregateDigest": digest},
            retry_class="same_digest",
        )
        receipt["aggregateDigest"] = digest
        return self._store_idempotent(grant, operation, idempotency_key, self._redact(receipt), input_digest)

    def create_private_repository(self, grant: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        operation = "repository.create_private"
        constraints = grant.get("resourceConstraints") or {}
        organization = str(constraints.get("hapeOrganizationId") or constraints.get("organization") or "")
        input_digest = str(grant.get("inputDigest") or self._request_hash(operation, {"organization": organization}))
        self._verify_grant(grant, operation, input_digest)
        replayed = self._replay_or_reserve(grant, operation, idempotency_key, input_digest)
        if replayed:
            return replayed
        registration = self._registration("managed-write")
        if organization not in registration.organization_allowlist:
            self._raise("organization_mismatch")
        source_digest = str(constraints.get("sourceSnapshotDigest") or "")
        snapshot = self._snapshots.get((str(grant["tenantId"]), source_digest))
        if snapshot is None:
            self._raise("digest_mismatch")
        for item in self._managed.values():
            if item.get("tenantId") == grant["tenantId"] and item.get("sourceDigest") == source_digest and item.get("status") != "disposed":
                self._raise("conflict")
        name = f"hape-mc-{secrets.token_hex(4)}"
        if not self.REPO_NAME_PATTERN.match(name):
            self._raise("provider_unavailable")
        installation_id = int(constraints["installationId"])
        token = self._mint_token("managed-write", installation_id)
        write_login = str(constraints.get("writeCollaboratorLogin") or "").strip()
        write_email = str(constraints.get("writeCollaboratorEmail") or "").strip()
        if not write_login and not write_email:
            self._raise("write_collaborator_required")
        try:
            created = self.client.create_organization_repository(token, organization, name)
            if not write_login:
                write_login = str(self.client.resolve_user_login_by_email(token, write_email) or "").strip()
            if not write_login:
                self._raise("write_collaborator_required")
            added = self.client.add_repository_collaborator(token, organization, name, write_login, "push")
            if not added:
                self._raise("write_collaborator_failed")
        except GitHubAppError:
            raise
        except GitHubAppClientError as exc:
            if exc.code in {"not_found", "unprocessable"}:
                self._raise("write_collaborator_failed")
            self._map_client_error(exc)
            raise
        repository_id = str(created.get("id") or uuid.uuid4())
        self._managed[repository_id] = {
            "tenantId": grant["tenantId"],
            "name": name,
            "organization": organization,
            "sourceDigest": source_digest,
            "status": "created",
            "installationId": installation_id,
        }
        receipt = self._receipt(
            operation=operation,
            subject=str(grant["tenantId"]),
            resource_ids={"repositoryName": name, "organization": organization},
            input_digest=input_digest,
            output_digest=source_digest,
            status="succeeded",
            safe_provider_ids={"repositoryId": repository_id, "repositoryName": name},
            retry_class="same_key_same_hash",
        )
        return self._store_idempotent(grant, operation, idempotency_key, receipt, input_digest)

    def publish_baseline(self, grant: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        operation = "commit.publish_baseline"
        constraints = grant.get("resourceConstraints") or {}
        repository_id = str(constraints.get("repositoryId") or "")
        input_digest = str(grant.get("inputDigest") or self._request_hash(operation, {"repositoryId": repository_id}))
        self._verify_grant(grant, operation, input_digest)
        replayed = self._replay_or_reserve(grant, operation, idempotency_key, input_digest)
        if replayed:
            return replayed
        managed = self._managed.get(repository_id)
        if managed is None or managed.get("tenantId") != grant.get("tenantId"):
            self._raise("not_found")
        snapshot = self._snapshots.get((str(grant["tenantId"]), str(managed["sourceDigest"])))
        if snapshot is None:
            self._raise("digest_mismatch")
        token = self._mint_token("managed-write", int(managed["installationId"]))
        try:
            sha = self._publish_commit(token, str(managed["organization"]), str(managed["name"]), snapshot["files"], "baseline", [])
            self.client.create_git_ref(token, str(managed["organization"]), str(managed["name"]), "refs/heads/main", sha)
        except GitHubAppClientError as exc:
            self._map_client_error(exc)
            raise
        output_digest = self._aggregate_digest(snapshot["files"])
        if output_digest != managed["sourceDigest"]:
            self._raise("digest_mismatch")
        managed["status"] = "baselined"
        managed["baselineSha"] = sha
        receipt = self._receipt(
            operation=operation,
            subject=str(grant["tenantId"]),
            resource_ids={"repositoryId": repository_id, "baselineSha": sha},
            input_digest=input_digest,
            output_digest=output_digest,
            status="succeeded",
            safe_provider_ids={"commitSha": sha},
            retry_class="same_digest",
        )
        return self._store_idempotent(grant, operation, idempotency_key, receipt, input_digest)

    def publish_artifact(self, grant: dict[str, Any], idempotency_key: str, files: list[dict[str, Any]], content_class: str) -> dict[str, Any]:
        operation = "commit.publish_artifact"
        constraints = grant.get("resourceConstraints") or {}
        repository_id = str(constraints.get("repositoryId") or "")
        input_digest = str(grant.get("inputDigest") or self._request_hash(operation, {"repositoryId": repository_id}))
        self._verify_grant(grant, operation, input_digest)
        replayed = self._replay_or_reserve(grant, operation, idempotency_key, input_digest)
        if replayed:
            return replayed
        if content_class == "plan_blueprint_only":
            self._raise("digest_mismatch")
        managed = self._managed.get(repository_id)
        if managed is None or managed.get("tenantId") != grant.get("tenantId"):
            self._raise("not_found")
        admitted, digest = self._admit_files(files)
        review_digest = str(constraints.get("reviewDigest") or grant.get("reviewDigest") or "")
        if review_digest != digest:
            self._raise("digest_mismatch")
        expected_parent = str(grant.get("expectedParent") or constraints.get("expectedParentSha") or "")
        current_parent = str(managed.get("resultSha") or managed.get("baselineSha") or "")
        if expected_parent != current_parent:
            self._raise("parent_mismatch")
        token = self._mint_token("managed-write", int(managed["installationId"]))
        try:
            current_ref = self.client.get_git_ref(token, str(managed["organization"]), str(managed["name"]), "heads/main")
            current_sha = str((current_ref.get("object") or {}).get("sha") or "")
            if current_sha and current_sha != expected_parent:
                self._raise("parent_mismatch")
            sha = self._publish_commit(token, str(managed["organization"]), str(managed["name"]), admitted, "result", [expected_parent] if expected_parent else [])
            self.client.update_git_ref(token, str(managed["organization"]), str(managed["name"]), "heads/main", sha)
        except GitHubAppError:
            raise
        except GitHubAppClientError as exc:
            if exc.code == "unprocessable":
                self._raise("parent_mismatch")
            self._map_client_error(exc)
            raise
        managed["status"] = "published"
        managed["resultSha"] = sha
        receipt = self._receipt(
            operation=operation,
            subject=str(grant["tenantId"]),
            resource_ids={"repositoryId": repository_id, "resultSha": sha},
            input_digest=input_digest,
            output_digest=digest,
            status="succeeded",
            safe_provider_ids={"commitSha": sha},
            retry_class="refresh_parent",
        )
        return self._store_idempotent(grant, operation, idempotency_key, receipt, input_digest)

    def publish_annotated_tag(self, grant: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        operation = "tag.publish_annotated"
        constraints = grant.get("resourceConstraints") or {}
        repository_id = str(constraints.get("repositoryId") or "")
        opaque = str(constraints.get("opaqueSubjectId") or "").replace("-", "")
        input_digest = str(grant.get("inputDigest") or self._request_hash(operation, {"repositoryId": repository_id, "opaqueSubjectId": opaque}))
        self._verify_grant(grant, operation, input_digest)
        replayed = self._replay_or_reserve(grant, operation, idempotency_key, input_digest)
        if replayed:
            return replayed
        if len(opaque) != 32 or any(char not in "0123456789abcdef" for char in opaque):
            self._raise("policy_denied")
        managed = self._managed.get(repository_id)
        if managed is None or managed.get("tenantId") != grant.get("tenantId"):
            self._raise("not_found")
        target_sha = str(constraints.get("commitSha") or managed.get("resultSha") or managed.get("baselineSha") or "")
        tag = f"hape-pub-{opaque}-{secrets.token_hex(4)}"
        if not self.TAG_NAME_PATTERN.match(tag):
            self._raise("provider_unavailable")
        if managed.get("tag") == tag:
            self._raise("conflict")
        token = self._mint_token("managed-write", int(managed["installationId"]))
        try:
            created = self.client.create_git_tag(token, str(managed["organization"]), str(managed["name"]), tag, "published", target_sha)
            self.client.create_git_ref(token, str(managed["organization"]), str(managed["name"]), f"refs/tags/{tag}", str(created.get("sha") or target_sha))
        except GitHubAppClientError as exc:
            if exc.code == "conflict":
                self._raise("conflict")
            self._map_client_error(exc)
            raise
        managed["tag"] = tag
        receipt = self._receipt(
            operation=operation,
            subject=str(grant["tenantId"]),
            resource_ids={"repositoryId": repository_id, "tag": tag},
            input_digest=input_digest,
            output_digest=target_sha,
            status="succeeded",
            safe_provider_ids={"tag": tag, "commitSha": target_sha},
            retry_class="none_on_collision",
        )
        return self._store_idempotent(grant, operation, idempotency_key, receipt, input_digest)

    def dispose_repository(self, grant: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        operation = "repository.dispose"
        constraints = grant.get("resourceConstraints") or {}
        repository_id = str(constraints.get("repositoryId") or "")
        input_digest = str(grant.get("inputDigest") or self._request_hash(operation, {"repositoryId": repository_id}))
        self._verify_grant(grant, operation, input_digest)
        replayed = self._replay_or_reserve(grant, operation, idempotency_key, input_digest)
        if replayed:
            return replayed
        if bool(constraints.get("legalHold")):
            self._raise("legal_hold_unsupported")
        managed = self._managed.get(repository_id)
        if managed is None:
            self._raise("not_found")
        token = self._mint_token("managed-write", int(managed["installationId"]))
        try:
            self.client.delete_repository(token, str(managed["organization"]), str(managed["name"]))
        except GitHubAppClientError as exc:
            if exc.code != "not_found":
                managed["status"] = "retrying"
                self._map_client_error(exc)
        managed["status"] = "disposed"
        receipt = self._receipt(
            operation=operation,
            subject=str(grant["tenantId"]),
            resource_ids={"repositoryId": repository_id},
            input_digest=input_digest,
            output_digest=self._sha256_hex(b"disposed"),
            status="completed",
            safe_provider_ids={"repositoryId": repository_id, "repositoryName": managed["name"]},
            retry_class="retrying_then_completed",
        )
        return self._store_idempotent(grant, operation, idempotency_key, receipt, input_digest)

    def get_receipt(self, grant: dict[str, Any], receipt_id: str) -> dict[str, Any]:
        operation = "receipt.get"
        input_digest = str(grant.get("inputDigest") or self._request_hash(operation, {"receiptId": receipt_id}))
        self._verify_grant(grant, operation, input_digest)
        receipt = self._receipts.get(receipt_id)
        if receipt is None or receipt.get("subject") != grant.get("tenantId"):
            self._raise("not_found")
        return self._redact(receipt)

    def admit_local_files(self, files: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
        return self._admit_files(files)


if __name__ == "__main__":
    print(GitHubAppService.RECEIPT_ENVELOPE_VERSION)
