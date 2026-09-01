# Five-minute quick start

## Purpose

Run one read-only command after a fresh install.

## Prerequisites

- [Installation](installation.md) completed.
- No remote credentials are required for this path.

## Steps

1. Confirm the CLI is on `PATH`:

```bash
hape --help
```

Expected: command groups such as `config`, `github`, `gitlab`, `vault`, and `kube-agent` appear.

2. Create a local config file if it does not exist:

```bash
hape config init-config-file
```

Safety level: `write`.

Side effects: creates or overwrites `~/.hape/config.json`.

3. Show the redacted config:

```bash
hape config show
```

Safety level: `read`.

Side effects: none.

Expected: JSON config values print with secrets redacted.

## Cleanup

No remote resources are created.

Delete `~/.hape/config.json` if you do not want a local config file.

## Related documentation

- [Configuration](configuration.md)
- [Safety basics](safety-basics.md)
- [Config command reference](../cli/config.md)
