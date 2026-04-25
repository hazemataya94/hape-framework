# Configuration

## Overview
Command configuration values are read from environment variables (including `.env`) first, then `config.json`.
Logging settings still use environment variables (`HAPE_LOG_LEVEL`, `HAPE_ENABLE_LOG_FILE`, `HAPE_LOG_FILE`).

Default path:
```
~/.hape/config.json
```

You can override the config path per command:
```
hape --config-file-path /path/to/config.json <command>
```

## Generate config.json
Use the config command to generate the JSON file from environment variables.
To load values from a `.env` file, pass `--dot-env-file`.
```
hape config init-config-file
hape config init-config-file --dot-env-file /path/to/.env
```

This overwrites any existing config file at the target path.

## Keys
All config keys are optional in `config.json`.
Commands fail only when they read a key that is missing.

General keys:
- `DEPLOYMENTS_ROOT`

Logging keys (environment-based):
- `HAPE_LOG_LEVEL` (one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`; default `DEBUG`)
- `HAPE_ENABLE_LOG_FILE` (0/1 or true/false; default `0`)
- `HAPE_LOG_FILE` (path for log file when file logging is enabled; default `~/.hape/hape.log`)

API keys:
- `HAPE_API_HOST` (default `0.0.0.0`)
- `HAPE_API_PORT` (default `8080`)
- `HAPE_API_ADMIN_KEY` (required for token management endpoints)
- `HAPE_API_TOKENS_FILE` (default `~/.hape/api-tokens.json`)
- `HAPE_API_RATE_LIMIT_PER_MINUTE` (default `10`)

GitLab keys:
- `HAPE_GITLAB_DOMAIN`
- `GITLAB_TOKEN`
- `GITLAB_DEFAULT_GROUP_ID`

DORA keys:
- `HAPE_DORA_EXPORTER_HOST`
- `HAPE_DORA_EXPORTER_PORT`
- `HAPE_DORA_EXPORTER_REFRESH_SECONDS`
- `HAPE_DORA_GITLAB_GROUP_IDS`
- `HAPE_DORA_GIT_RULES_PATH`
- `HAPE_DORA_KUBERNETES_MAPPINGS_PATH`
- `HAPE_DORA_PROMETHEUS_URL`
- `HAPE_DORA_KUBE_CONTEXT`
- `HAPE_DORA_PROVIDER`
- `HAPE_GITHUB_API_URL`
- `HAPE_GITHUB_TOKEN` (PAT mode)
- `HAPE_GITHUB_DEFAULT_OWNER`
- `HAPE_GITHUB_APP_ID`
- `HAPE_GITHUB_INSTALLATION_ID`
- `HAPE_GITHUB_APP_PRIVATE_KEY_PATH`
- `HAPE_DORA_GITHUB_ORGS`

Atlassian keys:
- `ATLASSIAN_DOMAIN`
- `ATLASSIAN_EMAIL`
- `ATLASSIAN_API_KEY`
- `CONFLUENCE_CHANGELOG_PARENT_PAGE_ID`
- `CONFLUENCE_CHANGELOG_ENTRY_PAGE_TEMPLATE_ID`
- `CONFLUENCE_TEST_PARENT_PAGE_ID`

Integer keys (when present):
- `GITLAB_DEFAULT_GROUP_ID`
- `HAPE_DORA_EXPORTER_PORT`
- `HAPE_DORA_EXPORTER_REFRESH_SECONDS`
- `CONFLUENCE_CHANGELOG_PARENT_PAGE_ID`
- `CONFLUENCE_CHANGELOG_ENTRY_PAGE_TEMPLATE_ID`
- `CONFLUENCE_TEST_PARENT_PAGE_ID`

## DORA JSON files
The DORA feature reads two JSON files by default:
- `config/dora/git-rules.json`
- `config/dora/kubernetes-mappings.json`

You can override those locations with:
- `HAPE_DORA_GIT_RULES_PATH`
- `HAPE_DORA_KUBERNETES_MAPPINGS_PATH`
