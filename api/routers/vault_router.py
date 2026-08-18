from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from services.vault_service import VaultService

router = APIRouter(prefix="/vault", tags=["vault"])


class KvGetRequest(BaseModel):
    secret_id_file: str | None = None
    role_id: str | None = None
    vault_addr: str | None = None
    auth_path: str | None = None
    kv_mount: str | None = None
    kv_path: str | None = None
    kv_field: str | None = None
    omit_value: bool = False


@router.post("/kv-get")
def kv_get(payload: KvGetRequest) -> dict[str, object]:
    vault_service = VaultService()
    return vault_service.kv_get(
        omit_value=payload.omit_value,
        vault_addr=payload.vault_addr,
        role_id=payload.role_id,
        secret_id_file=payload.secret_id_file,
        auth_path=payload.auth_path,
        kv_mount=payload.kv_mount,
        kv_relative_path=payload.kv_path,
        kv_field=payload.kv_field,
    )


if __name__ == "__main__":
    print(KvGetRequest.__name__)
    print(router.prefix)
