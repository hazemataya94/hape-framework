from __future__ import annotations


class GitHubV2Error(Exception):
    ERROR_HTTP = {
        "unauthorized": 401,
        "policy_denied": 403,
        "invalid_grant_signature": 401,
        "invalid_resource_constraints": 422,
        "grant_expired": 401,
        "grant_replayed": 403,
        "digest_mismatch": 409,
        "target_not_found": 404,
        "unsupported_destination_mode": 422,
        "target_mismatch": 409,
        "target_revoked": 403,
        "permission_drift": 409,
        "custody_unconfirmed": 409,
        "collaborator_failed": 409,
        "repository_not_found": 404,
        "parent_mismatch": 409,
        "conflict": 409,
        "provider_unavailable": 503,
        "rate_limited": 429,
        "operation_unknown": 409,
        "reconciliation_required": 409,
        "disposal_blocked": 409,
    }
    ERROR_MESSAGES = {
        "unauthorized": "A bearer token or local account is required.",
        "policy_denied": "The authenticated subject cannot perform this action.",
        "invalid_grant_signature": "The signed grant could not be verified.",
        "invalid_resource_constraints": "The resource constraints are invalid.",
        "grant_expired": "The authorization grant has expired.",
        "grant_replayed": "The authorization grant was already used.",
        "digest_mismatch": "The request digest does not match the sealed input.",
        "target_not_found": "The requested target was not found.",
        "unsupported_destination_mode": "The destination mode is not supported.",
        "target_mismatch": "The target does not match the signed grant.",
        "target_revoked": "The destination is revoked.",
        "permission_drift": "The destination permissions have drifted.",
        "custody_unconfirmed": "Installation custody is not confirmed.",
        "collaborator_failed": "The write collaborator could not be confirmed.",
        "repository_not_found": "The managed repository was not found.",
        "parent_mismatch": "The expected parent revision does not match.",
        "conflict": "The request conflicts with an existing operation.",
        "provider_unavailable": "The provider is temporarily unavailable.",
        "rate_limited": "The provider is rate limited. Retry later.",
        "operation_unknown": "The provider operation is unknown and must be reconciled.",
        "reconciliation_required": "Reconcile the unknown operation before retry.",
        "disposal_blocked": "Disposal cannot be completed.",
    }

    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        self.message = message or self.ERROR_MESSAGES.get(code, self.ERROR_MESSAGES["policy_denied"])
        self.http_status = self.ERROR_HTTP.get(code, 403)
        super().__init__(self.message)


if __name__ == "__main__":
    error = GitHubV2Error("policy_denied")
    print(error.code)
