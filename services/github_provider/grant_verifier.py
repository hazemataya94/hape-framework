from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

import jwt
from jwt import InvalidTokenError

from services.github_provider.errors import GitHubV2Error
from services.github_provider.models import ALLOWED_CONSTRAINT_KEYS, DESTINATION_MODES, FORBIDDEN_CAMEL_ALIASES, FORBIDDEN_PRODUCT_KEYS, GRANT_MAX_LIFETIME_SECONDS, REQUIRED_GRANT_CLAIMS, VerificationKey, collect_forbidden_keys


class GrantVerifier:
    ALLOWED_ALGORITHMS = ("RS256",)
    EXPECTED_ISS = "hape-platform-agent-authorization"
    EXPECTED_AUD = "hape-framework"

    def __init__(self, keys: list[VerificationKey] | None = None, clock: Callable[[], datetime] | None = None) -> None:
        self._keys = {item.kid: item for item in (keys or [])}
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def _lookup_key(self, kid: str) -> VerificationKey:
        key = self._keys.get(kid)
        if key is None or key.status not in {"active", "overlap"}:
            raise GitHubV2Error("invalid_grant_signature")
        return key

    def _reject_forbidden(self, payload: dict[str, Any]) -> None:
        found = collect_forbidden_keys(payload)
        if found:
            raise GitHubV2Error("policy_denied")
        for key in payload:
            if key in FORBIDDEN_PRODUCT_KEYS or key in FORBIDDEN_CAMEL_ALIASES:
                raise GitHubV2Error("policy_denied")

    def _validate_constraints(self, operation: str, constraints: Any) -> dict[str, Any]:
        if not isinstance(constraints, dict):
            raise GitHubV2Error("invalid_resource_constraints")
        unknown = set(constraints) - ALLOWED_CONSTRAINT_KEYS
        if unknown:
            raise GitHubV2Error("invalid_resource_constraints")
        mode = constraints.get("destination_mode")
        if mode is not None and mode not in DESTINATION_MODES:
            raise GitHubV2Error("unsupported_destination_mode")
        if operation == "managed_repository.create_private":
            if mode == "hape_organization" and not constraints.get("collaborator_login"):
                raise GitHubV2Error("invalid_resource_constraints")
            if mode in {"customer_organization", "customer_personal"} and "collaborator_login" in constraints:
                raise GitHubV2Error("invalid_resource_constraints")
        return constraints

    def verify(self, token: str, expected_operation: str, expected_sub: str | None = None) -> dict[str, Any]:
        if not token:
            raise GitHubV2Error("unauthorized")
        try:
            header = jwt.get_unverified_header(token)
        except InvalidTokenError as exc:
            raise GitHubV2Error("invalid_grant_signature") from exc
        kid = str(header.get("kid") or "")
        key = self._lookup_key(kid)
        try:
            payload = jwt.decode(token, key.public_pem, algorithms=list(self.ALLOWED_ALGORITHMS), audience=self.EXPECTED_AUD, issuer=self.EXPECTED_ISS, options={"require": ["exp", "iat", "nbf", "iss", "aud", "sub"]})
        except InvalidTokenError as exc:
            raise GitHubV2Error("invalid_grant_signature") from exc
        if not isinstance(payload, dict):
            raise GitHubV2Error("invalid_grant_signature")
        payload["kid"] = kid
        self._reject_forbidden(payload)
        missing = [claim for claim in REQUIRED_GRANT_CLAIMS if claim not in payload]
        if missing:
            raise GitHubV2Error("invalid_grant_signature")
        if payload.get("operation") != expected_operation:
            raise GitHubV2Error("policy_denied")
        if expected_sub is not None and payload.get("sub") != expected_sub:
            raise GitHubV2Error("policy_denied")
        issued_at = int(payload["iat"])
        expires_at = int(payload["exp"])
        if expires_at - issued_at > GRANT_MAX_LIFETIME_SECONDS:
            raise GitHubV2Error("grant_expired")
        now = int(self._clock().timestamp())
        if expires_at < now:
            raise GitHubV2Error("grant_expired")
        payload["resource_constraints"] = self._validate_constraints(expected_operation, payload.get("resource_constraints"))
        return payload


if __name__ == "__main__":
    verifier = GrantVerifier()
    print(verifier.EXPECTED_AUD)
