# GitHub App provider

## Purpose

HAPE Framework exposes a generic GitHub provider boundary for technically read-only source access and HAPE-managed snapshot repositories.

Product callers receive redacted receipts only.

Provider credentials never leave Framework.

## Prerequisites

A product caller token must include `iss=hape-platform-agent-backend`, `aud=hape-framework`, `sub=hape-platform-agent-backend`, `credential_role`, and `allowed_operations`.

Each request must also include a single-use authorization grant issued to Framework.

App registrations resolve from an in-memory sink in tests, or from a Vault KV sink when a reader is supplied.

The dummy path identities are `secret/example-org/framework/hape-framework/{environment}/github-apps/source-import` and `secret/example-org/framework/hape-framework/{environment}/github-apps/managed-repositories`. `{environment}` defaults to `dev`.

Required source-import fields are `app_id`, `client_id`, `client_secret`, `slug`, `private_key_pem`, and `expected_permissions`. Required managed-repositories fields are `app_id`, `private_key_pem`, `expected_permissions`, and `organization_allowlist`.

This path does not read `HAPE_GITHUB_TOKEN`, Platform Agent `GITHUB_LIVE_ENABLED`, config files, dotenv GitHub credentials, GitHub CLI, or SSH material.

The default provider API URL is `https://api.github.example.com`. The default OAuth host is `https://github.example.com`. `HAPE_GITHUB_APP_LIVE_ENABLED` must be `true` to use `https://api.github.com` and `https://github.com`.

`installation.setup_url` appends a backend-generated `setupState` and returns the public `clientId`. Framework does not generate browser-facing state.

`installation.verify` exchanges an OAuth authorization code with PKCE, requires `GET /user` plus a paginated exact match on `GET /user/installations`, inspects the installation with an App JWT, and only then mints an installation token. User access and refresh tokens are discarded. Authorization codes and PKCE verifiers never appear in receipts.

## Bounded operations

| Operation | Method and path | Role |
| --- | --- | --- |
| `installation.setup_url` | `POST /github/v1/installations/setup-url` | source-read |
| `installation.verify` | `POST /github/v1/installations/verify` | source-read |
| `installation.status` | `GET /github/v1/installations/{installationId}/status` | source-read |
| `repository.discover` | `POST /github/v1/repositories/discover` | source-read |
| `revision.resolve` | `POST /github/v1/revisions/resolve` | source-read |
| `snapshot.read` | `POST /github/v1/snapshots/read` | source-read |
| `repository.create_private` | `POST /github/v1/repositories` | managed-write |
| `commit.publish_baseline` | `POST /github/v1/commits/baseline` | managed-write |
| `commit.publish_artifact` | `POST /github/v1/commits/artifact` | managed-write |
| `tag.publish_annotated` | `POST /github/v1/tags` | managed-write |
| `repository.dispose` | `POST /github/v1/repositories/dispose` | managed-write |
| `receipt.get` | `GET /github/v1/receipts/{receiptId}` | source-read or managed-write |

`/github/v2` is the selectable-destination contract. It accepts a compact signed grant, opaque `subject_id` and `operation_id`, and returns `github.v2` snake_case receipts. v2 does not fall back to v1 and does not use v1 in-memory ledgers.

| Operation | Method and path | Role |
| --- | --- | --- |
| `managed_destination.status` | `GET /github/v2/managed-destinations/{destination_id}/status` | managed-write |
| `managed_target.setup_url` | `POST /github/v2/managed-targets/setup-url` | managed-write |
| `managed_target.verify` | `POST /github/v2/managed-targets/verify` | managed-write |
| `managed_target.status` | `GET /github/v2/managed-targets/{target_binding_id}/status` | managed-write |
| `managed_repository.create_private` | `POST /github/v2/managed-repositories` | managed-write |
| `managed_repository.publish_baseline` | `POST /github/v2/managed-repositories/{repository_id}/commits/baseline` | managed-write |
| `managed_repository.publish_artifact` | `POST /github/v2/managed-repositories/{repository_id}/commits/artifact` | managed-write |
| `managed_repository.publish_tag` | `POST /github/v2/managed-repositories/{repository_id}/tags` | managed-write |
| `managed_repository.dispose` | `POST /github/v2/managed-repositories/{repository_id}/dispose` | managed-write |
| `provider_operation.get` | `GET /github/v2/provider-operations/{operation_id}` | managed-write |
| `provider_receipt.get` | `GET /github/v2/provider-receipts/{receipt_id}` | managed-write |

v2 grants are compact RS256 JWTs. `resource_constraints` allows only `destination_mode`, `target_binding_id`, `repository_id`, `collaborator_login`, `artifact_digest`, and `expected_parent`.

Generated v2 repository names match `hape-mgr-` plus 16 lowercase hex characters. Receipts use envelope version `github.v2`.

GET routes accept the grant in the `X-Hape-Grant` header.

POST routes accept `idempotencyKey` and `grant` in the JSON body.

`POST /github/v1/installations/verify` also requires `authorizationCode`, `codeVerifier`, `installationId`, and `callbackUrl`. The grant `resourceConstraints.installationId` must match the body `installationId`.

## Authorization

Admin `POST /auth/tokens` can mint exactly one product role, `source-read` or `managed-write`, with the frozen operation allowlist for that role. Product caller tokens expire. The default TTL is seven days. Operator tokens without `credential_role` keep the existing name-only behavior.

A valid Framework bearer token does not inherit legacy GitHub routes.

Product `source-read` and `managed-write` tokens receive `403 policy_denied` on `POST /github/init-repo`, `POST /github/create/repo`, `POST /github/list-repos`, `POST /github/user-info`, and `POST /github/delete-repos`.

Operator tokens without a product credential role keep the existing legacy behavior.

Route dependencies require the exact operation claim before service code runs.

Source-read cannot create, commit, tag, or dispose.

Managed-write cannot read customer source, discover customer repositories, or resolve customer revisions.

## Provider transport

`GitHubAppClient` sends GitHub HTTPS API calls with an in-memory `Authorization` header.

Tokens do not appear in URLs, process arguments, files, or receipts.

Publication uses the Git Data API.

No provider publication path shells out to Git.

Managed repositories are created only in the configured allowlist organization `example-org`.

`repository.create_private` requires `writeCollaboratorEmail` or
`writeCollaboratorLogin` in the grant constraints. Framework prefers the
supplied login, otherwise resolves the email, then adds `permission=push`.
Create fails closed if the grant cannot be applied.

Generated repository names match `hape-mc-[a-z0-9]{8}`.

Generated tags match `hape-pub-[a-f0-9]{32}-[a-f0-9]{8}` and are annotated and unique.

## Snapshot admission

Canonical retrieval walks commit, tree, and blob objects.

Truncated recursive trees fall back to a bounded individual-tree walk.

Paths are UTF-8 NFC, sorted by UTF-8 path bytes, and limited to modes `100644` and `100755`.

Admission fails closed on traversal, `.git`, symlinks, submodules, LFS pointers, case collisions, NFC mismatch, size limits, and high-confidence secrets.

The aggregate digest is SHA-256 over `path NUL mode NUL decimal-size NUL per-file-sha256-hex LF`.

Receipts return the digest and never return source bodies.

## Receipts and idempotency

Receipts use envelope version `1.20.0` and include `receiptId`, `operation`, `subject`, `resourceIds`, `inputDigest`, `outputDigest`, `status`, `issuedAt`, `completedAt`, `safeProviderIds`, `retryClass`, and `customerSafeErrorCode`.

The same tenant, subject, operation, and idempotency key with the same request hash replays the original receipt.

A different hash on the same key returns `409 conflict` and does not mutate.

## Validation

From the repository root:

```sh
python -m pytest tests/github/test_github_app_client.py tests/github/test_github_app_snapshot.py tests/github/test_github_app_service.py tests/github/test_github_app_vault_sink.py tests/github/test_github_app_auth.py tests/github/test_github_v2_grants.py tests/github/test_github_v2_destinations.py tests/github/test_github_v2_publication.py tests/github/test_github_v2_persistence.py tests/github/test_github_v2_reconciliation.py tests/api/test_api_auth_and_parity.py tests/api/test_github_v2_api.py tests/cli/test_github_v2_commands.py tests/vault/test_vault_client.py
```

Expected outcome: fixture-backed tests pass with no live GitHub, Vault, or Git subprocess.

## Rollback

Disable product caller access to `/github/v1` while retaining stored redacted receipts.

Do not fall back to `HAPE_GITHUB_TOKEN` or legacy destructive GitHub routes for product callers.
