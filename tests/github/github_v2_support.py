from __future__ import annotations

from datetime import datetime, timezone
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt

from repositories.sqlite_github_provider_repository import SqliteGitHubProviderRepository
from services.github_provider.canonical import request_digest
from services.github_provider.fixture_provider import FixtureGitHubProvider
from services.github_provider.grant_verifier import GrantVerifier
from services.github_provider.models import VerificationKey
from services.github_provider.v2_service import GitHubV2Service


KID = "example-v2-key"
TENANT = "11111111-1111-1111-1111-111111111111"
SUBJECT_ID = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
GRANT_SUB = "hape-platform-agent-backend"


def generate_key_pair() -> tuple[str, str]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode("utf-8")
    public_pem = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode("utf-8")
    return private_pem, public_pem


def digest_request(request: dict) -> str:
    payload = {key: value for key, value in request.items() if key != "authorization_grant" and value not in (None, "", [], {})}
    if "files" in payload:
        files = []
        for item in payload["files"]:
            raw = item.get("bytes")
            if raw is None and item.get("hex_bytes"):
                raw = bytes.fromhex(str(item["hex_bytes"]))
            elif isinstance(raw, str):
                raw = raw.encode("utf-8")
            from services.github_provider.canonical import sha256_hex

            files.append({"digest": sha256_hex(raw), "mode": item.get("mode") or "100644", "path": item["path"], "size": len(raw)})
        payload["files"] = sorted(files, key=lambda item: item["path"])
    return request_digest(payload)


def sign_grant(private_pem: str, operation: str, request: dict, extra: dict | None = None) -> str:
    now = int(datetime.now(timezone.utc).timestamp())
    constraints = extra.get("resource_constraints") if extra else None
    if constraints is None:
        constraints = {}
        for key in ("destination_mode", "target_binding_id", "repository_id", "collaborator_login", "artifact_digest", "expected_parent"):
            if request.get(key):
                constraints[key] = request[key]
    payload = {
        "jti": str(uuid.uuid4()),
        "iss": "hape-platform-agent-authorization",
        "aud": "hape-framework",
        "sub": GRANT_SUB,
        "tenant_id": TENANT,
        "operation": operation,
        "operation_id": request.get("operation_id") or str(uuid.uuid4()),
        "resource_constraints": constraints,
        "input_digest": digest_request(request),
        "iat": now,
        "nbf": now,
        "exp": now + 300,
        "kid": KID,
    }
    if extra:
        payload.update({key: value for key, value in extra.items() if key != "resource_constraints"})
        if "resource_constraints" in extra:
            payload["resource_constraints"] = extra["resource_constraints"]
        payload["input_digest"] = extra.get("input_digest", payload["input_digest"])
    return jwt.encode(payload, private_pem, algorithm="RS256", headers={"kid": KID})


def sample_files(text: str = "# Example\n") -> list[dict]:
    return [{"path": "README.md", "mode": "100644", "bytes": text.encode("utf-8")}]


def build_service(sqlite_path: str = ":memory:", private_pem: str = "", public_pem: str = "") -> tuple[GitHubV2Service, FixtureGitHubProvider, str, str]:
    if not private_pem or not public_pem:
        private_pem, public_pem = generate_key_pair()
    provider = FixtureGitHubProvider()
    provider.seed_installation(1, 11, "example-org", "Organization")
    provider.seed_installation(201, 21, "customer-org", "Organization")
    provider.seed_installation(301, 31, "customer-user", "User")
    verifier = GrantVerifier([VerificationKey(kid=KID, public_pem=public_pem, status="active")])
    service = GitHubV2Service(SqliteGitHubProviderRepository(sqlite_path), provider, verifier)
    return service, provider, private_pem, public_pem


def signed_request(service: GitHubV2Service, private_pem: str, operation: str, request: dict, extra: dict | None = None) -> dict:
    body = dict(request)
    if operation.startswith("managed_repository.") or operation.startswith("managed_target."):
        body.setdefault("operation_id", str(uuid.uuid4()))
        body.setdefault("subject_id", SUBJECT_ID)
    body["authorization_grant"] = sign_grant(private_pem, operation, body, extra)
    return body


if __name__ == "__main__":
    print(KID)
