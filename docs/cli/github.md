# GitHub CLI

## Purpose
Use GitHub CLI commands in HAPE to authenticate, create, initialize, list, inspect, and delete GitHub repositories.

## Prerequisites
- Prefer `hape github auth login` (GitHub CLI `gh`) to store `HAPE_GITHUB_TOKEN` in `~/.hape/config.json`.
- Prefer `hape github auth configure --owner <org-or-user>` to store `HAPE_GITHUB_DEFAULT_OWNER`.
- You may still set those keys through environment variables or `hape config set`.
- For `init-repo`, set global git user email on host with `git config --global user.email <email>` so HAPE can resolve and grant admin access for the repository.
- For `init-repo`, ensure `--repo-path` exists and does not contain a `.git` directory.

## Auth bootstrap
Preferred path (required owner, defaults `github.com` + `ssh`):

```bash
hape github auth bootstrap --owner example-org
```

Flow:
1. Preflight: require `gh`; for SSH, resolve OpenSSH config with `ssh -G git@github.com` (uses `~/.ssh/config`, no assumed key paths).
2. Print a plan with hostname, git protocol, owner, and actions (no secrets).
3. Ask `Proceed with GitHub auth bootstrap? [y/N]` unless `--yes` is set.
4. If `gh` already has a session token, import it into `HAPE_GITHUB_TOKEN`. Otherwise run `gh auth login` (with `--skip-ssh-key` when protocol is `ssh`), store `HAPE_GITHUB_TOKEN` and `HAPE_GITHUB_DEFAULT_OWNER`, verify `auth_ok`.
5. Token write also sets process env and syncs `HAPE_GITHUB_TOKEN` in `hape-framework/.env` when that key already exists (env/.env override `config.json`).
6. Stop before `init-repo`.

Approve the printed plan without a second prompt:

```bash
hape github auth bootstrap --owner example-org --yes
```

`--org` is an alias for `--owner`.

Prompt once for git protocol (`ssh`/`https`) only when requested:

```bash
hape github auth bootstrap --owner example-org --set-github-auth-method
```

Or set protocol directly:

```bash
hape github auth bootstrap --owner example-org --git-protocol https --yes
```

Default `auth login` remains available for bare interactive `gh auth login`:

```bash
hape github auth login
```

Non-interactive web helper (CI/non-TTY):

```bash
hape github auth login --web
hape github auth login --non-interactive --web
```

If the org enforces SAML SSO, authorize the token for that org in GitHub after login.

Fallback when `gh` is unavailable:

```bash
printf '%s' "$HAPE_GITHUB_TOKEN" | hape github auth login --token-stdin
```

Manual configure and verify:

```bash
hape github auth configure --owner example-org
hape github auth status
hape github user-info
```

`auth status` reports whether a token is configured and whether API auth works. It never prints the token value.

## Create repository
Create a private repository in an organization by default:

```bash
hape github create repo --name service-a --org example-org
```

Create a public repository in an organization:

```bash
hape github create repo --name service-a --org example-org --public
```

## Init repository
Create a private repository by default:

```bash
hape github init-repo --repo-path /path/to/repo --owner example-org
```

Create a public repository and override the repository name:

```bash
hape github init-repo --repo-path /path/to/repo --name custom-repo-name --public
```

## Owner resolution
HAPE resolves owner in this order:
1. `--owner`
2. `HAPE_GITHUB_DEFAULT_OWNER`
3. authenticated token owner (`/user`), then first available org login

## List repositories
List repositories in the authenticated user personal account (default behavior):

```bash
hape github list-repos
```

List repositories in an organization:

```bash
hape github list-repos --org example-org
```

Include archived repositories:

```bash
hape github list-repos --org example-org --include-archived
```

## Clone repositories
Clone all repositories in an organization into a target directory:

```bash
hape github clone-repos --org example-org --clone-dir /path/to/dir
```

## Authenticated user info
Get authenticated GitHub user info:

```bash
hape github user-info
```

## Delete repositories
Delete repositories in an organization by explicit include list:

```bash
hape github delete-repos --org example-org --include service-a service-b
```

Delete all organization repositories and keep exclusions:

```bash
hape github delete-repos --org example-org --all --exclude service-a
```

Notes:
- `--org` is required for deletion.
- `--all` overrides `--include`.
- `--exclude` still applies when `--all` is used.
- The command prints the repository list first, then asks for a confirmation phrase before deletion.

## Behavior
- `create repo` creates a remote GitHub repository only.
- `create repo --org <org-login>` creates the repository in the selected organization.
- `create repo` requires `--name`.
- `create repo` visibility defaults to private.
- `create repo --public` creates a public repository.
- Repository name defaults to the basename of `--repo-path` when `--name` is not set.
- Visibility defaults to private.
- Command fails when `--repo-path` already contains `.git`.
- On success, HAPE resolves the host global git email to a GitHub login and adds that user as an admin collaborator.
- On success, HAPE runs `git init`, adds `origin`, and prints repository URL, local path, and admin collaborator login.
- `list-repos` without `--org` returns repositories owned by the authenticated user personal account.
- `list-repos --org <org-login>` returns repositories for that organization.
- `list-repos` prints JSON output with stable repository fields.
- `clone-repos` uses organization repositories returned by `list_repositories` and clones each repository by SSH URL.
- `clone-repos` writes repositories under recursive namespace paths: `<clone-dir>/<org>/<repo-name>`.
- `clone-repos` skips repositories that already exist locally and returns JSON with cloned and skipped counts.
- `user-info` prints JSON output with authenticated `login`, `name`, and `html_url`.
- `delete-repos` deletes only organization repositories in the provided `--org`.
