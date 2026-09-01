# AGENTS.md

## Purpose

`AGENTS.md` is the IDE-neutral entrypoint for coding agents.

This repository includes a root `AGENTS.md` for contributors working in HAPE Framework itself.

Other repositories should copy `docs/ai-ide/templates/generic/AGENTS.md`.

## Install in another repository

1. Copy the generic template into the other repository root, or merge it as a section.
2. Point `<HAPE_FRAMEWORK_PATH>` at a local clone when the agent needs the LLM rule files.
3. Confirm the agent can open `docs/llm/README.md` from that clone.

## Verify

Ask the agent what to do when `hape` fails.

Expected: diagnose or restore HAPE; do not silently fall back to `gh` or another provider CLI.

## Remove

Delete the HAPE section or the copied `AGENTS.md` file if it contains only HAPE guidance.
