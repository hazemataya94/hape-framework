from __future__ import annotations

from fastapi import Depends, FastAPI
import uvicorn

from api.auth.rate_limiter import TokenRateLimiter
from api.auth.token_service import ApiTokenService
from api.dependencies import require_auth_token
from api.error_mapping import register_exception_handlers
from api.routers import auth_router, config_router, confluence_router, csv_router, dora_router, eks_deployment_cost_router, github_router, gitlab_router, health_router, init_cicd_router, jira_router, kube_agent_router, markdown_router
from core.config import Config
from core.logging import LocalLogging


def create_app() -> FastAPI:
    LocalLogging.bootstrap()
    app = FastAPI(title="HAPE API", version="1.0.0")
    app.state.token_service = ApiTokenService(store_file_path=Config.get_api_tokens_file_path())
    app.state.rate_limiter = TokenRateLimiter(limit_per_minute=Config.get_api_rate_limit_per_minute())
    app.state.api_admin_key = Config.get_api_admin_key()

    register_exception_handlers(app)

    app.include_router(health_router.router)
    app.include_router(auth_router.router)
    app.include_router(config_router.router, dependencies=[Depends(require_auth_token)])
    app.include_router(gitlab_router.router, dependencies=[Depends(require_auth_token)])
    app.include_router(github_router.router, dependencies=[Depends(require_auth_token)])
    app.include_router(jira_router.router, dependencies=[Depends(require_auth_token)])
    app.include_router(confluence_router.router, dependencies=[Depends(require_auth_token)])
    app.include_router(csv_router.router, dependencies=[Depends(require_auth_token)])
    app.include_router(markdown_router.router, dependencies=[Depends(require_auth_token)])
    app.include_router(dora_router.router, dependencies=[Depends(require_auth_token)])
    app.include_router(eks_deployment_cost_router.router, dependencies=[Depends(require_auth_token)])
    app.include_router(kube_agent_router.router, dependencies=[Depends(require_auth_token)])
    app.include_router(init_cicd_router.router, dependencies=[Depends(require_auth_token)])
    return app


def run() -> None:
    app = create_app()
    uvicorn.run(app, host=Config.get_api_host(), port=Config.get_api_port())


if __name__ == "__main__":
    run()
