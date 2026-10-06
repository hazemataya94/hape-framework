from __future__ import annotations

from typing import Any

from services.github_provider.errors import GitHubV2Error
from services.github_provider.fixture_provider import FixtureGitHubProvider
from services.github_provider.models import ManagedRepository, ProviderOperation
from repositories.sqlite_github_provider_repository import SqliteGitHubProviderRepository


class ReconciliationService:
    def __init__(self, repository: SqliteGitHubProviderRepository, provider: FixtureGitHubProvider) -> None:
        self._repository = repository
        self._provider = provider

    def inspect(self, operation: ProviderOperation, managed: ManagedRepository | None) -> dict[str, Any]:
        marker = operation.provider_marker
        if operation.operation == "managed_repository.create_private":
            exists = self._provider.repository_exists(marker)
            return {"confirmed": exists, "absent": not exists, "marker": marker}
        if operation.operation in {"managed_repository.publish_baseline", "managed_repository.publish_artifact"}:
            if managed is None:
                raise GitHubV2Error("repository_not_found")
            current = self._provider.get_ref(managed.repository_name, "refs/heads/main")
            return {"confirmed": current == marker, "absent": current is None, "marker": current or ""}
        if operation.operation == "managed_repository.publish_tag":
            if managed is None:
                raise GitHubV2Error("repository_not_found")
            key = f"{managed.repository_name}:{marker}"
            present = key in self._provider.tags
            return {"confirmed": present, "absent": not present, "marker": marker}
        if operation.operation == "managed_repository.dispose":
            if managed is None:
                return {"confirmed": True, "absent": True, "marker": marker}
            exists = self._provider.repository_exists(managed.repository_name)
            return {"confirmed": not exists, "absent": not exists, "marker": marker}
        raise GitHubV2Error("operation_unknown")


if __name__ == "__main__":
    print(ReconciliationService)
