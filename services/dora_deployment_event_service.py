from __future__ import annotations

import re

from core.logging import LocalLogging
from services.dora_models import DoraDeploymentEvent, DoraProjectRule


class DoraDeploymentEventService:
    def __init__(self) -> None:
        self.logger = LocalLogging.get_logger("hape.dora_deployment_event_service")

    @staticmethod
    def _match_job_name(job_name: str, job_names: list[str], job_name_regex: list[str]) -> bool:
        if job_name in job_names:
            return True
        for regex_pattern in job_name_regex:
            if re.search(regex_pattern, job_name):
                return True
        return False

    @staticmethod
    def _match_stage(stage: str, deploy_stages: list[str]) -> bool:
        if not deploy_stages:
            return True
        return stage in deploy_stages

    @staticmethod
    def _match_ref(ref: str, refs: list[str]) -> bool:
        return ref in refs

    def filter_successful_deployment_events(self, events: list[DoraDeploymentEvent], rule: DoraProjectRule) -> list[DoraDeploymentEvent]:
        filtered: list[DoraDeploymentEvent] = []
        for event in events:
            if event.status not in rule.successful_job_statuses:
                continue
            if not self._match_ref(ref=event.ref, refs=rule.refs):
                continue
            if not self._match_job_name(job_name=event.job_name, job_names=rule.deploy_job_names, job_name_regex=rule.deploy_job_name_regex):
                continue
            if not self._match_stage(stage=event.stage, deploy_stages=rule.deploy_stages):
                continue
            filtered.append(event)
        filtered.sort(key=lambda item: item.finished_at)
        return filtered


if __name__ == "__main__":
    print(DoraDeploymentEventService)
