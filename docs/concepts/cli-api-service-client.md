# CLI, API, services, and clients

## Purpose

Keep layer ownership explicit when you use or extend HAPE.

## CLI

Command groups are registered in `cli/main.py`.

Current groups: `config`, `gitlab`, `github`, `jira`, `linkedin`, `confluence`, `csv`, `dora`, `ecr`, `vault`, `eks-deployment-cost`, `kube-agent`, `init-cicd`, and `markdown`.

## API

Most CLI command paths have a matching `POST` endpoint.

CLI-only exceptions include `linkedin`, `ecr`, and interactive `github auth` flows.

See [parity mapping](../api/parity-mapping.md).

## Services and clients

Service internals live under [services](../services/README.md).

Client adapters live under `clients/` in the source tree.

## Related documentation

- [CLI index](../cli/README.md)
- [API index](../api/README.md)
- [Architecture](../architecture.md)
