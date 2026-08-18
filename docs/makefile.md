# Makefile Documentation

## Purpose
Document all `Makefile` variables and targets in one place.

## Variables
- `PYTHON` (default: `python`)
- `VERSION_FILE` (default: `VERSION`)
- `INSTALL_PREFIX` (default: empty)
- `API_BASE_URL` (default: `http://localhost:8080`)
- `API_TOKEN_NAME` (default: `default-token`)
- `API_ADMIN_KEY` (default: empty; required for `make api-generate-token`)
- `KIND_CLUSTER_NAME` (default: `hape`)
- `KIND_CONFIG_PATH` (default: `infrastructure/kubernetes/kind/cluster-config.yaml`)
- `DOCKER_IMAGE` (default: `example/hape`)
- `DOCKERFILE_PATH` (default: `docker/Dockerfile`)
- `KUSTOMIZE_TARGET_PATH` (derived from second argument to `make kustomize-apply` or `make kustomize-delete`)

## Targets
- `make help`: list available Make targets and descriptions.
- `make clean`: remove local build artifacts (`build`, `dist`, `*.egg-info`).
- `make bump-version`: increment patch version in `VERSION`.
- `make build`: bump version, then build wheel and source distribution.
- `make install`: install latest wheel from `dist/` with optional prefix.
- `make run-api`: run FastAPI server (`python -m api.app`).
- `make api-generate-token`: generate an API token using `POST /auth/tokens`.
- `make kind-up`: create local `kind` cluster when not already running.
- `make helmfile-sync`: sync Helmfile releases for local cluster tooling.
- `make kind-down`: delete local `kind` cluster when running.
- `make kustomize-apply <path>`: render and apply a kustomization directory.
- `make kustomize-delete <path>`: render and delete resources from a kustomization directory.
- `make publish`: retrieve the PyPI token with `hape vault kv-get`, upload `dist/` with twine, then commit/tag/push and publish Docker.
  - Uses Vault AppRole plus `secret.id`. Does not read a local `pypi.token` file.

## Common usage
Show available targets:

```bash
make help
```

Build package:

```bash
make build
```

Install latest wheel:

```bash
make install
```

Run API server:

```bash
make run-api
```

Generate API token:

```bash
make api-generate-token API_ADMIN_KEY=<YOUR_ADMIN_KEY> API_TOKEN_NAME=automation-bot
```

Generate API token against a different API base URL:

```bash
make api-generate-token API_ADMIN_KEY=<YOUR_ADMIN_KEY> API_BASE_URL=http://127.0.0.1:8080
```

Create local cluster:

```bash
make kind-up
```

Sync Helmfile releases:

```bash
make helmfile-sync
```

Delete local cluster:

```bash
make kind-down
```

Apply a kustomization directory:

```bash
make kustomize-apply infrastructure/kubernetes/exporters/dora
```

Delete a kustomization directory:

```bash
make kustomize-delete infrastructure/kubernetes/exporters/dora
```

Publish package to PyPI:

```bash
make publish
```

`make publish` calls `hape vault kv-get` to retrieve the token, then runs `python -m twine upload`.

Set `HAPE_VAULT_ROLE_ID` and provide `secret.id`.

Do not pass a local PyPI token file.

## Validation steps
1. Run `make help` and verify listed targets match this document.
2. Run `make kind-up` and verify cluster exists with `kind get clusters`.
3. Run `make helmfile-sync` and verify Helm releases with `helm -n monitoring list`.
4. Run `make kind-down` and verify cluster is removed.
5. Run `make kustomize-apply <path>` and verify resources exist with `kubectl get all -n <namespace>`.
6. Run `make kustomize-delete <path>` and verify resources are removed.
