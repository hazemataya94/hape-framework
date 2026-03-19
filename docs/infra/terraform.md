# Terraform Status

## Purpose
Track current Terraform scope for HAPE infrastructure.

## Current status
- Terraform modules exist for GitLab and GitHub DORA sandbox provisioning.
- Environment stacks exist under:
  - `infrastructure/terraform/envs/dora-demo-gitlab/`
  - `infrastructure/terraform/envs/dora-demo-github/`

## Planned direction
- Expand reusable modules under `infrastructure/terraform/modules/`.
- Add more environment stacks under `infrastructure/terraform/envs/` for non-DORA use cases.
- Keep future module design aligned with least-privilege and secure defaults.

## Validation steps
- Confirm Terraform files exist:
  ```bash
  rg --files infrastructure/terraform -g "*.tf"
  ```
- Validate sandbox stack:
  ```bash
  cd infrastructure/terraform/envs/dora-demo-gitlab
  terraform init
  terraform validate
  ```
- Validate GitHub demo stack:
  ```bash
  cd infrastructure/terraform/envs/dora-demo-github
  terraform init
  terraform validate
  ```

## Related files
- `infrastructure/terraform/README.md`
- `infrastructure/README.md`
- `docs/infra/terraform-dora-gitlab.md`
- `docs/infra/terraform-dora-github.md`
