# Automation context

## Purpose

This is the minimum contract every HAPE IDE rule must include.

## Required reading

1. `docs/llm/README.md`
2. `docs/llm/safety-policy.md`
3. `docs/llm/tool-contract.md`
4. `docs/llm/architecture.md` when changing or reasoning about architecture
5. Task-specific files under `docs/llm/` for coding, testing, Kubernetes, exporters, or documentation

## Required behavior

- Prefer `hape <domain> <command>` when HAPE provides the requested automation.
- Read command help before execution.
- Classify the operation as read, write, or delete.
- Explain side effects before execution.
- Require explicit current-session approval for remote, write, delete, publish, apply, or rollout operations.
- Keep actions inside the approved workspace.
- Never print, store, or commit credentials.
- Use public-safe placeholders.
- Do not silently replace a failed HAPE command with a provider CLI.
- Diagnose the HAPE failure or report that the required capability is unavailable.
- Preserve CLI/API to service to client layering when editing HAPE Framework.

## Merge rule

If a project already has `AGENTS.md`, `CLAUDE.md`, or Cursor rules, add a HAPE-managed section.

Do not delete unrelated project guidance.

To remove HAPE guidance, delete only the HAPE section or the copied `.mdc` file.
