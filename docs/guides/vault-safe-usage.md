# Vault safe usage

## Purpose

Retrieve one Vault KV field without logging the secret.

## Prerequisites

- Vault address such as `https://vault.example.com`.
- AppRole credentials supplied through config or environment.
- A KV path and field name.

## Retrieve a field

```bash
hape vault kv-get --mount kv --path example/app --field token --omit-value
```

Safety level: `read`.

Side effects: authenticates to Vault and reads one KV field.

`--omit-value` prevents printing the secret.

Without `--omit-value`, the command writes the retrieved field to stdout so a caller can capture it.

Do not log that value.

Do not paste retrieved secrets into docs, tickets, or git.

## Related documentation

- [Vault CLI](../cli/vault.md)
- [Vault service](../services/vault-service.md)
- [Safety policy](../llm/safety-policy.md)
