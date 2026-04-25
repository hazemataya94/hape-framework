from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, Request, status

from api.auth.rate_limiter import TokenRateLimiter
from api.auth.token_service import ApiTokenService


@dataclass
class AuthContext:
    token_id: str
    token_name: str
    token_hash: str


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
    return AuthContext(token_id=validated["token_id"], token_name=validated["name"], token_hash=validated["token_hash"])


def require_admin_key(x_hape_admin_key: str = Header(default=""), admin_key: str = Depends(get_admin_key)) -> None:
    if not admin_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="API admin key is not configured.")
    if x_hape_admin_key != admin_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin key.")
