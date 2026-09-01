# ECR CLI

## Purpose

This page documents a leftover `hape ecr ensure-repos` verb.

HAPE product ECR repositories are not managed by this CLI.

Create and update those repositories with Terraform and Terragrunt in the infrastructure repository, the same way sibling product repositories are created.

Agents must not run `hape ecr ensure-repos` for HAPE product images.

## Product path

Add the repository name to the Terragrunt ECR stack `repository_names` list in the infrastructure repository.

Plan and apply that stack with Terragrunt.

Publish image tags only after the repository exists.

## Leftover verb (do not use for HAPE product ECR)

The commands below remain in the CLI for historical reference.

Do not use them to create HAPE product repositories.

```bash
hape ecr ensure-repos \
  --metadata /path/to/example-system-metadata.json \
  --dry-run
```

```bash
hape ecr ensure-repos \
  --metadata /path/to/example-system-metadata.json
```

```bash
hape ecr ensure-repos \
  --metadata /path/to/example-system-metadata.json \
  --yes
```

Optional filters:

```bash
hape ecr ensure-repos \
  --metadata /path/to/example-system-metadata.json \
  --services website,backend \
  --region us-east-1 \
  --yes
```

## Historical behavior

1. Load metadata and select enabled services that declare `ecr_repository`.
2. Print a plan with region, expected account, caller account, and repository names (no secrets).
3. With `--dry-run`, stop after the plan.
4. Without `--yes`, ask for confirmation (default No).
5. With `--yes`, describe each repository and create only when missing.
6. Never delete repositories and never push images.
