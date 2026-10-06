from __future__ import annotations

import json
from typing import Any, Literal

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from api.dependencies import deny_product_legacy_github, get_github_app_service, require_github_operation
from api.schemas.github_v2_schemas import GitHubV2Request
from services.github_app_service import GitHubAppError, GitHubAppService
from services.github_service import GitHubService

router = APIRouter(prefix="/github", tags=["github"])


class InitRepoRequest(BaseModel):
    repo_path: str
    owner: str | None = None
    name: str | None = None
    visibility: str = "private"


class CreateRepoRequest(BaseModel):
    org: str
    name: str
    visibility: Literal["private", "public"] = "private"
    writeCollaboratorEmail: str = ""
    writeCollaboratorLogin: str = ""


class ListReposRequest(BaseModel):
    org: str | None = None
    include_archived: bool = False


class DeleteReposRequest(BaseModel):
    org: str
    include: list[str] | None = None
    exclude: list[str] | None = None
    delete_all: bool = False
    confirmation_phrase: str


class AuthorizationGrant(BaseModel):
    grantId: str
    iss: str
    aud: str
    sub: str
    tenantId: str
    appId: str
    operation: str
    resourceConstraints: dict[str, Any] = Field(default_factory=dict)
    inputDigest: str
    nonce: str
    iat: int
    exp: int
    decisionId: str
    expectedParent: str | None = None
    runId: str | None = None
    reviewId: str | None = None
    reviewDigest: str | None = None


class ProviderEnvelope(BaseModel):
    idempotencyKey: str
    grant: AuthorizationGrant


class VerifyInstallationRequest(ProviderEnvelope):
    authorizationCode: str
    codeVerifier: str
    installationId: int
    callbackUrl: str


class DiscoverRepositoriesRequest(ProviderEnvelope):
    page: int = 1


class ArtifactFile(BaseModel):
    path: str
    mode: str
    bytes: str | None = None
    hexBytes: str | None = None


class PublishArtifactRequest(ProviderEnvelope):
    files: list[ArtifactFile] = Field(default_factory=list)
    contentClass: str = "content_bearing"


def _error_response(exc: GitHubAppError) -> JSONResponse:
    return JSONResponse(status_code=exc.http_status, content={"code": exc.code, "message": exc.message})


def _parse_grant_header(x_hape_grant: str) -> dict[str, Any]:
    if not x_hape_grant:
        raise GitHubAppError("unauthorized")
    try:
        payload = json.loads(x_hape_grant)
    except json.JSONDecodeError as exc:
        raise GitHubAppError("policy_denied") from exc
    if not isinstance(payload, dict):
        raise GitHubAppError("policy_denied")
    return payload


def _artifact_files(items: list[ArtifactFile]) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for item in items:
        if item.hexBytes is not None:
            content = bytes.fromhex(item.hexBytes)
        else:
            content = (item.bytes or "").encode("utf-8")
        files.append({"path": item.path, "mode": item.mode, "bytes": content})
    return files


@router.post("/init-repo")
def init_repo(payload: InitRepoRequest, _: Any = Depends(deny_product_legacy_github)) -> dict[str, str]:
    service = GitHubService()
    return service.init_repo(repo_path=payload.repo_path, owner=payload.owner, name=payload.name, visibility=payload.visibility)


@router.post("/create/repo")
def create_repo(payload: CreateRepoRequest, _: Any = Depends(deny_product_legacy_github)) -> dict[str, Any]:
    service = GitHubService()
    return service.create_repository(
        org=payload.org,
        name=payload.name,
        visibility=payload.visibility,
        write_collaborator_email=payload.writeCollaboratorEmail,
        write_collaborator_login=payload.writeCollaboratorLogin,
    )


@router.post("/list-repos")
def list_repos(payload: ListReposRequest, _: Any = Depends(deny_product_legacy_github)) -> list[dict[str, Any]]:
    service = GitHubService()
    return service.list_repositories(org=payload.org, include_archived=payload.include_archived)


@router.post("/user-info")
def user_info(_: Any = Depends(deny_product_legacy_github)) -> dict[str, str]:
    service = GitHubService()
    return service.get_authenticated_user_info()


@router.post("/delete-repos")
def delete_repos(payload: DeleteReposRequest, _: Any = Depends(deny_product_legacy_github)) -> dict[str, Any]:
    service = GitHubService()
    return service.delete_repositories(
        org=payload.org,
        include=payload.include,
        exclude=payload.exclude,
        delete_all=payload.delete_all,
        confirmation_phrase=payload.confirmation_phrase,
    )


@router.post("/v1/installations/setup-url")
def setup_url(payload: ProviderEnvelope, _: Any = Depends(require_github_operation("installation.setup_url")), service: GitHubAppService = Depends(get_github_app_service)) -> Any:
    try:
        return service.create_setup_url(payload.grant.model_dump(), payload.idempotencyKey)
    except GitHubAppError as exc:
        return _error_response(exc)


@router.post("/v1/installations/verify")
def verify_installation(payload: VerifyInstallationRequest, _: Any = Depends(require_github_operation("installation.verify")), service: GitHubAppService = Depends(get_github_app_service)) -> Any:
    try:
        return service.verify_installation(
            payload.grant.model_dump(),
            payload.idempotencyKey,
            payload.authorizationCode,
            payload.codeVerifier,
            payload.installationId,
            payload.callbackUrl,
        )
    except GitHubAppError as exc:
        return _error_response(exc)


@router.get("/v1/installations/{installationId}/status")
def installation_status(installationId: int, x_hape_grant: str = Header(default=""), _: Any = Depends(require_github_operation("installation.status")), service: GitHubAppService = Depends(get_github_app_service)) -> Any:
    try:
        return service.get_installation_status(_parse_grant_header(x_hape_grant), installationId)
    except GitHubAppError as exc:
        return _error_response(exc)


@router.post("/v1/repositories/discover")
def discover_repositories(payload: DiscoverRepositoriesRequest, _: Any = Depends(require_github_operation("repository.discover")), service: GitHubAppService = Depends(get_github_app_service)) -> Any:
    try:
        return service.discover_repositories(payload.grant.model_dump(), payload.idempotencyKey, payload.page)
    except GitHubAppError as exc:
        return _error_response(exc)


@router.post("/v1/revisions/resolve")
def resolve_revision(payload: ProviderEnvelope, _: Any = Depends(require_github_operation("revision.resolve")), service: GitHubAppService = Depends(get_github_app_service)) -> Any:
    try:
        return service.resolve_revision(payload.grant.model_dump(), payload.idempotencyKey)
    except GitHubAppError as exc:
        return _error_response(exc)


@router.post("/v1/snapshots/read")
def read_snapshot(payload: ProviderEnvelope, _: Any = Depends(require_github_operation("snapshot.read")), service: GitHubAppService = Depends(get_github_app_service)) -> Any:
    try:
        return service.read_snapshot(payload.grant.model_dump(), payload.idempotencyKey)
    except GitHubAppError as exc:
        return _error_response(exc)


@router.post("/v1/repositories")
def create_private_repository(payload: ProviderEnvelope, _: Any = Depends(require_github_operation("repository.create_private")), service: GitHubAppService = Depends(get_github_app_service)) -> Any:
    try:
        return service.create_private_repository(payload.grant.model_dump(), payload.idempotencyKey)
    except GitHubAppError as exc:
        return _error_response(exc)


@router.post("/v1/commits/baseline")
def publish_baseline(payload: ProviderEnvelope, _: Any = Depends(require_github_operation("commit.publish_baseline")), service: GitHubAppService = Depends(get_github_app_service)) -> Any:
    try:
        return service.publish_baseline(payload.grant.model_dump(), payload.idempotencyKey)
    except GitHubAppError as exc:
        return _error_response(exc)


@router.post("/v1/commits/artifact")
def publish_artifact(payload: PublishArtifactRequest, _: Any = Depends(require_github_operation("commit.publish_artifact")), service: GitHubAppService = Depends(get_github_app_service)) -> Any:
    try:
        return service.publish_artifact(payload.grant.model_dump(), payload.idempotencyKey, _artifact_files(payload.files), payload.contentClass)
    except GitHubAppError as exc:
        return _error_response(exc)


@router.post("/v1/tags")
def publish_tag(payload: ProviderEnvelope, _: Any = Depends(require_github_operation("tag.publish_annotated")), service: GitHubAppService = Depends(get_github_app_service)) -> Any:
    try:
        return service.publish_annotated_tag(payload.grant.model_dump(), payload.idempotencyKey)
    except GitHubAppError as exc:
        return _error_response(exc)


@router.post("/v1/repositories/dispose")
def dispose_repository(payload: ProviderEnvelope, _: Any = Depends(require_github_operation("repository.dispose")), service: GitHubAppService = Depends(get_github_app_service)) -> Any:
    try:
        return service.dispose_repository(payload.grant.model_dump(), payload.idempotencyKey)
    except GitHubAppError as exc:
        return _error_response(exc)


@router.get("/v1/receipts/{receiptId}")
def get_receipt(receiptId: str, x_hape_grant: str = Header(default=""), _: Any = Depends(require_github_operation("receipt.get")), service: GitHubAppService = Depends(get_github_app_service)) -> Any:
    try:
        return service.get_receipt(_parse_grant_header(x_hape_grant), receiptId)
    except GitHubAppError as exc:
        return _error_response(exc)


_V2_DEST_STATUS = require_github_operation("managed_destination.status")
_V2_TARGET_SETUP = require_github_operation("managed_target.setup_url")
_V2_TARGET_VERIFY = require_github_operation("managed_target.verify")
_V2_TARGET_STATUS = require_github_operation("managed_target.status")
_V2_CREATE = require_github_operation("managed_repository.create_private")
_V2_BASELINE = require_github_operation("managed_repository.publish_baseline")
_V2_ARTIFACT = require_github_operation("managed_repository.publish_artifact")
_V2_TAG = require_github_operation("managed_repository.publish_tag")
_V2_DISPOSE = require_github_operation("managed_repository.dispose")
_V2_OPERATION = require_github_operation("provider_operation.get")
_V2_RECEIPT = require_github_operation("provider_receipt.get")


def _v2_dump(payload: GitHubV2Request) -> dict[str, Any]:
    data = payload.model_dump()
    files = []
    for item in payload.files:
        entry = {"path": item.path, "mode": item.mode}
        if item.hex_bytes:
            entry["hex_bytes"] = item.hex_bytes
        elif item.bytes is not None:
            entry["bytes"] = item.bytes
        files.append(entry)
    data["files"] = files
    return data


def _v2_result(result: dict[str, Any]) -> Any:
    if result.get("status") == "unknown":
        return JSONResponse(status_code=409, content=result)
    return result


@router.get("/v2/managed-destinations/{destination_id}/status")
def v2_destination_status(destination_id: str, request: Request, x_hape_grant: str = Header(default=""), _: Any = Depends(_V2_DEST_STATUS)) -> Any:
    body = {"authorization_grant": x_hape_grant, "destination_id": destination_id}
    return request.app.state.github_v2_service.destination_status(body)


@router.post("/v2/managed-targets/setup-url")
def v2_target_setup_url(payload: GitHubV2Request, request: Request, _: Any = Depends(_V2_TARGET_SETUP)) -> Any:
    return _v2_result(request.app.state.github_v2_service.target_setup_url(_v2_dump(payload)))


@router.post("/v2/managed-targets/verify")
def v2_target_verify(payload: GitHubV2Request, request: Request, _: Any = Depends(_V2_TARGET_VERIFY)) -> Any:
    return _v2_result(request.app.state.github_v2_service.target_verify(_v2_dump(payload)))


@router.get("/v2/managed-targets/{target_binding_id}/status")
def v2_target_status(target_binding_id: str, request: Request, destination_mode: str = "", x_hape_grant: str = Header(default=""), _: Any = Depends(_V2_TARGET_STATUS)) -> Any:
    body = {"authorization_grant": x_hape_grant, "target_binding_id": target_binding_id, "destination_mode": destination_mode}
    return request.app.state.github_v2_service.target_status(body)


@router.post("/v2/managed-repositories")
def v2_create_private(payload: GitHubV2Request, request: Request, _: Any = Depends(_V2_CREATE)) -> Any:
    return _v2_result(request.app.state.github_v2_service.create_private(_v2_dump(payload)))


@router.post("/v2/managed-repositories/{repository_id}/commits/baseline")
def v2_publish_baseline(repository_id: str, payload: GitHubV2Request, request: Request, _: Any = Depends(_V2_BASELINE)) -> Any:
    body = _v2_dump(payload)
    body["repository_id"] = repository_id
    return _v2_result(request.app.state.github_v2_service.publish_baseline(body))


@router.post("/v2/managed-repositories/{repository_id}/commits/artifact")
def v2_publish_artifact(repository_id: str, payload: GitHubV2Request, request: Request, _: Any = Depends(_V2_ARTIFACT)) -> Any:
    body = _v2_dump(payload)
    body["repository_id"] = repository_id
    return _v2_result(request.app.state.github_v2_service.publish_artifact(body))


@router.post("/v2/managed-repositories/{repository_id}/tags")
def v2_publish_tag(repository_id: str, payload: GitHubV2Request, request: Request, _: Any = Depends(_V2_TAG)) -> Any:
    body = _v2_dump(payload)
    body["repository_id"] = repository_id
    return _v2_result(request.app.state.github_v2_service.publish_tag(body))


@router.post("/v2/managed-repositories/{repository_id}/dispose")
def v2_dispose(repository_id: str, payload: GitHubV2Request, request: Request, _: Any = Depends(_V2_DISPOSE)) -> Any:
    body = _v2_dump(payload)
    body["repository_id"] = repository_id
    return _v2_result(request.app.state.github_v2_service.dispose(body))


@router.get("/v2/provider-operations/{operation_id}")
def v2_get_operation(operation_id: str, request: Request, x_hape_grant: str = Header(default=""), _: Any = Depends(_V2_OPERATION)) -> Any:
    body = {"authorization_grant": x_hape_grant, "operation_id": operation_id}
    return request.app.state.github_v2_service.get_operation(body)


@router.get("/v2/provider-receipts/{receipt_id}")
def v2_get_receipt(receipt_id: str, request: Request, x_hape_grant: str = Header(default=""), _: Any = Depends(_V2_RECEIPT)) -> Any:
    body = {"authorization_grant": x_hape_grant, "receipt_id": receipt_id}
    return request.app.state.github_v2_service.get_receipt(body)
