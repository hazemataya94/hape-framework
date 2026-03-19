from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class DoraProjectRule:
    provider: str
    group_path: str
    project_path: str
    project_id: int | None
    default_branch: str
    refs: list[str]
    environment: str
    successful_job_statuses: list[str]
    deploy_job_names: list[str]
    deploy_job_name_regex: list[str]
    deploy_stages: list[str]
    failure_detection_minutes: int
    recovery_timeout_minutes: int
    recovery_stability_minutes: int


@dataclass
class DoraWorkloadMapping:
    kind: str
    name: str
    prometheus_label_matchers: dict[str, str]


@dataclass
class DoraKubernetesMapping:
    provider: str
    project_path: str
    cluster: str
    namespace: str
    workloads: list[DoraWorkloadMapping]


@dataclass
class DoraProjectInfo:
    provider: str
    group_path: str
    project_path: str
    project_id: int
    default_branch: str
    archived: bool


@dataclass
class DoraDeploymentEvent:
    provider: str
    group_path: str
    project_path: str
    project_id: int
    default_branch: str
    environment: str
    pipeline_id: int
    job_id: int
    job_name: str
    stage: str
    ref: str
    sha: str
    status: str
    started_at: datetime
    finished_at: datetime


@dataclass
class DoraFailureEvent:
    project_path: str
    environment: str
    deployment_finished_at: datetime
    failure_started_at: datetime
    recovered_at: datetime | None
    is_open: bool


@dataclass
class DoraProjectWindowMetrics:
    provider: str
    group_path: str
    project_path: str
    default_branch: str
    archived: bool
    environment: str
    window: str
    deployments_total: int = 0
    has_deployments: int = 0
    deployment_frequency_per_day: float = 0.0
    lead_time_seconds: float = 0.0
    has_change_data: int = 0
    failed_deployments_total: int = 0
    change_fail_rate_ratio: float = 0.0
    failed_deployment_recovery_time_seconds: float = 0.0
    open_failed_deployments_total: int = 0
    labels: dict[str, Any] = field(default_factory=dict)


if __name__ == "__main__":
    print(DoraProjectRule)
