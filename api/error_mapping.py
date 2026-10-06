from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from core.errors.exceptions import HapeError, HapeExternalError, HapeOperationError, HapeValidationError
from services.github_provider.errors import GitHubV2Error


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HapeValidationError)
    async def _handle_validation_error(_, exc: HapeValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"code": exc.code, "message": exc.message, "context": exc.context or {}})

    @app.exception_handler(HapeExternalError)
    async def _handle_external_error(_, exc: HapeExternalError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"code": exc.code, "message": exc.message, "context": exc.context or {}})

    @app.exception_handler(HapeOperationError)
    async def _handle_operation_error(_, exc: HapeOperationError) -> JSONResponse:
        return JSONResponse(status_code=500, content={"code": exc.code, "message": exc.message, "context": exc.context or {}})

    @app.exception_handler(HapeError)
    async def _handle_hape_error(_, exc: HapeError) -> JSONResponse:
        return JSONResponse(status_code=500, content={"code": exc.code, "message": exc.message, "context": exc.context or {}})

    @app.exception_handler(GitHubV2Error)
    async def _handle_github_v2(_, exc: GitHubV2Error) -> JSONResponse:
        return JSONResponse(status_code=exc.http_status, content={"code": exc.code, "message": exc.message})
