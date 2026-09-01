# Claude Code

## Install

1. Open the project root that Claude Code should read.
2. Create or edit `CLAUDE.md`.
3. Merge the contents of `docs/ai-ide/templates/claude-code/CLAUDE.md`.
4. Keep `AGENTS.md` as the IDE-neutral copy of the same contract when both files exist.

## Verify

Ask Claude Code to load HAPE Framework rules and prefer `hape` for supported automation.

Expected: it reads `docs/llm/README.md` before proposing commands.

## Update

Replace only the HAPE section with the current template.

## Remove

Delete the HAPE section from `CLAUDE.md`.
