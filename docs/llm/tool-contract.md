# Minimal Tool Contract
A **tool** is any HAPE capability the agent can invoke via `hape <domain> <command>`.
This contract is for adding new tools and for making existing tools agent-safe.

## Required properties
- **Name**: stable, kebab-case CLI command path.
- **Purpose**: one sentence.
- **Inputs**: all inputs must be explicit CLI flags (no positional args).
- **Outputs**: deterministic stdout format (prefer JSON or clearly titled sections).
- **Side effects**: declared in docs + help (create/update/delete, uploads, deploys).

## Safety levels
- **read**: fetch/list/describe only.
- **write**: creates or updates.
- **delete**: destructive (delete, purge, rotate, apply, rollout).

## Error contract
- Services must raise `HapeValidationError` for bad input.
- Services must raise `HapeExternalError` for upstream/API failures.
- Errors must include: `code`, human message, and minimal context (no secrets).

## Idempotency and retries
- Prefer operations that are safe to reproduce or rerun (Idempotency).
- If retries are needed, implement them in services with backoff and clear logging.

## Logging
- Clients log request intent + status (no secrets).
- Services log orchestration steps and decisions.

## Documentation
For each new tool:
- add a page under `docs/cli/` with 1–2 examples
- document safety level, side effects, and required config/env
