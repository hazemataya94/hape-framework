from __future__ import annotations

from statistics import median

from core.logging import LocalLogging
from services.dora_models import DoraDeploymentEvent
from utils.datetime_utils import DatetimeUtils


class DoraLeadTimeService:
    def __init__(self) -> None:
        self.logger = LocalLogging.get_logger("hape.dora_lead_time_service")

    @staticmethod
    def _build_commit_time_map(commits: list[dict]) -> dict[str, object]:
        commit_time_by_sha: dict[str, object] = {}
        for commit in commits:
            sha = str(commit.get("id", "")).strip()
            committed_date = str(commit.get("committed_date", "")).strip()
            if not sha or not committed_date:
                continue
            commit_time_by_sha[sha] = DatetimeUtils.parse_iso_datetime(committed_date)
        return commit_time_by_sha

    def calculate_project_lead_time_seconds(self, deployment_events: list[DoraDeploymentEvent], commits: list[dict]) -> tuple[float, int]:
        if len(deployment_events) < 2:
            return 0.0, 0
        commit_time_by_sha = self._build_commit_time_map(commits=commits)
        commit_times = []
        for commit in commits:
            committed_date = str(commit.get("committed_date", "")).strip()
            if not committed_date:
                continue
            commit_times.append(DatetimeUtils.parse_iso_datetime(committed_date))
        commit_times.sort()
        lead_time_samples: list[float] = []
        sorted_events = sorted(deployment_events, key=lambda item: item.finished_at)
        for index in range(1, len(sorted_events)):
            previous = sorted_events[index - 1]
            current = sorted_events[index]
            if previous.sha == current.sha:
                continue
            for commit_time in commit_times:
                if commit_time <= previous.finished_at:
                    continue
                if commit_time > current.finished_at:
                    break
                lead_time_samples.append(max((current.finished_at - commit_time).total_seconds(), 0.0))
            current_commit_time = commit_time_by_sha.get(current.sha)
            if current_commit_time and previous.finished_at < current_commit_time <= current.finished_at:
                lead_time_samples.append(max((current.finished_at - current_commit_time).total_seconds(), 0.0))
        if not lead_time_samples:
            return 0.0, 0
        return float(median(lead_time_samples)), 1


if __name__ == "__main__":
    print(DoraLeadTimeService)
