# GitHub CLI

## Purpose
Use GitHub CLI commands in HAPE to initialize a local repository and create the matching GitHub repository.

## Prerequisites
- Set `HAPE_GITHUB_TOKEN` in environment variables or config.
- Optional: set `HAPE_GITHUB_DEFAULT_OWNER` to use a default owner when `--owner` is not passed.
- Set global git user email on host with `git config --global user.email <email>` so HAPE can resolve and grant admin access for the repository.
- Ensure `--repo-path` exists and does not contain a `.git` directory.

## Init repository
Create a private repository by default:

```bash
python -m cli.main github init-repo --repo-path /path/to/repo --owner hape-vibes
```

Create a public repository and override the repository name:

```bash
python -m cli.main github init-repo --repo-path /path/to/repo --name custom-repo-name --public
```

## Owner resolution
HAPE resolves owner in this order:
1. `--owner`
2. `HAPE_GITHUB_DEFAULT_OWNER`
3. authenticated token owner (`/user`), then first available org login

## List repositories
List repositories in the authenticated user personal account (default behavior):

```bash
python -m cli.main github list-repos
```

List repositories in an organization:

```bash
python -m cli.main github list-repos --org hape-vibes
```

Include archived repositories:

```bash
python -m cli.main github list-repos --org hape-vibes --include-archived
```

## Authenticated user info
Get authenticated GitHub user info:

```bash
python -m cli.main github user-info
```

## Delete repositories
Delete repositories in an organization by explicit include list:

```bash
python -m cli.main github delete-repos --org hape-vibes --include service-a service-b
```

Delete all organization repositories and keep exclusions:

```bash
python -m cli.main github delete-repos --org hape-vibes --all --exclude service-a
```

Notes:
- `--org` is required for deletion.
- `--all` overrides `--include`.
- `--exclude` still applies when `--all` is used.
- The command prints the repository list first, then asks for a confirmation phrase before deletion.

## Behavior
- Repository name defaults to the basename of `--repo-path` when `--name` is not set.
- Visibility defaults to private.
- Command fails when `--repo-path` already contains `.git`.
- On success, HAPE resolves the host global git email to a GitHub login and adds that user as an admin collaborator.
- On success, HAPE runs `git init`, adds `origin`, and prints repository URL, local path, and admin collaborator login.
- `list-repos` without `--org` returns repositories owned by the authenticated user personal account.
- `list-repos --org <org-login>` returns repositories for that organization.
- `list-repos` prints JSON output with stable repository fields.
- `user-info` prints JSON output with authenticated `login`, `name`, and `html_url`.
- `delete-repos` deletes only organization repositories in the provided `--org`.
