from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

from botocore.exceptions import ClientError

from clients.aws_client import AwsClient
from core.errors.exceptions import HapeExternalError, HapeValidationError
from core.errors.messages.ecr_error_messages import get_ecr_error_message
from core.logging import LocalLogging


class EcrService:
    def __init__(
        self,
        aws_client: AwsClient | None = None,
        input_func: Callable[[str], str] | None = None,
    ) -> None:
        self.aws_client = aws_client or AwsClient()
        self.input_func = input_func or input
        self.logger = LocalLogging.get_logger("hape.ecr_service")

    @staticmethod
    def _prompt_yes_no(message: str, default_yes: bool = False, input_func: Callable[[str], str] = input) -> bool:
        default_label = "Y/n" if default_yes else "y/N"
        response = input_func(f"{message} [{default_label}]: ").strip().lower()
        if not response:
            return default_yes
        if response in {"y", "yes"}:
            return True
        if response in {"n", "no"}:
            return False
        return default_yes

    @staticmethod
    def _load_metadata(metadata_path: str) -> dict[str, Any]:
        path = Path(metadata_path).expanduser()
        if not path.exists():
            raise HapeValidationError(
                code="ECR_METADATA_NOT_FOUND",
                message=get_ecr_error_message("ECR_METADATA_NOT_FOUND", metadata_path=str(path)),
            )
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise HapeValidationError(
                code="ECR_METADATA_INVALID_JSON",
                message=get_ecr_error_message("ECR_METADATA_INVALID_JSON", metadata_path=str(path)),
            ) from exc
        if not isinstance(data, dict):
            raise HapeValidationError(
                code="ECR_METADATA_INVALID",
                message=get_ecr_error_message("ECR_METADATA_INVALID", reason="root must be an object"),
            )
        return data

    @staticmethod
    def _parse_services_filter(raw_services: str | None) -> set[str] | None:
        if raw_services is None:
            return None
        parsed = {item.strip() for item in raw_services.split(",") if item.strip()}
        if not parsed:
            raise HapeValidationError(
                code="ECR_METADATA_INVALID",
                message=get_ecr_error_message(
                    "ECR_METADATA_INVALID",
                    reason="--services was provided but no valid service names were found",
                ),
            )
        return parsed

    def _resolve_targets(
        self,
        metadata: dict[str, Any],
        services: str | None,
        region_override: str | None,
    ) -> tuple[str, str | None, list[dict[str, str]]]:
        registry = metadata.get("registry")
        if not isinstance(registry, dict):
            raise HapeValidationError(
                code="ECR_METADATA_INVALID",
                message=get_ecr_error_message("ECR_METADATA_INVALID", reason="registry must be an object"),
            )
        provider = str(registry.get("provider", "")).strip().lower()
        if provider != "ecr":
            raise HapeValidationError(
                code="ECR_PROVIDER_UNSUPPORTED",
                message=get_ecr_error_message("ECR_PROVIDER_UNSUPPORTED", provider=provider or "<empty>"),
            )
        region = (region_override or str(registry.get("region", "")).strip()).strip()
        if not region:
            raise HapeValidationError(
                code="ECR_REGION_REQUIRED",
                message=get_ecr_error_message("ECR_REGION_REQUIRED"),
            )
        expected_account = str(registry.get("account_id", "")).strip() or None

        services_raw = metadata.get("services")
        if not isinstance(services_raw, list) or not services_raw:
            raise HapeValidationError(
                code="ECR_METADATA_INVALID",
                message=get_ecr_error_message("ECR_METADATA_INVALID", reason="services must be a non-empty array"),
            )

        requested = self._parse_services_filter(services)
        known_names = {
            str(item.get("name", "")).strip()
            for item in services_raw
            if isinstance(item, dict) and str(item.get("name", "")).strip()
        }
        if requested is not None:
            unknown = sorted(name for name in requested if name not in known_names)
            if unknown:
                raise HapeValidationError(
                    code="ECR_SERVICES_UNKNOWN",
                    message=get_ecr_error_message("ECR_SERVICES_UNKNOWN", services=", ".join(unknown)),
                )

        targets: list[dict[str, str]] = []
        seen_repos: set[str] = set()
        for index, item in enumerate(services_raw):
            if not isinstance(item, dict):
                raise HapeValidationError(
                    code="ECR_METADATA_INVALID",
                    message=get_ecr_error_message(
                        "ECR_METADATA_INVALID",
                        reason=f"services[{index}] must be an object",
                    ),
                )
            name = str(item.get("name", "")).strip()
            if not name:
                raise HapeValidationError(
                    code="ECR_METADATA_INVALID",
                    message=get_ecr_error_message(
                        "ECR_METADATA_INVALID",
                        reason=f"services[{index}].name must be a non-empty string",
                    ),
                )
            if requested is not None and name not in requested:
                continue
            enabled = item.get("enabled", True)
            if not isinstance(enabled, bool):
                raise HapeValidationError(
                    code="ECR_METADATA_INVALID",
                    message=get_ecr_error_message(
                        "ECR_METADATA_INVALID",
                        reason=f"services[{index}].enabled must be a boolean when provided",
                    ),
                )
            if not enabled:
                continue
            ecr_repository = str(item.get("ecr_repository", "")).strip()
            if not ecr_repository:
                continue
            if ecr_repository in seen_repos:
                continue
            seen_repos.add(ecr_repository)
            targets.append({"service": name, "repository_name": ecr_repository})

        if not targets:
            raise HapeValidationError(
                code="ECR_REPOSITORIES_EMPTY",
                message=get_ecr_error_message("ECR_REPOSITORIES_EMPTY"),
            )
        return region, expected_account, targets

    def _build_plan(
        self,
        metadata_path: str,
        region: str,
        expected_account: str | None,
        targets: list[dict[str, str]],
        dry_run: bool,
        yes: bool,
    ) -> dict[str, Any]:
        caller_account: str | None = None
        try:
            caller_account = self.aws_client.get_caller_account_id() or None
        except Exception as exc:  # noqa: BLE001 - plan should still print without identity
            self.logger.warning("caller identity lookup failed: %s", exc)

        return {
            "metadata_path": str(Path(metadata_path).expanduser().resolve()),
            "provider": "ecr",
            "region": region,
            "expected_account_id": expected_account,
            "caller_account_id": caller_account,
            "account_match": (
                None
                if not expected_account or not caller_account
                else expected_account == caller_account
            ),
            "repositories": [item["repository_name"] for item in targets],
            "services": [item["service"] for item in targets],
            "dry_run": dry_run,
            "yes": yes,
            "actions": [
                "describe each ECR repository",
                "create repository only when missing",
                "never delete repositories",
            ],
            "notes": [
                "Uses the default AWS credential chain from the environment or shared config.",
                "Does not push images and does not change scan or lifecycle policies.",
            ],
        }

    def _print_plan(self, plan: dict[str, Any]) -> None:
        print("ECR ensure-repos plan (no secrets):")
        print(json.dumps(plan, indent=2, sort_keys=True))

    def ensure_repositories(
        self,
        metadata_path: str,
        services: str | None = None,
        region: str | None = None,
        dry_run: bool = False,
        yes: bool = False,
    ) -> dict[str, Any]:
        if not (metadata_path or "").strip():
            raise HapeValidationError(
                code="ECR_METADATA_REQUIRED",
                message=get_ecr_error_message("ECR_METADATA_REQUIRED"),
            )

        metadata = self._load_metadata(metadata_path=metadata_path)
        resolved_region, expected_account, targets = self._resolve_targets(
            metadata=metadata,
            services=services,
            region_override=region,
        )
        plan = self._build_plan(
            metadata_path=metadata_path,
            region=resolved_region,
            expected_account=expected_account,
            targets=targets,
            dry_run=dry_run,
            yes=yes,
        )
        self._print_plan(plan)

        if dry_run:
            return {
                "plan": plan,
                "executed": False,
                "created": [],
                "already_existed": [],
                "failed": [],
            }

        if not yes:
            if self.input_func is input and not sys.stdin.isatty():
                raise HapeValidationError(
                    code="ECR_ENSURE_CANCELLED",
                    message=get_ecr_error_message("ECR_ENSURE_CANCELLED"),
                )
            approved = self._prompt_yes_no(
                "Proceed with ECR ensure-repos?",
                default_yes=False,
                input_func=self.input_func,
            )
            if not approved:
                raise HapeValidationError(
                    code="ECR_ENSURE_CANCELLED",
                    message=get_ecr_error_message("ECR_ENSURE_CANCELLED"),
                )

        created: list[str] = []
        already_existed: list[str] = []
        failed: list[dict[str, str]] = []

        for target in targets:
            repository_name = target["repository_name"]
            try:
                existing = self.aws_client.describe_ecr_repository(
                    repository_name=repository_name,
                    region_name=resolved_region,
                )
            except ClientError as exc:
                failed.append({"repository_name": repository_name, "stage": "describe"})
                raise HapeExternalError(
                    code="ECR_DESCRIBE_FAILED",
                    message=get_ecr_error_message(
                        "ECR_DESCRIBE_FAILED",
                        repository_name=repository_name,
                        region=resolved_region,
                    ),
                ) from exc

            if existing is not None:
                already_existed.append(repository_name)
                self.logger.info("ECR repository already exists: %s", repository_name)
                continue

            try:
                created_repo = self.aws_client.create_ecr_repository(
                    repository_name=repository_name,
                    region_name=resolved_region,
                )
            except ClientError as exc:
                failed.append({"repository_name": repository_name, "stage": "create"})
                raise HapeExternalError(
                    code="ECR_CREATE_FAILED",
                    message=get_ecr_error_message(
                        "ECR_CREATE_FAILED",
                        repository_name=repository_name,
                        region=resolved_region,
                    ),
                ) from exc
            created.append(repository_name)
            uri = str(created_repo.get("repositoryUri", "")).strip()
            self.logger.info("Created ECR repository: %s (%s)", repository_name, uri or "uri-unavailable")

        result = {
            "plan": plan,
            "executed": True,
            "created": created,
            "already_existed": already_existed,
            "failed": failed,
        }
        print(json.dumps({k: v for k, v in result.items() if k != "plan"}, indent=2, sort_keys=True))
        return result


if __name__ == "__main__":
    print(EcrService)
