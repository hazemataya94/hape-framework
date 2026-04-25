from __future__ import annotations

from pydantic import BaseModel


class CreateTokenRequest(BaseModel):
    name: str


class CreateTokenResponse(BaseModel):
    token: str
    token_id: str
    name: str
    created_at: str


class TokenMetadata(BaseModel):
    token_id: str
    name: str
    created_at: str
    revoked: bool


class RevokeTokenRequest(BaseModel):
    token_id: str
