from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from services.github_provider.errors import GitHubV2Error
from services.github_provider.fixture_provider import FixtureGitHubProvider
from services.github_provider.models import DESTINATION_MODES, ManagedDestination
from repositories.sqlite_github_provider_repository import SqliteGitHubProviderRepository


class DestinationService:
    HAPE_REGISTRATION_ID = "hape-managed-repositories"
    CUSTOMER_REGISTRATION_ID = "customer-managed-repositories"
    SETUP_TTL_SECONDS = 600

    def __init__(self, repository: SqliteGitHubProviderRepository, provider: FixtureGitHubProvider, hape_organization: str = "example-org") -> None:
        self._repository = repository
        self._provider = provider
        self._hape_organization = hape_organization

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _stamp(self) -> str:
        return self._now().isoformat()

    def ensure_hape_destination(self) -> ManagedDestination:
        existing = self._repository.get_hape_destination()
        if existing is not None:
            return existing
        self._provider.seed_installation(1, 11, self._hape_organization, "Organization")
        destination = ManagedDestination(
            destination_id=str(uuid.uuid4()),
            mode="hape_organization",
            tenant_subject=None,
            registration_id=self.HAPE_REGISTRATION_ID,
            installation_id=1,
            account_id=11,
            account_login=self._hape_organization,
            account_type="Organization",
            repository_selection="selected",
            configuration_revision="1",
            permission_fingerprint="contents:write",
            status="active",
            verified_at=self._stamp(),
            last_observed_at=self._stamp(),
        )
        self._repository.upsert_destination(destination)
        return destination

    def status(self, destination_id: str) -> dict[str, Any]:
        destination = self._repository.get_destination(destination_id)
        if destination is None:
            raise GitHubV2Error("target_not_found")
        return {
            "destination_id": destination.destination_id,
            "mode": destination.mode,
            "account_login": destination.account_login,
            "account_type": destination.account_type,
            "status": destination.status,
        }

    def setup_url(self, tenant_subject: str, code_verifier: str = "") -> dict[str, Any]:
        state = secrets.token_urlsafe(32)
        verifier = code_verifier or secrets.token_urlsafe(32)
        challenge = hashlib.sha256(verifier.encode("utf-8")).hexdigest()
        expires_at = (self._now() + timedelta(seconds=self.SETUP_TTL_SECONDS)).isoformat()
        self._repository.put_setup_state(state, tenant_subject, challenge, expires_at)
        return {
            "setup_state": state,
            "code_verifier": verifier,
            "setup_url": f"https://github.example.com/apps/example-customer-managed/installations/new?state={state}",
        }

    def verify(self, tenant_subject: str, request: dict[str, Any]) -> ManagedDestination:
        mode = str(request.get("destination_mode") or "")
        if mode not in {"customer_organization", "customer_personal"}:
            raise GitHubV2Error("unsupported_destination_mode")
        state = str(request.get("setup_state") or "")
        challenge = self._repository.consume_setup_state(state, tenant_subject, self._stamp())
        if challenge is None:
            raise GitHubV2Error("policy_denied")
        expected = hashlib.sha256(str(request.get("code_verifier") or "").encode("utf-8")).hexdigest()
        if expected != challenge:
            raise GitHubV2Error("policy_denied")
        installation_id = int(request["installation_id"])
        installation = self._provider.get_installation(installation_id)
        expected_type = "Organization" if mode == "customer_organization" else "User"
        if installation["account_type"] != expected_type:
            raise GitHubV2Error("target_mismatch")
        occupied = self._repository.find_destination_by_installation(installation_id)
        if occupied is not None and occupied.tenant_subject != tenant_subject:
            raise GitHubV2Error("policy_denied")
        existing = self._repository.find_customer_destination(tenant_subject, installation_id)
        if existing is not None:
            return existing
        destination = ManagedDestination(
            destination_id=str(uuid.uuid4()),
            mode=mode,
            tenant_subject=tenant_subject,
            registration_id=self.CUSTOMER_REGISTRATION_ID,
            installation_id=installation_id,
            account_id=int(installation["account_id"]),
            account_login=str(installation["account_login"]),
            account_type=str(installation["account_type"]),
            repository_selection=str(installation["repository_selection"]),
            configuration_revision="1",
            permission_fingerprint="contents:write",
            status="active",
            verified_at=self._stamp(),
            last_observed_at=self._stamp(),
        )
        self._repository.upsert_destination(destination)
        return destination

    def resolve(self, tenant_subject: str, mode: str, target_binding_id: str | None) -> ManagedDestination:
        if mode not in DESTINATION_MODES:
            raise GitHubV2Error("unsupported_destination_mode")
        if mode == "hape_organization":
            destination = self.ensure_hape_destination()
            if target_binding_id and target_binding_id != destination.destination_id:
                raise GitHubV2Error("target_mismatch")
            return destination
        if not target_binding_id:
            raise GitHubV2Error("invalid_resource_constraints")
        destination = self._repository.get_destination(target_binding_id)
        if destination is None or destination.tenant_subject != tenant_subject:
            raise GitHubV2Error("target_not_found")
        if destination.mode != mode:
            raise GitHubV2Error("target_mismatch")
        if destination.status == "revoked":
            raise GitHubV2Error("target_revoked")
        if destination.status == "permission_drift":
            raise GitHubV2Error("permission_drift")
        if destination.status != "active":
            raise GitHubV2Error("target_not_found")
        return destination


if __name__ == "__main__":
    print(DestinationService.HAPE_REGISTRATION_ID)
