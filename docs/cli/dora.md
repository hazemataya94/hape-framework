# DORA Metrics

## Purpose
Run DORA metrics using GitLab or GitHub data, commit history, and Prometheus/Kubernetes signals.

## Prerequisites
- Provider configured:
  - GitLab: `HAPE_DORA_PROVIDER=gitlab`, `HAPE_GITLAB_DOMAIN`, `GITLAB_TOKEN`, `HAPE_DORA_GITLAB_GROUP_IDS`
  - GitHub: `HAPE_DORA_PROVIDER=github`, `HAPE_GITHUB_TOKEN`, `HAPE_DORA_GITHUB_ORGS`
- DORA JSON files exist:
  - `config/dora/git-rules.json`
  - `config/dora/kubernetes-mappings.json`
- Prometheus endpoint reachable from your runtime.

For GitHub-specific examples, you can use:
- `config/dora/git-rules-github.json`
- `config/dora/kubernetes-mappings-github.json`
- `scripts/dora_seed_github.py`
- `scripts/dora_clone_deploy_github.py`

## Validate DORA config
```bash
python -m cli.main dora validate-config
```

## List configured projects
```bash
python -m cli.main dora list-projects
```

## Compute one project
```bash
python -m cli.main dora compute-project --project-path example/platform/service-a
```

## Notes
- Deployment frequency is based only on successful CI deploy jobs.
- Project refs must be explicit in `git-rules.json`.
- Overview and group views include configured projects with zero deployment data.
- Terraform bootstrap docs:
  - GitLab: `docs/infra/terraform-dora-gitlab.md`
  - GitHub modules: `docs/infra/terraform-dora-github.md`
