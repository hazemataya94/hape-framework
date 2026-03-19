# Terraform DORA GitLab 

## Purpose
Create a GitLab.com Free sandbox for DORA exporter testing.

For GitHub module usage, see `docs/infra/terraform-dora-github.md`.

## Prerequisites
- Terraform installed.
- GitLab personal token with permissions to create groups/projects.
- Local working directory: repository root.

## Files
- `infrastructure/terraform/modules/gitlab_group/`
- `infrastructure/terraform/modules/gitlab_project/`
- `infrastructure/terraform/modules/gitlab_repository_files/`
- `infrastructure/terraform/envs/dora-demo-gitlab/`

## Usage
```bash
cd infrastructure/terraform/envs/dora-demo-gitlab
cp terraform.tfvars.example terraform.tfvars
```
Set needed values in `infrastructure/terraform/envs/dora-demo-gitlab/terraform.tfvars`
```
cd infrastructure/terraform/envs/dora-demo-gitlab
terraform init
terraform plan -out tfplan
terraform apply tfplan
```

## Seed deployment-like history
After Terraform creates projects, run:
```bash
python -m scripts.dora_seed_github --gitlab-domain gitlab.com --gitlab-token <YOUR_TOKEN> --project-id <PROJECT_ID> --ref main --iterations 5
```

## Validation
- Group and project structure exists in GitLab Free.
- Each project contains `.gitlab-ci.yml` and `kubernetes/deployment.yaml`.
- Seed output file `dora-seed-output.json` exists after running the seed script.

## Cleanup
```bash
cd infrastructure/terraform/envs/dora-demo-gitlab
terraform destroy
```
