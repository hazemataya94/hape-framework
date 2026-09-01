# Repository automation

## Purpose

Inspect or initialize GitHub repositories with explicit flags.

## Prerequisites

- `HAPE_GITHUB_TOKEN` or a completed `hape github auth` flow.
- Optional `HAPE_GITHUB_DEFAULT_OWNER` set to `example-org` in docs and tests.

## Read-only inspection

```bash
hape github user-info
hape github list-repos --org example-org
```

Safety level: `read`.

Side effects: none beyond GitHub API reads.

## Initialize a repository

```bash
hape github init-repo --repo-path /path/to/repo --owner example-org
```

Safety level: `write`.

Side effects: creates a remote repository, may run local `git init`, and may add `origin`.

Requires explicit current-session approval.

## Delete repositories

```bash
hape github delete-repos --org example-org --include service-a service-b
```

Safety level: `delete`.

Side effects: permanently deletes matching GitHub repositories.

Requires explicit current-session approval.

## Related documentation

- [GitHub CLI reference](../cli/github.md)
- [ECR repository ensure](../cli/ecr.md)
- [Init CI/CD](../cli/init-cicd.md)
- [Parity mapping](../api/parity-mapping.md)
