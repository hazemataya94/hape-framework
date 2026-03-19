#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

from core.logging import LocalLogging


class DoraSeedGithubService:
    DEFAULT_COMMIT_MESSAGE = "seed: dora deployment event"

    def __init__(self, github_api_url: str, github_token: str, dry_run: bool) -> None:
        self.github_api_url = github_api_url.rstrip("/")
        self.github_token = github_token
        self.dry_run = dry_run
        self.logger = LocalLogging.get_logger("hape.dora_seed_github_service")

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.github_token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, payload: dict | None = None, allow_empty_response: bool = False, allow_not_found: bool = False) -> dict | None:
        if self.dry_run:
            self.logger.info("Dry-run request: method=%s path=%s", method, path)
            return {"dry_run": True, "method": method, "path": path, "payload": payload or {}}
        self.logger.debug("GitHub request start: method=%s path=%s", method, path)
        response = requests.request(
            method=method,
            url=f"{self.github_api_url}{path}",
            headers=self._headers(),
            data=json.dumps(payload) if payload else None,
            timeout=30,
        )
        self.logger.debug("GitHub request end: method=%s path=%s status=%s", method, path, response.status_code)
        if allow_not_found and response.status_code == 404:
            self.logger.debug("GitHub resource not found: path=%s", path)
            return None
        response.raise_for_status()
        if allow_empty_response and not response.content:
            return {}
        return response.json() if response.content else {}

    def _get_file_sha(self, owner: str, repo: str, file_path: str, ref: str) -> str | None:
        self.logger.debug("Checking seed file state: repo=%s/%s path=%s ref=%s", owner, repo, file_path, ref)
        response = self._request(
            method="GET",
            path=f"/repos/{owner}/{repo}/contents/{file_path}?ref={ref}",
            allow_not_found=True,
        )
        if response is None:
            self.logger.debug("Seed file does not exist yet: repo=%s/%s path=%s", owner, repo, file_path)
            return None
        sha = response.get("sha")
        if isinstance(sha, str) and sha:
            self.logger.debug("Seed file exists and will be updated: repo=%s/%s path=%s", owner, repo, file_path)
            return sha
        return None

    def _upsert_seed_file(self, owner: str, repo: str, ref: str, marker: str, index: int) -> dict:
        seed_file_path = f"seed/dora-seed-{index + 1}.txt"
        payload = {
            "message": self.DEFAULT_COMMIT_MESSAGE,
            "content": base64.b64encode(marker.encode("utf-8")).decode("utf-8"),
            "branch": ref,
        }
        existing_sha = self._get_file_sha(owner=owner, repo=repo, file_path=seed_file_path, ref=ref)
        if existing_sha is not None:
            payload["sha"] = existing_sha
            self.logger.info("Updating existing seed file: repo=%s/%s path=%s", owner, repo, seed_file_path)
        else:
            self.logger.info("Creating seed file: repo=%s/%s path=%s", owner, repo, seed_file_path)
        return self._request(method="PUT", path=f"/repos/{owner}/{repo}/contents/{seed_file_path}", payload=payload)

    def _trigger_workflow_dispatch(self, owner: str, repo: str, workflow_id: str, ref: str) -> dict:
        payload = {"ref": ref}
        self.logger.info("Triggering workflow dispatch: repo=%s/%s workflow=%s ref=%s", owner, repo, workflow_id, ref)
        return self._request(
            method="POST",
            path=f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
            payload=payload,
            allow_empty_response=True,
        )

    def seed_repository(self, owner: str, repo: str, workflow_id: str, ref: str, iterations: int) -> list[dict]:
        self.logger.info(
            "Starting GitHub seed run: repo=%s/%s workflow=%s ref=%s iterations=%s",
            owner,
            repo,
            workflow_id,
            ref,
            iterations,
        )
        events: list[dict] = []
        for index in range(iterations):
            self.logger.info("Seed iteration %s/%s for repo=%s/%s", index + 1, iterations, owner, repo)
            marker = f"seed-run={index + 1}, timestamp={datetime.now(timezone.utc).isoformat()}"
            commit_response = self._upsert_seed_file(owner=owner, repo=repo, ref=ref, marker=marker, index=index)
            workflow_response = self._trigger_workflow_dispatch(owner=owner, repo=repo, workflow_id=workflow_id, ref=ref)
            events.append({"commit": commit_response, "workflow_dispatch": workflow_response})
        self.logger.info("Completed GitHub seed run: repo=%s/%s events=%s", owner, repo, len(events))
        return events


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed GitHub sandbox repositories with deploy-like workflow history.")
    parser.add_argument("--github-api-url", required=False, default="https://api.github.com", help="GitHub API URL.")
    parser.add_argument("--github-token", required=True, default=None, help="GitHub personal access token.")
    parser.add_argument("--owner", required=True, default=None, help="GitHub owner or organization.")
    parser.add_argument("--repo", required=True, default=None, help="GitHub repository name.")
    parser.add_argument(
        "--workflow-id",
        required=True,
        default=None,
        help="Workflow file name or workflow ID (example: deploy.yml).",
    )
    parser.add_argument("--ref", required=False, default="main", help="Target branch or ref.")
    parser.add_argument("--iterations", required=False, default=5, type=int, help="Number of seed iterations.")
    parser.add_argument("--dry-run", required=False, default=False, action="store_true", help="Run without API writes.")
    return parser.parse_args()


def main() -> None:
    LocalLogging.bootstrap()
    logger = LocalLogging.get_logger("hape.dora_seed_github")
    args = _parse_args()
    logger.info(
        "Running GitHub seed script: owner=%s repo=%s workflow=%s ref=%s iterations=%s dry_run=%s",
        args.owner,
        args.repo,
        args.workflow_id,
        args.ref,
        args.iterations,
        args.dry_run,
    )
    service = DoraSeedGithubService(github_api_url=args.github_api_url, github_token=args.github_token, dry_run=args.dry_run)
    output = service.seed_repository(owner=args.owner, repo=args.repo, workflow_id=args.workflow_id, ref=args.ref, iterations=args.iterations)
    output_path = Path.cwd() / "dora-seed-github-output.json"
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    logger.info("GitHub DORA seed output written to %s", output_path)


if __name__ == "__main__":
    main()
