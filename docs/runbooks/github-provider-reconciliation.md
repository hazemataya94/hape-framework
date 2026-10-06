# GitHub provider reconciliation

## Purpose

Recover `/github/v2` operations that left the durable ledger in `unknown` after an ambiguous fixture or provider outcome.

## When to use

Use this runbook when a `github.v2` receipt has `status=unknown` and `retry_class=reconcile_then_retry`.

Do not retry the original mutation until reconciliation completes.

## Procedure

1. Read the operation with `hape github v2 provider-operation get --request-file-path /path/to/operation.json`.
2. Confirm `state` is `unknown` and note `operation_id` plus `retry_class`.
3. Ask Framework to reconcile through `GET /github/v2/provider-operations/{operation_id}` after the service inspects the reserved provider marker.
4. If the receipt status becomes `reconciled`, the stored result may be reused with the same idempotency key and hash.
5. If confirmation is impossible, `retry_class` becomes `manual` and an operator must inspect the reserved repository name, ref, or tag.

## Safety

- Reconcile by the reserved generated name, commit marker, or tag only.
- Do not enumerate customer repositories.
- Do not treat a timeout as success.
- Do not start Compose, kind, Vault, or a live GitHub operation from this runbook.
