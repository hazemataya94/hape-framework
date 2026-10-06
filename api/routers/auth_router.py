from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_token_service, require_admin_key
from api.schemas.auth_schemas import CreateTokenRequest, CreateTokenResponse, RevokeTokenRequest, TokenMetadata
from api.auth.token_service import ApiTokenService
from services.github_app_service import MANAGED_OPERATIONS, SOURCE_OPERATIONS

router = APIRouter(prefix="/auth", tags=["auth"])

PRODUCT_CALLER_ROLE_OPERATIONS = {
    "source-read": sorted(SOURCE_OPERATIONS),
    "managed-write": sorted(MANAGED_OPERATIONS),
}


@router.post("/tokens", response_model=CreateTokenResponse, dependencies=[Depends(require_admin_key)])
def create_token(payload: CreateTokenRequest, token_service: ApiTokenService = Depends(get_token_service)) -> dict[str, str]:
    role = (payload.credential_role or "").strip() or None
    if role is None:
        return token_service.create_token(name=payload.name)
    if role not in PRODUCT_CALLER_ROLE_OPERATIONS:
        raise HTTPException(status_code=400, detail="credential_role must be source-read or managed-write.")
    operations = list(PRODUCT_CALLER_ROLE_OPERATIONS[role])
    if not operations:
        raise HTTPException(status_code=400, detail="allowed_operations cannot be empty.")
    if payload.exp_seconds is not None and int(payload.exp_seconds) <= 0:
        raise HTTPException(status_code=400, detail="exp_seconds must be a positive TTL.")
    return token_service.create_token(
        name=payload.name,
        credential_role=role,
        allowed_operations=operations,
        exp_seconds=payload.exp_seconds,
    )


@router.get("/tokens", response_model=list[TokenMetadata], dependencies=[Depends(require_admin_key)])
def list_tokens(token_service: ApiTokenService = Depends(get_token_service)) -> list[dict[str, str | bool]]:
    return token_service.list_tokens()


@router.post("/tokens/revoke", dependencies=[Depends(require_admin_key)])
def revoke_token(payload: RevokeTokenRequest, token_service: ApiTokenService = Depends(get_token_service)) -> dict[str, str]:
    revoked = token_service.revoke_token(token_id=payload.token_id)
    if not revoked:
        raise HTTPException(status_code=404, detail="Token not found.")
    return {"message": "Token revoked."}
