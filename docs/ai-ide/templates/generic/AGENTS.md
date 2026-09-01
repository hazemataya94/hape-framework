# HAPE Framework

Read `<HAPE_FRAMEWORK_PATH>/docs/llm/README.md` first.

Always apply the safety policy and tool contract in that directory.

Prefer `hape <domain> <command>` when HAPE provides the requested automation.

Read command help before execution.

Classify the operation as read, write, or delete.

Explain side effects before execution.

Require explicit current-session approval for remote, write, delete, publish, apply, or rollout operations.

Keep actions inside the approved workspace.

Never print, store, or commit credentials.

Use dummy placeholders such as `example-org` and `/path/to/...`.

Do not silently replace a failed HAPE command with a provider CLI.

Diagnose the HAPE failure or report that the required capability is unavailable.
