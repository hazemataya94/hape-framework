# GitHub CLI

## Purpose
Use GitHub CLI commands in HAPE to initialize a local repository and create the matching GitHub repository.

## Prerequisites
- Set `HAPE_GITHUB_TOKEN` in environment variables or config.
- Optional: set `HAPE_GITHUB_DEFAULT_OWNER` to use a default owner when `--owner` is not passed.
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

## Behavior
- Repository name defaults to the basename of `--repo-path` when `--name` is not set.
- Visibility defaults to private.
- Command fails when `--repo-path` already contains `.git`.
- On success, HAPE runs `git init`, adds `origin`, and prints repository URL and local path.
