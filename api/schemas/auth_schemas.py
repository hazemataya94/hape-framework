from __future__ import annotations

from pydantic import BaseModel


class CreateTokenRequest(BaseModel):
    name: str
    credential_role: str | None = None
    exp_seconds: int | None = None


class CreateTokenResponse(BaseModel):
    token: str
    token_id: str
    name: str
    created_at: str
    credential_role: str | None = None
    jti: str | None = None


class TokenMetadata(BaseModel):
    token_id: str
    name: str
    created_at: str
    revoked: bool


class RevokeTokenRequest(BaseModel):
    token_id: str


class ProductCallerClaims(BaseModel):
    iss: str
    aud: str
    sub: str
    credential_role: str
    allowed_operations: list[str]
    jti: str
    iat: int
    exp: int
    revoked: bool = False
