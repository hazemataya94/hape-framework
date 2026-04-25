from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_token_service, require_admin_key
from api.schemas.auth_schemas import CreateTokenRequest, CreateTokenResponse, RevokeTokenRequest, TokenMetadata
from api.auth.token_service import ApiTokenService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/tokens", response_model=CreateTokenResponse, dependencies=[Depends(require_admin_key)])
def create_token(payload: CreateTokenRequest, token_service: ApiTokenService = Depends(get_token_service)) -> dict[str, str]:
    return token_service.create_token(name=payload.name)


@router.get("/tokens", response_model=list[TokenMetadata], dependencies=[Depends(require_admin_key)])
def list_tokens(token_service: ApiTokenService = Depends(get_token_service)) -> list[dict[str, str | bool]]:
    return token_service.list_tokens()


@router.post("/tokens/revoke", dependencies=[Depends(require_admin_key)])
def revoke_token(payload: RevokeTokenRequest, token_service: ApiTokenService = Depends(get_token_service)) -> dict[str, str]:
    revoked = token_service.revoke_token(token_id=payload.token_id)
    if not revoked:
        raise HTTPException(status_code=404, detail="Token not found.")
    return {"message": "Token revoked."}
