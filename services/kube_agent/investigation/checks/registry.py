from services.kube_agent.investigation.checks.base_check import BaseCheck
from services.kube_agent.investigation.checks.packs.cost_checks import CostExporterAvailabilityCheck, CostHourlyIncreaseRatioCheck, CostTopWorkloadsIncreaseCheck, CostTotalHourlyThresholdCheck, CostWorkloadHourlyThresholdCheck
from services.kube_agent.investigation.checks.packs.image_pull_checks import ErrImagePullCheck, ImagePullBackOffCheck
from services.kube_agent.investigation.checks.packs.node_condition_checks import DiskPressureCheck, MemoryPressureCheck, NodeNotReadyCheck, PidPressureCheck
from services.kube_agent.investigation.checks.packs.pod_pending_checks import FailedSchedulingCheck, ImagePullFailureCheck, InsufficientResourceCheck, PvcBindingCheck, TaintMismatchCheck
from services.kube_agent.investigation.checks.packs.pod_restart_checks import EvictionCheck, OomKillCheck, ProbeFailureCheck, UnexpectedExitCodeCheck
from services.kube_agent.investigation.checks.packs.probe_failure_checks import LivenessProbeFailureCheck, ReadinessProbeFailureCheck
from services.kube_agent.investigation.checks.packs.rollout_regression_checks import ConfigChangeCorrelationCheck, DeploymentRevisionChangeCheck, ImageChangeCheck


class DiagnosticCheckRegistry:
    def get_checks(self, trigger_type: str | None = None) -> list[BaseCheck]:
        if trigger_type == "cost":
            return [CostExporterAvailabilityCheck(), CostTotalHourlyThresholdCheck(), CostWorkloadHourlyThresholdCheck(), CostHourlyIncreaseRatioCheck(), CostTopWorkloadsIncreaseCheck()]
        return [
            OomKillCheck(), ProbeFailureCheck(), EvictionCheck(), UnexpectedExitCodeCheck(),
            FailedSchedulingCheck(), InsufficientResourceCheck(), TaintMismatchCheck(), PvcBindingCheck(), ImagePullFailureCheck(),
            MemoryPressureCheck(), DiskPressureCheck(), PidPressureCheck(), NodeNotReadyCheck(),
            DeploymentRevisionChangeCheck(), ImageChangeCheck(), ConfigChangeCorrelationCheck(),
            ReadinessProbeFailureCheck(), LivenessProbeFailureCheck(),
            ImagePullBackOffCheck(), ErrImagePullCheck(),
        ]


if __name__ == "__main__":
    print(len(DiagnosticCheckRegistry().get_checks()))
