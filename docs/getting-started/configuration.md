# Configuration

## Purpose

Store optional integration values in `~/.hape/config.json` or environment variables.

## Default path

```text
~/.hape/config.json
```

Override the path per command:

```bash
hape --config-file-path /path/to/config.json config show
```

## Generate a file

```bash
hape config init-config-file
hape config init-config-file --dot-env-file /path/to/.env
```

Safety level: `write`.

Side effects: overwrites the target config file.

Prefer `hape config set` when you only need one key.

## Set one key

```bash
hape config set --key HAPE_GITHUB_DEFAULT_OWNER --value example-org
```

Safety level: `write`.

Side effects: updates one key in the target config file.

Do not paste live tokens into shell history, docs, or git.

## Show values

```bash
hape config show
```

Safety level: `read`.

Side effects: none.

`--reveal-secrets` prints secret values and is for local debugging only.

## Command keys

Commands fail only when they read a missing key.

Canonical key lists live in [config command reference](../cli/config.md).

## Related documentation

- [Safety basics](safety-basics.md)
- [API authentication](../api/auth-and-tokens.md)
- [Config command reference](../cli/config.md)
