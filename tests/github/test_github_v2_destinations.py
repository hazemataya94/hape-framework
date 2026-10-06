from __future__ import annotations

import pytest

from services.github_provider.errors import GitHubV2Error
from tests.github.github_v2_support import build_service, signed_request


def test_hape_destination_is_created_once() -> None:
    service, _provider, _private, _public = build_service()
    first = service._destinations.ensure_hape_destination()
    second = service._destinations.ensure_hape_destination()
    assert first.destination_id == second.destination_id
    assert first.mode == "hape_organization"
    assert first.account_login == "example-org"


def test_customer_organization_and_personal_bindings() -> None:
    service, _provider, private_pem, _public = build_service()
    setup = signed_request(service, private_pem, "managed_target.setup_url", {"idempotency_key": "setup-org", "code_verifier": "verifier-org"})
    setup_receipt = service.target_setup_url(setup)
    verify = signed_request(
        service,
        private_pem,
        "managed_target.verify",
        {
            "idempotency_key": "verify-org",
            "destination_mode": "customer_organization",
            "setup_state": setup_receipt["setup_state"],
            "code_verifier": "verifier-org",
            "installation_id": 201,
        },
    )
    org = service.target_verify(verify)
    assert org["safe_provider_ids"]["mode"] == "customer_organization"
    personal_setup = signed_request(service, private_pem, "managed_target.setup_url", {"idempotency_key": "setup-user", "code_verifier": "verifier-user"})
    personal_receipt = service.target_setup_url(personal_setup)
    personal = signed_request(
        service,
        private_pem,
        "managed_target.verify",
        {
            "idempotency_key": "verify-user",
            "destination_mode": "customer_personal",
            "setup_state": personal_receipt["setup_state"],
            "code_verifier": "verifier-user",
            "installation_id": 301,
        },
    )
    user = service.target_verify(personal)
    assert user["safe_provider_ids"]["mode"] == "customer_personal"
    assert org["safe_provider_ids"]["destination_id"] != user["safe_provider_ids"]["destination_id"]


def test_customer_installation_cannot_bind_two_tenants() -> None:
    service, _provider, private_pem, _public = build_service()
    setup = signed_request(service, private_pem, "managed_target.setup_url", {"idempotency_key": "setup-one", "code_verifier": "verifier-one"})
    setup_receipt = service.target_setup_url(setup)
    verify = signed_request(
        service,
        private_pem,
        "managed_target.verify",
        {
            "idempotency_key": "verify-one",
            "destination_mode": "customer_organization",
            "setup_state": setup_receipt["setup_state"],
            "code_verifier": "verifier-one",
            "installation_id": 201,
        },
    )
    service.target_verify(verify)
    other_setup = service._destinations.setup_url("other-tenant", "verifier-two")
    with pytest.raises(GitHubV2Error) as raised:
        service._destinations.verify("other-tenant", {"destination_mode": "customer_organization", "setup_state": other_setup["setup_state"], "code_verifier": "verifier-two", "installation_id": 201})
    assert raised.value.code == "policy_denied"


def test_wrong_account_type_fails() -> None:
    service, _provider, private_pem, _public = build_service()
    setup = signed_request(service, private_pem, "managed_target.setup_url", {"idempotency_key": "setup-mismatch", "code_verifier": "verifier-mismatch"})
    setup_receipt = service.target_setup_url(setup)
    verify = signed_request(
        service,
        private_pem,
        "managed_target.verify",
        {
            "idempotency_key": "verify-mismatch",
            "destination_mode": "customer_personal",
            "setup_state": setup_receipt["setup_state"],
            "code_verifier": "verifier-mismatch",
            "installation_id": 201,
        },
    )
    with pytest.raises(GitHubV2Error) as raised:
        service.target_verify(verify)
    assert raised.value.code == "target_mismatch"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
