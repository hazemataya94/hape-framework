#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable
from urllib.parse import urlsplit, urlunsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from clients.github_client import GitHubClient
from core.config import Config
from core.logging import LocalLogging


DEFAULT_REPOSITORY_PREFIX = "hape-dora-demo-service-"
DEFAULT_MANIFEST_CANDIDATES = [
    "infrastructure/kubernetes",
    "kubernetes",
    "k8s",
    "manifests",
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clone GitHub DORA demo repositories and deploy manifests to a local Kubernetes cluster."
    )
    parser.add_argument("--owner", required=False, default=None, help="GitHub owner or organization.")
    parser.add_argument(
        "--github-token",
        required=False,
        default="",
        help="GitHub token for private repository HTTPS clone and pull.",
    )
    parser.add_argument(
        "--clone-protocol",
        required=False,
        default="https",
        choices=["https", "ssh"],
        help="Clone protocol. Use ssh when SSH keys are configured.",
    )
    parser.add_argument(
        "--repos",
        required=False,
        default="",
        help="Comma-separated repository names to clone and deploy. If omitted, repositories are auto-discovered by prefix.",
    )
    parser.add_argument(
        "--repo-prefix",
        required=False,
        default=DEFAULT_REPOSITORY_PREFIX,
        help="Repository prefix used for auto-discovery when --repos is omitted.",
    )
    parser.add_argument(
        "--clone-dir",
        required=False,
        default="tmp/dora-github-repos",
        help="Directory where repositories are cloned.",
    )
    parser.add_argument("--branch", required=False, default="main", help="Branch to checkout for each repository.")
    parser.add_argument(
        "--manifest-path",
        required=False,
        default="",
        help="Relative path in each repo for Kubernetes manifests. If omitted, common locations are auto-detected.",
    )
    parser.add_argument(
        "--kube-context",
        required=False,
        default="hape-kind",
        help="kubectl context name for deployment target.",
    )
    parser.add_argument("--dry-run", required=False, default=False, action="store_true", help="Print actions without executing.")
    parser.add_argument("--skip-clone", required=False, default=False, action="store_true", help="Skip git clone/update steps.")
    parser.add_argument("--skip-deploy", required=False, default=False, action="store_true", help="Skip kubectl apply steps.")
    return parser.parse_args()


def _run_command(command: list[str], cwd: Path | None = None, dry_run: bool = False) -> None:
    if dry_run:
        return
    subprocess.run(command, cwd=str(cwd) if cwd else None, check=True, text=True, capture_output=False)


def _resolve_owner(owner: str | None) -> str:
    if owner:
        return owner
    orgs_csv = Config.get_dora_github_orgs_csv()
    first_org = orgs_csv.split(",")[0].strip()
    if not first_org:
        raise ValueError("GitHub owner is required. Set --owner or HAPE_DORA_GITHUB_ORGS.")
    return first_org


def _resolve_github_token(github_token: str | None) -> str:
    if github_token and github_token.strip():
        return github_token.strip()
    try:
        return Config.get_dora_github_token()
    except Exception:
        return ""


def _parse_repos(repos_csv: str) -> list[str]:
    values = [value.strip() for value in repos_csv.split(",")]
    return [value for value in values if value]


def _discover_repos_by_prefix(logger: LocalLogging, github_client: GitHubClient, owner: str, repo_prefix: str) -> list[str]:
    repositories = github_client.get_org_repositories(org_name=owner, include_archived=False)
    matched_repositories = []
    for repository in repositories:
        name = repository.get("name")
        if isinstance(name, str) and name.startswith(repo_prefix):
            matched_repositories.append(name)
    matched_repositories.sort()
    logger.info(
        "Auto-discovered %s repositories with prefix '%s' under owner '%s'.",
        len(matched_repositories),
        repo_prefix,
        owner,
    )
    return matched_repositories


def _build_authenticated_https_url(clone_url: str, github_token: str) -> str:
    if not github_token:
        return clone_url
    split_url = urlsplit(clone_url)
    if split_url.scheme != "https":
        return clone_url
    netloc = split_url.netloc
    return urlunsplit((split_url.scheme, f"x-access-token:{github_token}@{netloc}", split_url.path, split_url.query, split_url.fragment))


def _resolve_clone_url(repository: dict, clone_protocol: str, github_token: str) -> str:
    if clone_protocol == "ssh":
        ssh_url = repository.get("ssh_url")
        if isinstance(ssh_url, str) and ssh_url:
            return ssh_url
        raise RuntimeError("ssh_url was not returned by GitHub API.")
    clone_url = repository.get("clone_url")
    if not isinstance(clone_url, str) or not clone_url:
        raise RuntimeError("clone_url was not returned by GitHub API.")
    return _build_authenticated_https_url(clone_url=clone_url, github_token=github_token)


def _clone_or_update_repo( logger: LocalLogging, github_client: GitHubClient, owner: str, repo_name: str, clone_dir: Path, branch: str, clone_protocol: str, github_token: str, dry_run: bool, ) -> Path:
    clone_dir.mkdir(parents=True, exist_ok=True)
    repo_path = clone_dir / repo_name
    if not repo_path.exists():
        repository = github_client.get_repository(owner=owner, repo=repo_name)
        clone_url = _resolve_clone_url(repository=repository, clone_protocol=clone_protocol, github_token=github_token)
        logger.info("Cloning %s/%s into %s", owner, repo_name, repo_path)
        _run_command(["git", "clone", clone_url, str(repo_path)], dry_run=dry_run)
    else:
        logger.info("Repository already exists at %s", repo_path)
        if clone_protocol == "https" and github_token:
            repository = github_client.get_repository(owner=owner, repo=repo_name)
            clone_url = _resolve_clone_url(repository=repository, clone_protocol=clone_protocol, github_token=github_token)
            _run_command(["git", "remote", "set-url", "origin", clone_url], cwd=repo_path, dry_run=dry_run)

    logger.info("Checking out branch %s for %s", branch, repo_name)
    _run_command(["git", "fetch", "--all"], cwd=repo_path, dry_run=dry_run)
    _run_command(["git", "checkout", branch], cwd=repo_path, dry_run=dry_run)
    _run_command(["git", "pull", "--ff-only", "origin", branch], cwd=repo_path, dry_run=dry_run)
    return repo_path


def _detect_manifest_path(repo_path: Path, explicit_manifest_path: str) -> Path:
    if explicit_manifest_path:
        candidate = repo_path / explicit_manifest_path
        if not candidate.exists():
            raise FileNotFoundError(f"Manifest path does not exist: {candidate}")
        return candidate
    for rel_path in DEFAULT_MANIFEST_CANDIDATES:
        candidate = repo_path / rel_path
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"No manifest path found in {repo_path}. Tried: {', '.join(DEFAULT_MANIFEST_CANDIDATES)}"
    )


def _has_kustomization(path: Path) -> bool:
    return any((path / file_name).exists() for file_name in ("kustomization.yaml", "kustomization.yml", "Kustomization"))


def _deploy_repo_manifests(logger: LocalLogging, repo_path: Path, manifest_path: Path, kube_context: str, dry_run: bool) -> None:
    if _has_kustomization(manifest_path):
        command = ["kubectl", "--context", kube_context, "apply", "-k", str(manifest_path)]
        logger.info("Deploying %s with kustomize path %s", repo_path.name, manifest_path)
        _run_command(command, dry_run=dry_run)
        return

    yaml_files = sorted(manifest_path.rglob("*.yaml")) + sorted(manifest_path.rglob("*.yml"))
    if not yaml_files:
        raise FileNotFoundError(f"No Kubernetes YAML files found under {manifest_path}.")

    logger.info("Deploying %s with manifest directory %s", repo_path.name, manifest_path)
    _run_command(["kubectl", "--context", kube_context, "apply", "-f", str(manifest_path)], dry_run=dry_run)


def _check_context_exists(kube_context: str) -> None:
    result = subprocess.run(
        ["kubectl", "config", "get-contexts", "-o", "name"],
        check=True,
        text=True,
        capture_output=True,
    )
    contexts = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if kube_context not in contexts:
        raise RuntimeError(f"kubectl context '{kube_context}' was not found.")


def _iter_repository_names(repository_names: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for repository_name in repository_names:
        if repository_name in seen:
            continue
        seen.add(repository_name)
        ordered.append(repository_name)
    return ordered


def main() -> None:
    LocalLogging.bootstrap()
    logger = LocalLogging.get_logger("hape.dora_clone_deploy_github")
    args = _parse_args()

    owner = _resolve_owner(args.owner)
    github_token = _resolve_github_token(args.github_token)
    clone_dir = Path(args.clone_dir).expanduser().resolve()
    github_client = GitHubClient(token=github_token or None)

    repository_names = _parse_repos(args.repos)
    if repository_names:
        repository_names = _iter_repository_names(repository_names)
        logger.info("Using explicit repository list from --repos (%s repositories).", len(repository_names))
    else:
        repository_names = _discover_repos_by_prefix(
            logger=logger,
            github_client=github_client,
            owner=owner,
            repo_prefix=args.repo_prefix,
        )
        repository_names = _iter_repository_names(repository_names)
        if not repository_names:
            raise ValueError(
                f"No repositories found for owner '{owner}' with prefix '{args.repo_prefix}'. "
                "Use --repos to pass an explicit list."
            )

    if args.clone_protocol == "https" and not github_token and not args.skip_clone:
        logger.warning(
            "No GitHub token provided for HTTPS clone. Private repositories may fail. Use --github-token or set HAPE_GITHUB_TOKEN."
        )

    if not args.skip_deploy:
        _check_context_exists(args.kube_context)

    for repo_name in repository_names:
        repo_path = clone_dir / repo_name
        if not args.skip_clone:
            repo_path = _clone_or_update_repo(
                logger=logger,
                github_client=github_client,
                owner=owner,
                repo_name=repo_name,
                clone_dir=clone_dir,
                branch=args.branch,
                clone_protocol=args.clone_protocol,
                github_token=github_token,
                dry_run=args.dry_run,
            )
        if not args.skip_deploy:
            manifest_path = _detect_manifest_path(repo_path=repo_path, explicit_manifest_path=args.manifest_path)
            _deploy_repo_manifests(
                logger=logger,
                repo_path=repo_path,
                manifest_path=manifest_path,
                kube_context=args.kube_context,
                dry_run=args.dry_run,
            )

    logger.info("Done. Processed repositories: %s", ", ".join(repository_names))


if __name__ == "__main__":
    main()
