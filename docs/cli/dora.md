# DORA Metrics

## Purpose
Run DORA metrics using GitLab or GitHub data, commit history, and Prometheus/Kubernetes signals.

## Prerequisites
- Provider configured:
  - GitLab: `HAPE_DORA_PROVIDER=gitlab`, `HAPE_GITLAB_DOMAIN`, `GITLAB_TOKEN`, `HAPE_DORA_GITLAB_GROUP_IDS`
  - GitHub: `HAPE_DORA_PROVIDER=github`, `HAPE_GITHUB_TOKEN`, `HAPE_DORA_GITHUB_ORGS`
- Provider-specific DORA JSON files exist:
  - GitHub: `config/dora/git-rules-github.json` and `config/dora/kubernetes-mappings-github.json`
  - GitLab: `config/dora/git-rules-gitlab.json` and `config/dora/kubernetes-mappings-gitlab.json`
- Prometheus endpoint reachable from your runtime when Kubernetes signals are required.

This repository does not ship `config/dora/git-rules.json`.

Helper scripts:
- `scripts/dora_seed_github.py`
- `scripts/dora_clone_deploy_github.py`

## Validate DORA config
```bash
hape dora validate-config
```

## List configured projects
```bash
hape dora list-projects
```

## Compute one project
```bash
hape dora compute-project --project-path example/platform/service-a
```

## Notes
- Deployment frequency is based only on successful CI deploy jobs.
- Project refs must be explicit in the provider-specific git-rules JSON file.
- Overview and group views include configured projects with zero deployment data.
- Terraform bootstrap docs:
  - GitHub modules: `docs/infra/terraform-dora-github.md`
  - Terraform status: `docs/infra/terraform.md`
