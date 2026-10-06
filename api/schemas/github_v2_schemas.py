from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from services.github_provider.errors import GitHubV2Error
from services.github_provider.models import collect_forbidden_keys


class GitHubV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def reject_forbidden(cls, value: Any) -> Any:
        if collect_forbidden_keys(value):
            raise GitHubV2Error("policy_denied")
        return value


class ArtifactFile(GitHubV2Model):
    path: str
    mode: str = "100644"
    bytes: str | None = None
    hex_bytes: str | None = None


class GitHubV2Request(GitHubV2Model):
    authorization_grant: str
    idempotency_key: str = ""
    subject_id: str = ""
    operation_id: str
    destination_mode: str = ""
    target_binding_id: str = ""
    destination_id: str = ""
    repository_id: str = ""
    source_snapshot_digest: str = ""
    artifact_digest: str = ""
    expected_parent: str = ""
    collaborator_login: str = ""
    installation_id: int | None = None
    setup_state: str = ""
    code_verifier: str = ""
    receipt_id: str = ""
    files: list[ArtifactFile] = Field(default_factory=list)


if __name__ == "__main__":
    print(GitHubV2Request.__name__)
