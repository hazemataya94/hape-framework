# Safety basics

## Purpose

Classify HAPE commands before you run them.

A tool is any capability invoked as `hape <domain> <command>`.

## Safety levels

- `read`: fetch, list, describe, or show only.
- `write`: create or update.
- `delete`: destructive actions such as delete, purge, rotate, apply, or rollout.

## Before you run a command

1. Read `hape <domain> <command> --help`.
2. Identify required config keys.
3. Identify side effects.
4. Use dummy values in examples.
5. Require explicit approval for remote, write, delete, publish, apply, or rollout operations.

## Secrets

Never print, store, or commit tokens.

`hape vault kv-get` can write a secret field to stdout so a caller can capture it.

Use `--omit-value` in docs, tests, and interactive checks.

Do not log retrieved secret values.

## Dummy defaults

Use placeholders such as:

- `example-org`
- `/path/to/...`
- `https://vault.example.com`
- `<YOUR_TOKEN>`

Do not use real operator hosts, account IDs, or production endpoints as examples.

## AI agents

Give your AI IDE the HAPE LLM rules before asking it to run automation.

See [AI IDE integration](../ai-ide/README.md).

## Related documentation

- [Tool contract](../llm/tool-contract.md)
- [Safety policy](../llm/safety-policy.md)
- [CLI usage](../cli/cli.md)
