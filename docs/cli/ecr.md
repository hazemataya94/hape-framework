# ECR CLI

## Purpose

Ensure AWS ECR repositories exist for `hape*` release metadata before image publish.

## Prerequisites

- AWS credentials in the default chain (`AWS_PROFILE`, env keys, or instance role).
- Metadata file with `registry.provider=ecr`, `registry.region`, and service `ecr_repository` values.

## Ensure repositories

Print a plan and stop (no creates, no prompt):

```bash
hape ecr ensure-repos \
  --metadata /path/to/example-system-metadata.json \
  --dry-run
```

Print a plan, then prompt `Proceed with ECR ensure-repos? [y/N]`:

```bash
hape ecr ensure-repos \
  --metadata /path/to/example-system-metadata.json
```

Approve the printed plan without a second prompt:

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

## Behavior

1. Load metadata and select enabled services that declare `ecr_repository`.
2. Print a plan with region, expected account, caller account, and repository names (no secrets).
3. With `--dry-run`, stop after the plan.
4. Without `--yes`, ask for confirmation (default No).
5. With `--yes`, describe each repository and create only when missing.
6. Never delete repositories and never push images.

## Make wrapper

From a product workspace repository:

```bash
cd /path/to/example-workspace
make prod-ensure-ecr DRY_RUN=1
make prod-ensure-ecr
```

`DRY_RUN=1` maps to `--dry-run`. Live runs pass `--yes`.
