# AI IDE integration

## Purpose

Give Cursor, Codex, Claude Code, and other coding agents the HAPE Framework rules.

Canonical rules stay in [docs/llm](../llm/README.md).

IDE files must link to those rules instead of copying them in full.

## Choose your IDE

- [Automation context](automation-context.md)
- [Cursor](cursor.md)
- [Codex](codex.md)
- [Claude Code](claude-code.md)
- [AGENTS.md](agents-md.md)

## Templates

Copy from:

- `docs/ai-ide/templates/cursor/hape-framework.mdc`
- `docs/ai-ide/templates/codex/AGENTS.md`
- `docs/ai-ide/templates/claude-code/CLAUDE.md`
- `docs/ai-ide/templates/generic/AGENTS.md`

Do not overwrite existing project rules.

Merge the HAPE section, then verify the agent can read `docs/llm/README.md`.
