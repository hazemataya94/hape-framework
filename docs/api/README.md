# API Documentation

## Purpose
This directory documents the HAPE FastAPI interface, token auth, and CLI parity contracts.

## Run API
```bash
make run-api
```

The API binds to `HAPE_API_HOST` and `HAPE_API_PORT`.
Default host is `0.0.0.0`.

## Authentication
All workflow endpoints require bearer token auth.
Auth token management endpoints require `X-Hape-Admin-Key`.

- Token issuance: `POST /auth/tokens`
- Token listing: `GET /auth/tokens`
- Token revoke: `POST /auth/tokens/revoke`

See [auth-and-tokens.md](auth-and-tokens.md) for token operations.

## Rate limiting
Each API token is limited to 10 requests per minute by default.
Set `HAPE_API_RATE_LIMIT_PER_MINUTE` to override.

## Parity contract
Endpoint paths follow strict 1:1 CLI parity naming.
See [parity-mapping.md](parity-mapping.md).

## OpenAPI
OpenAPI contract lives at `docs/api/openapi.yaml`.
