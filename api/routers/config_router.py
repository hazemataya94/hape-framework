from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from services.config_service import ConfigService

router = APIRouter(prefix="/config", tags=["config"])


class InitConfigFileRequest(BaseModel):
    config_file_path: str | None = None
    dot_env_file: str | None = None


class ShowConfigFileRequest(BaseModel):
    config_file_path: str | None = None
    reveal_secrets: bool = False


@router.post("/init-config-file")
def init_config_file(payload: InitConfigFileRequest) -> dict[str, str]:
    config_service = ConfigService()
    config_path = config_service.init_config_file(config_path=payload.config_file_path, dot_env_file=payload.dot_env_file)
    return {"config_path": config_path}


@router.post("/show")
def show_config_file(payload: ShowConfigFileRequest) -> dict[str, object]:
    config_service = ConfigService()
    return config_service.show_config_file(
        config_path=payload.config_file_path,
        reveal_secrets=payload.reveal_secrets,
    )
