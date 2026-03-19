#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

from core.logging import LocalLogging


class DoraSeedGitLabService:
    DEFAULT_COMMIT_MESSAGE = "seed: dora deployment event"

    def __init__(self, gitlab_domain: str, gitlab_token: str, dry_run: bool) -> None:
        self.gitlab_domain = gitlab_domain
        self.gitlab_token = gitlab_token
        self.dry_run = dry_run
        self.base_url = f"https://{gitlab_domain}/api/v4"
        self.logger = LocalLogging.get_logger("hape.dora_seed_gitlab_service")

    def _headers(self) -> dict[str, str]:
        return {"Private-Token": self.gitlab_token, "Content-Type": "application/json"}

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        if self.dry_run:
            self.logger.info("Dry-run request: method=%s path=%s", method, path)
            return {"dry_run": True, "method": method, "path": path, "payload": payload or {}}
        self.logger.debug("GitLab request start: method=%s path=%s", method, path)
        response = requests.request(
            method=method,
            url=f"{self.base_url}{path}",
            headers=self._headers(),
            data=json.dumps(payload) if payload else None,
            timeout=30,
        )
        self.logger.debug("GitLab request end: method=%s path=%s status=%s", method, path, response.status_code)
        response.raise_for_status()
        return response.json() if response.content else {}

    def _commit_seed_file(self, project_id: int, ref: str, marker: str) -> dict:
        self.logger.info("Creating/updating GitLab seed file: project_id=%s ref=%s", project_id, ref)
        payload = {
            "branch": ref,
            "commit_message": self.DEFAULT_COMMIT_MESSAGE,
            "actions": [
                {
                    "action": "upsert",
                    "file_path": "seed/dora-seed.txt",
                    "content": marker,
                }
            ],
        }
        return self._request(method="POST", path=f"/projects/{project_id}/repository/commits", payload=payload)

    def _trigger_pipeline(self, project_id: int, ref: str) -> dict:
        self.logger.info("Triggering GitLab pipeline: project_id=%s ref=%s", project_id, ref)
        payload = {"ref": ref}
        return self._request(method="POST", path=f"/projects/{project_id}/pipeline", payload=payload)

    def seed_project(self, project_id: int, ref: str, iterations: int) -> list[dict]:
        self.logger.info(
            "Starting GitLab seed run: project_id=%s ref=%s iterations=%s",
            project_id,
            ref,
            iterations,
        )
        events: list[dict] = []
        for index in range(iterations):
            self.logger.info("Seed iteration %s/%s for project_id=%s", index + 1, iterations, project_id)
            marker = f"seed-run={index + 1}, timestamp={datetime.now(timezone.utc).isoformat()}"
            commit_response = self._commit_seed_file(project_id=project_id, ref=ref, marker=marker)
            pipeline_response = self._trigger_pipeline(project_id=project_id, ref=ref)
            events.append({"commit": commit_response, "pipeline": pipeline_response})
        self.logger.info("Completed GitLab seed run: project_id=%s events=%s", project_id, len(events))
        return events


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed GitLab sandbox projects with deploy-like pipeline history.")
    parser.add_argument("--gitlab-domain", required=True, default=None, help="GitLab domain like gitlab.com.")
    parser.add_argument("--gitlab-token", required=True, default=None, help="GitLab personal access token.")
    parser.add_argument("--project-id", required=True, default=None, type=int, help="GitLab project ID to seed.")
    parser.add_argument("--ref", required=False, default="main", help="Target branch or ref.")
    parser.add_argument("--iterations", required=False, default=5, type=int, help="Number of seed iterations.")
    parser.add_argument("--dry-run", required=False, default=False, action="store_true", help="Run without API writes.")
    return parser.parse_args()


def main() -> None:
    LocalLogging.bootstrap()
    logger = LocalLogging.get_logger("hape.dora_seed_gitlab")
    args = _parse_args()
    logger.info(
        "Running GitLab seed script: project_id=%s ref=%s iterations=%s dry_run=%s",
        args.project_id,
        args.ref,
        args.iterations,
        args.dry_run,
    )
    service = DoraSeedGitLabService(gitlab_domain=args.gitlab_domain, gitlab_token=args.gitlab_token, dry_run=args.dry_run)
    output = service.seed_project(project_id=args.project_id, ref=args.ref, iterations=args.iterations)
    output_path = Path.cwd() / "dora-seed-output.json"
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    logger.info("GitLab DORA seed output written to %s", output_path)


if __name__ == "__main__":
    main()
