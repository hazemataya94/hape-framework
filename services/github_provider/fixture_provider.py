from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from services.github_provider.canonical import sha256_hex
from services.github_provider.errors import GitHubV2Error


@dataclass
class FixtureGitHubProvider:
    UNKNOWN = "unknown"
    repositories: dict[str, dict[str, Any]] = field(default_factory=dict)
    refs: dict[str, str] = field(default_factory=dict)
    commits: dict[str, dict[str, Any]] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)
    installations: dict[int, dict[str, Any]] = field(default_factory=dict)
    next_repository_id: int = 1000
    next_fail: str | None = None

    def _maybe_fail(self) -> None:
        if self.next_fail == self.UNKNOWN:
            self.next_fail = None
            raise GitHubV2Error("operation_unknown")
        if self.next_fail == "provider_unavailable":
            self.next_fail = None
            raise GitHubV2Error("provider_unavailable")

    def seed_installation(self, installation_id: int, account_id: int, account_login: str, account_type: str) -> None:
        self.installations[installation_id] = {
            "id": installation_id,
            "account_id": account_id,
            "account_login": account_login,
            "account_type": account_type,
            "repository_selection": "selected",
            "permissions": {"contents": "write", "administration": "write"},
        }

    def get_installation(self, installation_id: int) -> dict[str, Any]:
        installation = self.installations.get(installation_id)
        if installation is None:
            raise GitHubV2Error("target_not_found")
        return dict(installation)

    def create_repository(self, owner_login: str, repository_name: str, account_id: int) -> dict[str, Any]:
        self._maybe_fail()
        if repository_name in self.repositories:
            raise GitHubV2Error("conflict")
        self.next_repository_id += 1
        record = {
            "provider_repository_id": self.next_repository_id,
            "owner_login": owner_login,
            "owner_account_id": account_id,
            "repository_name": repository_name,
            "visibility": "private",
            "collaborators": [],
            "exists": True,
        }
        self.repositories[repository_name] = record
        return dict(record)

    def add_collaborator(self, repository_name: str, login: str) -> None:
        self._maybe_fail()
        record = self.repositories.get(repository_name)
        if record is None:
            raise GitHubV2Error("repository_not_found")
        if login not in record["collaborators"]:
            record["collaborators"].append(login)

    def installation_can_access(self, installation_id: int, repository_name: str) -> bool:
        if installation_id not in self.installations:
            return False
        return repository_name in self.repositories and self.repositories[repository_name]["exists"]

    def get_ref(self, repository_name: str, ref_name: str) -> str | None:
        return self.refs.get(f"{repository_name}:{ref_name}")

    def create_commit(self, repository_name: str, parent: str | None, tree_digest: str, message: str) -> str:
        self._maybe_fail()
        if repository_name not in self.repositories:
            raise GitHubV2Error("repository_not_found")
        sha = sha256_hex(f"{repository_name}:{parent or ''}:{tree_digest}:{message}")[:40]
        self.commits[sha] = {"parent": parent, "tree": tree_digest, "message": message}
        return sha

    def update_ref(self, repository_name: str, ref_name: str, sha: str, expected_parent: str | None) -> None:
        self._maybe_fail()
        key = f"{repository_name}:{ref_name}"
        current = self.refs.get(key)
        if expected_parent is not None and current != expected_parent:
            raise GitHubV2Error("parent_mismatch")
        if expected_parent is None and current is not None:
            raise GitHubV2Error("conflict")
        self.refs[key] = sha

    def create_tag(self, repository_name: str, tag_name: str, sha: str) -> None:
        self._maybe_fail()
        key = f"{repository_name}:{tag_name}"
        if key in self.tags:
            raise GitHubV2Error("conflict")
        self.tags[key] = sha

    def delete_repository(self, repository_name: str) -> None:
        self._maybe_fail()
        record = self.repositories.get(repository_name)
        if record is None:
            raise GitHubV2Error("repository_not_found")
        record["exists"] = False

    def repository_exists(self, repository_name: str) -> bool:
        record = self.repositories.get(repository_name)
        return bool(record and record["exists"])


if __name__ == "__main__":
    provider = FixtureGitHubProvider()
    provider.seed_installation(1, 11, "example-org", "Organization")
    print(provider.get_installation(1)["account_login"])
