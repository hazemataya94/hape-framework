# Terraform DORA GitHub 

## Purpose
Provision GitHub repositories and bootstrap files for DORA exporter testing.

## Prerequisites
- Terraform installed.
- GitHub token with repository administration permissions.
- Repository root as working directory.

## Modules
- `infrastructure/terraform/modules/github_owner/`
- `infrastructure/terraform/modules/github_repository/`
- `infrastructure/terraform/modules/github_repository_files/`

## Usage model
Use the modules from a Terraform environment stack where the GitHub provider is configured.

Environment stack path:
- `infrastructure/terraform/envs/dora-demo-github/`
- Default environment creates 26 repositories: `hape-dora-demo-service-a` through `hape-dora-demo-service-z`.

Minimal root module example:
```hcl
provider "github" {
  owner = var.github_owner
  token = var.github_token
}

module "github_owner" {
  source = "../../modules/github_owner"
  owner  = var.github_owner
}

module "github_repository" {
  source = "../../modules/github_repository"
  repositories = [
    {
      name        = "service-a"
      description = "DORA sandbox repository"
      visibility  = "private"
    }
  ]
}

module "github_repository_files" {
  source                 = "../../modules/github_repository_files"
  repositories           = module.github_repository.repository_names
  default_branch         = "main"
  sample_ci_content      = "# placeholder GitHub workflow"
  sample_manifest_content = "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: sample"
}
```

## Validation
- Repositories are created under the configured owner.
- Each repository contains:
  - `.github/workflows/deploy.yml`
  - `kubernetes/deployment.yaml`
- In `kubernetes/deployment.yaml`, every `sample-app` placeholder is replaced with that repository name.

## Seed deployment-like history
After repositories and workflows exist, run:
```bash
python -m scripts.dora_seed_github --github-token <YOUR_TOKEN> --owner <OWNER> --repo <REPO> --workflow-id deploy.yml --ref main --iterations 5
```

## Clone and deploy seeded repositories
To deploy repository manifests to local Kubernetes:
```bash
python scripts/dora_clone_deploy_github.py --owner <OWNER> --github-token <YOUR_TOKEN> --clone-protocol https --kube-context kind-hape --manifest-path infrastructure/kubernetes
```
