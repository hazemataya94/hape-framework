from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from fastapi import Depends, Header, HTTPException, Request, status

from api.auth.rate_limiter import TokenRateLimiter
from api.auth.token_service import ApiTokenService

PRODUCT_CALLER_ROLES = {"source-read", "managed-write"}
PRODUCT_CALLER_ISS = "hape-platform-agent-backend"
PRODUCT_CALLER_AUD = "hape-framework"
PRODUCT_CALLER_SUB = "hape-platform-agent-backend"
POLICY_DENIED_DETAIL = {
    "code": "policy_denied",
    "message": "The authenticated subject cannot perform this action.",
}
UNAUTHORIZED_DETAIL = {
    "code": "unauthorized",
    "message": "A bearer token or local account is required.",
}
GITHUB_OPERATION_ROLES: dict[str, tuple[str, ...]] = {
    "installation.setup_url": ("source-read",),
    "installation.verify": ("source-read",),
    "installation.status": ("source-read",),
    "repository.discover": ("source-read",),
    "revision.resolve": ("source-read",),
    "snapshot.read": ("source-read",),
    "repository.create_private": ("managed-write",),
    "commit.publish_baseline": ("managed-write",),
    "commit.publish_artifact": ("managed-write",),
    "tag.publish_annotated": ("managed-write",),
    "repository.dispose": ("managed-write",),
    "receipt.get": ("source-read", "managed-write"),
    "managed_destination.status": ("managed-write",),
    "managed_target.setup_url": ("managed-write",),
    "managed_target.verify": ("managed-write",),
    "managed_target.status": ("managed-write",),
    "managed_repository.create_private": ("managed-write",),
    "managed_repository.publish_baseline": ("managed-write",),
    "managed_repository.publish_artifact": ("managed-write",),
    "managed_repository.publish_tag": ("managed-write",),
    "managed_repository.dispose": ("managed-write",),
    "provider_operation.get": ("managed-write",),
    "provider_receipt.get": ("managed-write",),
}


@dataclass
class AuthContext:
    token_id: str
    token_name: str
    token_hash: str
    credential_role: str | None = None
    allowed_operations: tuple[str, ...] = field(default_factory=tuple)
    iss: str | None = None
    aud: str | None = None
    sub: str | None = None
    jti: str | None = None
    iat: int | None = None
    exp: int | None = None
    revoked: bool = False


def get_token_service(request: Request) -> ApiTokenService:
    token_service = getattr(request.app.state, "token_service", None)
    if token_service is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token service is not initialized.")
    return token_service


def get_rate_limiter(request: Request) -> TokenRateLimiter:
    rate_limiter = getattr(request.app.state, "rate_limiter", None)
    if rate_limiter is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Rate limiter is not initialized.")
    return rate_limiter


def get_admin_key(request: Request) -> str:
    admin_key = getattr(request.app.state, "api_admin_key", "")
    return str(admin_key)


def require_auth_token(authorization: str = Header(default=""), token_service: ApiTokenService = Depends(get_token_service), rate_limiter: TokenRateLimiter = Depends(get_rate_limiter)) -> AuthContext:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header.")
    token_value = authorization.replace("Bearer ", "", 1).strip()
    if not token_value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token.")
    validated = token_service.validate_token(token_value)
    if validated is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API token.")
    allowed, retry_after = rate_limiter.allow(validated["token_hash"])
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for token. Retry in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )
    allowed_operations = validated.get("allowed_operations") or []
    if not isinstance(allowed_operations, list):
        allowed_operations = []
    return AuthContext(
        token_id=str(validated["token_id"]),
        token_name=str(validated["name"]),
        token_hash=str(validated["token_hash"]),
        credential_role=validated.get("credential_role"),
        allowed_operations=tuple(str(item) for item in allowed_operations),
        iss=validated.get("iss"),
        aud=validated.get("aud"),
        sub=validated.get("sub"),
        jti=validated.get("jti"),
        iat=validated.get("iat") if isinstance(validated.get("iat"), int) else None,
        exp=validated.get("exp") if isinstance(validated.get("exp"), int) else None,
        revoked=bool(validated.get("revoked", False)),
    )


def require_admin_key(x_hape_admin_key: str = Header(default=""), admin_key: str = Depends(get_admin_key)) -> None:
    if not admin_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="API admin key is not configured.")
    if x_hape_admin_key != admin_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin key.")


def deny_product_legacy_github(auth: AuthContext = Depends(require_auth_token)) -> AuthContext:
    if auth.credential_role in PRODUCT_CALLER_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=POLICY_DENIED_DETAIL)
    return auth


def require_github_operation(operation: str) -> Callable[..., AuthContext]:
    allowed_roles = GITHUB_OPERATION_ROLES.get(operation, ())

    def _require_operation(auth: AuthContext = Depends(require_auth_token)) -> AuthContext:
        if auth.credential_role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=POLICY_DENIED_DETAIL)
        if operation not in auth.allowed_operations:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=POLICY_DENIED_DETAIL)
        if auth.iss != PRODUCT_CALLER_ISS or auth.aud != PRODUCT_CALLER_AUD or auth.sub != PRODUCT_CALLER_SUB:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=POLICY_DENIED_DETAIL)
        if auth.revoked:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=UNAUTHORIZED_DETAIL)
        return auth

    return _require_operation


def get_github_app_service(request: Request) -> Any:
    github_app_service = getattr(request.app.state, "github_app_service", None)
    if github_app_service is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="GitHub App service is not initialized.")
    return github_app_service


def get_github_v2_service(request: Request) -> Any:
    github_v2_service = getattr(request.app.state, "github_v2_service", None)
    if github_v2_service is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="GitHub v2 service is not initialized.")
    return github_v2_service
