# Vault CLI

## Purpose

Authenticate as the HAPE platform agent AppRole and read one Vault KV field.

Default CLI output is the field value on stdout so a caller such as `make publish` can capture it.

Use `--omit-value` in docs, tests, and interactive checks so the secret is not printed.

## Prerequisites

- `HAPE_VAULT_ROLE_ID` from the AppRole `role_id` output
- AppRole `secret_id` in `secret.id` (not in git)
- Target secret stored in Vault KV
- Real address and KV path set in config; shipped defaults are dummy placeholders

## Retrieve

Confirm retrieval without printing the secret:

```bash
hape vault kv-get --omit-value
```

Print the field value (caller capture only; do not paste this output into tickets, docs, or chat):

```bash
hape vault kv-get
```

`make publish` retrieves the token with `hape vault kv-get`, then uploads `dist/` with twine:

```bash
make publish
```

## Config keys

- `HAPE_WORKSPACE_ROOT` (directory that contains `secret.id`)
- `HAPE_VAULT_ADDR` (default `https://vault.example.com`)
- `HAPE_VAULT_ROLE_ID`
- `HAPE_VAULT_SECRET_ID_FILE` (override path to `secret.id`)
- `HAPE_VAULT_AUTH_PATH` (default `approle`)
- `HAPE_VAULT_KV_MOUNT` (default `kv`)
- `HAPE_VAULT_KV_PATH` (default `example/pypi`)
- `HAPE_VAULT_KV_FIELD` (default `token`)

Do not put `secret_id` or KV values in docs, git, or chat.
