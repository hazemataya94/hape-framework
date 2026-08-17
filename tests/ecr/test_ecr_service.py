from __future__ import annotations

import json
from pathlib import Path

import pytest
from botocore.exceptions import ClientError

from core.errors.exceptions import HapeExternalError, HapeValidationError
from services.ecr_service import EcrService


class _FakeAwsClient:
    def __init__(self, existing: set[str] | None = None, account_id: str = "915610715996") -> None:
        self.existing = set(existing or set())
        self.account_id = account_id
        self.created: list[tuple[str, str]] = []
        self.describe_calls: list[tuple[str, str]] = []

    def get_caller_account_id(self) -> str:
        return self.account_id

    def describe_ecr_repository(self, repository_name: str, region_name: str) -> dict | None:
        self.describe_calls.append((repository_name, region_name))
        if repository_name in self.existing:
            return {"repositoryName": repository_name, "repositoryUri": f"example/{repository_name}"}
        return None

    def create_ecr_repository(self, repository_name: str, region_name: str) -> dict:
        self.created.append((repository_name, region_name))
        self.existing.add(repository_name)
        return {
            "repositoryName": repository_name,
            "repositoryUri": f"915610715996.dkr.ecr.{region_name}.amazonaws.com/{repository_name}",
        }


def _write_metadata(path: Path, *, include_backend: bool = True) -> Path:
    services = [
        {
            "name": "website",
            "enabled": True,
            "path": "hape-academy",
            "ecr_repository": "hape-academy-website",
            "depends_on": [],
        }
    ]
    if include_backend:
        services.append(
            {
                "name": "backend",
                "enabled": True,
                "path": "hape-academy/hape-academy-backend",
                "ecr_repository": "hape-academy-backend",
                "depends_on": [],
            }
        )
    payload = {
        "schema_version": "1.0",
        "system-name": "hape-academy",
        "registry": {
            "provider": "ecr",
            "region": "eu-central-1",
            "account_id": "915610715996",
        },
        "build": {"timeout_seconds": 1800, "fail_fast": True},
        "services": services,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_ensure_repositories_dry_run_prints_plan_without_create(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    metadata = _write_metadata(tmp_path / "meta.json")
    fake = _FakeAwsClient(existing=set())
    service = EcrService(aws_client=fake)  # type: ignore[arg-type]
    result = service.ensure_repositories(metadata_path=str(metadata), dry_run=True, yes=False)
    assert result["executed"] is False
    assert result["created"] == []
    assert fake.created == []
    assert fake.describe_calls == []
    captured = capsys.readouterr().out
    assert "ECR ensure-repos plan" in captured
    assert "hape-academy-website" in captured


def test_ensure_repositories_yes_creates_missing_and_skips_existing(tmp_path: Path) -> None:
    metadata = _write_metadata(tmp_path / "meta.json")
    fake = _FakeAwsClient(existing={"hape-academy-website"})
    service = EcrService(aws_client=fake)  # type: ignore[arg-type]
    result = service.ensure_repositories(metadata_path=str(metadata), yes=True)
    assert result["executed"] is True
    assert result["already_existed"] == ["hape-academy-website"]
    assert result["created"] == ["hape-academy-backend"]
    assert fake.created == [("hape-academy-backend", "eu-central-1")]


def test_ensure_repositories_services_filter(tmp_path: Path) -> None:
    metadata = _write_metadata(tmp_path / "meta.json")
    fake = _FakeAwsClient(existing=set())
    service = EcrService(aws_client=fake)  # type: ignore[arg-type]
    result = service.ensure_repositories(metadata_path=str(metadata), services="website", yes=True)
    assert result["created"] == ["hape-academy-website"]
    assert fake.created == [("hape-academy-website", "eu-central-1")]


def test_ensure_repositories_unknown_service_raises(tmp_path: Path) -> None:
    metadata = _write_metadata(tmp_path / "meta.json")
    service = EcrService(aws_client=_FakeAwsClient())  # type: ignore[arg-type]
    with pytest.raises(HapeValidationError) as error:
        service.ensure_repositories(metadata_path=str(metadata), services="nope", yes=True)
    assert error.value.code == "ECR_SERVICES_UNKNOWN"


def test_ensure_repositories_prompt_cancel(tmp_path: Path) -> None:
    metadata = _write_metadata(tmp_path / "meta.json")
    fake = _FakeAwsClient(existing=set())
    service = EcrService(aws_client=fake, input_func=lambda _: "n")  # type: ignore[arg-type]
    with pytest.raises(HapeValidationError) as error:
        service.ensure_repositories(metadata_path=str(metadata), yes=False)
    assert error.value.code == "ECR_ENSURE_CANCELLED"
    assert fake.created == []


def test_ensure_repositories_create_failure_raises(tmp_path: Path) -> None:
    metadata = _write_metadata(tmp_path / "meta.json", include_backend=False)

    class _FailingCreateClient(_FakeAwsClient):
        def create_ecr_repository(self, repository_name: str, region_name: str) -> dict:
            raise ClientError(
                {"Error": {"Code": "AccessDeniedException", "Message": "denied"}},
                "CreateRepository",
            )

    service = EcrService(aws_client=_FailingCreateClient())  # type: ignore[arg-type]
    with pytest.raises(HapeExternalError) as error:
        service.ensure_repositories(metadata_path=str(metadata), yes=True)
    assert error.value.code == "ECR_CREATE_FAILED"
