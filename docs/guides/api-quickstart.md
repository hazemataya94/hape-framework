# API quick start

## Purpose

Start the local FastAPI process and create one bearer token.

## Prerequisites

- Local install from [installation](../getting-started/installation.md).
- `HAPE_API_ADMIN_KEY` set in the environment.

Default bind: `HAPE_API_HOST` and `HAPE_API_PORT`.

Documented default port is `8080`.

## Start the API

```bash
make run-api
```

Safety level: `write` for the local process only.

Side effects: starts a local HTTP server.

Production artifacts must not call `localhost` or `*.hape.local`.

## Create a token

```bash
curl -s -X POST "http://127.0.0.1:8080/auth/tokens" \
  -H "Content-Type: application/json" \
  -H "X-Hape-Admin-Key: <YOUR_ADMIN_KEY>" \
  -d '{"name":"automation-bot"}'
```

Safety level: `write`.

Side effects: creates a local API token record.

## Call a workflow endpoint

```bash
curl -s -X POST "http://127.0.0.1:8080/config/show" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Safety level: follows the matching CLI command.

## Related documentation

- [API index](../api/README.md)
- [Auth and tokens](../api/auth-and-tokens.md)
- [Parity mapping](../api/parity-mapping.md)
