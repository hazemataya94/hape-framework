# DORA workflows

## Purpose

Validate DORA config and compute metrics from GitLab or GitHub data.

## Prerequisites

- Provider configured:
  - GitLab: `HAPE_DORA_PROVIDER=gitlab`, `HAPE_GITLAB_DOMAIN`, `GITLAB_TOKEN`, `HAPE_DORA_GITLAB_GROUP_IDS`
  - GitHub: `HAPE_DORA_PROVIDER=github`, `HAPE_GITHUB_TOKEN`, `HAPE_DORA_GITHUB_ORGS`
- Provider-specific JSON files:
  - `config/dora/git-rules-github.json` or `config/dora/git-rules-gitlab.json`
  - `config/dora/kubernetes-mappings-github.json` or `config/dora/kubernetes-mappings-gitlab.json`
- Prometheus reachable from your runtime when Kubernetes signals are required.

There is no `config/dora/git-rules.json` file in this repository.

Pass the provider-specific path when a command requires `--git-rules-path`.

## Validate config

```bash
hape dora validate-config
```

Safety level: `read`.

Side effects: none.

## List projects

```bash
hape dora list-projects
```

Safety level: `read`.

## Compute one project

```bash
hape dora compute-project --project-path example/platform/service-a
```

Safety level: `read`.

Side effects: reads VCS and Prometheus data; does not mutate those systems.

## Related documentation

- [DORA CLI reference](../cli/dora.md)
- [DORA GitHub service](../services/dora-github.md)
- [DORA exporter](../exporters/dora-exporter.md)
- [GitHub DORA sandbox](../infra/terraform-dora-github.md)
