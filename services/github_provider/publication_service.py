from __future__ import annotations

import secrets
from typing import Any

from services.github_provider.canonical import sha256_hex
from services.github_provider.errors import GitHubV2Error
from services.github_provider.fixture_provider import FixtureGitHubProvider
from services.github_provider.models import MAX_NAME_RETRIES, REPO_NAME_HEX_LENGTH, REPO_NAME_PREFIX, ManagedDestination, ManagedRepository
from repositories.sqlite_github_provider_repository import SqliteGitHubProviderRepository


class PublicationService:
    ALLOWED_MODES = {"100644", "100755"}

    def __init__(self, repository: SqliteGitHubProviderRepository, provider: FixtureGitHubProvider) -> None:
        self._repository = repository
        self._provider = provider
        self._snapshots: dict[tuple[str, str], list[dict[str, Any]]] = {}

    def _normalize_files(self, files: list[dict[str, Any]]) -> list[dict[str, Any]]:
        admitted: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in files:
            path = str(item.get("path") or "")
            mode = str(item.get("mode") or "100644")
            content = item.get("bytes")
            if not isinstance(content, (bytes, bytearray)):
                raise GitHubV2Error("digest_mismatch")
            if not path or ".." in path or path.startswith("/") or ".git" in path.split("/"):
                raise GitHubV2Error("digest_mismatch")
            if mode not in self.ALLOWED_MODES:
                raise GitHubV2Error("digest_mismatch")
            if path in seen:
                raise GitHubV2Error("digest_mismatch")
            seen.add(path)
            admitted.append({"path": path, "mode": mode, "bytes": bytes(content), "digest": sha256_hex(bytes(content))})
        admitted.sort(key=lambda item: item["path"])
        return admitted

    def _aggregate(self, files: list[dict[str, Any]]) -> str:
        lines = [f"{item['path']}\0{item['mode']}\0{len(item['bytes'])}\0{item['digest']}" for item in files]
        return sha256_hex("\n".join(lines) + "\n")

    def admit_files(self, files: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
        admitted = self._normalize_files(files)
        return admitted, self._aggregate(admitted)

    def store_snapshot(self, tenant_subject: str, digest: str, files: list[dict[str, Any]]) -> None:
        self._snapshots[(tenant_subject, digest)] = files

    def load_snapshot(self, tenant_subject: str, digest: str) -> list[dict[str, Any]]:
        files = self._snapshots.get((tenant_subject, digest))
        if files is None:
            raise GitHubV2Error("digest_mismatch")
        return files

    def generate_name(self) -> str:
        for _ in range(MAX_NAME_RETRIES):
            name = f"{REPO_NAME_PREFIX}{secrets.token_hex(REPO_NAME_HEX_LENGTH // 2)}"
            if self._repository.reserve_name(name):
                return name
        raise GitHubV2Error("conflict")

    def create_repository(self, destination: ManagedDestination, name: str, collaborator_login: str) -> dict[str, Any]:
        created = self._provider.create_repository(destination.account_login, name, destination.account_id)
        if destination.mode == "customer_personal":
            if not self._provider.installation_can_access(destination.installation_id, name):
                raise GitHubV2Error("custody_unconfirmed")
        if destination.mode == "hape_organization":
            if not collaborator_login:
                raise GitHubV2Error("invalid_resource_constraints")
            self._provider.add_collaborator(name, collaborator_login)
            record = self._provider.repositories.get(name) or {}
            if collaborator_login not in record.get("collaborators", []):
                raise GitHubV2Error("collaborator_failed")
        if str(created.get("visibility")) != "private":
            raise GitHubV2Error("target_mismatch")
        if str(created.get("owner_login")) != destination.account_login:
            raise GitHubV2Error("target_mismatch")
        return created

    def publish_commit(self, repository: ManagedRepository, tree_digest: str, message: str, parent: str | None) -> str:
        sha = self._provider.create_commit(repository.repository_name, parent, tree_digest, message)
        self._provider.update_ref(repository.repository_name, "refs/heads/main", sha, parent)
        current = self._provider.get_ref(repository.repository_name, "refs/heads/main")
        if current != sha:
            raise GitHubV2Error("parent_mismatch")
        return sha

    def current_parent(self, repository: ManagedRepository) -> str | None:
        return self._provider.get_ref(repository.repository_name, "refs/heads/main")

    def publish_tag(self, repository: ManagedRepository, tag_name: str, sha: str) -> None:
        self._provider.create_tag(repository.repository_name, tag_name, sha)

    def dispose(self, repository: ManagedRepository) -> None:
        self._provider.delete_repository(repository.repository_name)
        if self._provider.repository_exists(repository.repository_name):
            raise GitHubV2Error("disposal_blocked")


if __name__ == "__main__":
    print(PublicationService.ALLOWED_MODES)
