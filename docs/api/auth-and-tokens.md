# Auth And Tokens

## Token model
HAPE uses opaque bearer tokens.
Token values are generated once and stored hashed in a local JSON file.

- Store file: `HAPE_API_TOKENS_FILE` (default `~/.hape/api-tokens.json`)
- Token hashes are SHA-256.
- Plain token values are never stored.

## Prerequisites
Set an admin key in runtime config:

```bash
export HAPE_API_ADMIN_KEY='<YOUR_ADMIN_KEY>'
```

## Generate token

```bash
curl -s -X POST "http://localhost:8080/auth/tokens"   -H "Content-Type: application/json"   -H "X-Hape-Admin-Key: <YOUR_ADMIN_KEY>"   -d '{"name":"automation-bot"}'
```

Save the returned `token` securely.
HAPE returns token value only at creation time.

## List tokens

```bash
curl -s "http://localhost:8080/auth/tokens"   -H "X-Hape-Admin-Key: <YOUR_ADMIN_KEY>"
```

## Revoke token

```bash
curl -s -X POST "http://localhost:8080/auth/tokens/revoke"   -H "Content-Type: application/json"   -H "X-Hape-Admin-Key: <YOUR_ADMIN_KEY>"   -d '{"token_id":"<TOKEN_ID>"}'
```

## Use token on API calls

```bash
curl -s -X POST "http://localhost:8080/github/init-repo"   -H "Authorization: Bearer <API_TOKEN>"   -H "Content-Type: application/json"   -d '{"repo_path":"/path/to/repo","owner":"hape-vibes"}'
```

## Rate limit behavior
Each token is limited to `HAPE_API_RATE_LIMIT_PER_MINUTE` requests in a rolling 60-second window.
Default is 10.
When exceeded, API returns HTTP 429 with `Retry-After` header.
