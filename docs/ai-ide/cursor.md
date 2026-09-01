# Cursor

## Install

1. Clone https://github.com/hazemataya94/hape-framework or add it as a sibling checkout.
2. Copy `docs/ai-ide/templates/cursor/hape-framework.mdc` to your project:

```text
.cursor/rules/hape-framework.mdc
```

3. If the rule needs a path to the HAPE clone, replace `<HAPE_FRAMEWORK_PATH>` with that local path.
4. Restart the Cursor agent session or start a new chat.

## Verify

Ask the agent to name the HAPE automation choke point and the LLM rule directory.

Expected: it cites `hape <domain> <command>` and `docs/llm/`.

## Update

Replace the copied `.mdc` file with the current template from this repository.

## Remove

Delete `.cursor/rules/hape-framework.mdc`.
