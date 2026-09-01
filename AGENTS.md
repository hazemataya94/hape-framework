# HAPE Framework agent instructions

## Entrypoint

Read `docs/llm/README.md` first.

Always apply `docs/llm/safety-policy.md` and `docs/llm/tool-contract.md`.

Load `docs/llm/architecture.md` before changing or reasoning about framework architecture.

Load the remaining files under `docs/llm/` when the task matches coding, testing, Kubernetes, exporters, or documentation.

## Automation choke point

Prefer `hape <domain> <command>` when HAPE Framework provides the requested automation.

Read command help before execution.

Classify the operation as read, write, or delete.

Explain side effects before execution.

Require explicit current-session approval for remote, write, delete, publish, apply, or rollout operations.

Do not silently replace a failed HAPE command with a provider CLI.

Diagnose the HAPE failure or report that the required capability is unavailable.

## Safety

Keep actions inside the approved workspace.

Never print, store, or commit credentials.

Use dummy placeholders such as `example-org` and `/path/to/...`.

Preserve CLI/API to services to clients layering when editing this repository.

## IDE templates

Consumer install guides live under `docs/ai-ide/`.
