import argparse
from datetime import UTC, datetime

import cli.commands.kube_agent_commands as kube_agent_commands_module
from cli.commands.kube_agent_commands import KubeAgentCommands


class _FakeFindings:
    def __init__(self) -> None:
        self.summary = "summary"
        self.title = "title"
        self.likely_root_cause = "cause"
        self.evidence_summary = ["e1"]
        self.debugging_steps = ["s1"]
        self.suggested_fixes = ["f1"]
        self.dashboard_links = {}
        self.ai_used = False
        self.incident_id = "inc-1"


class _FakeIncident:
    def __init__(self) -> None:
        self.incident_id = "inc-1"
        self.fingerprint = "fp"
        self.first_seen = datetime.now(UTC)
        self.last_seen = datetime.now(UTC)
        self.occurrence_count = 2
        self.latest_likely_cause = "oom-kill"


class _FakeKubeAgentService:
    last_raw_trigger = None
    last_use_ai = None

    def investigate(self, raw_trigger, use_ai=True):
        _FakeKubeAgentService.last_raw_trigger = raw_trigger
        _FakeKubeAgentService.last_use_ai = use_ai
        return _FakeFindings()

    def list_incidents(self):
        return [_FakeIncident()]

    def get_incident(self, incident_id: str):
        if incident_id == "inc-1":
            return _FakeIncident()
        return None


class _FakeCostAnalysisService:
    last_call = None

    def analyze(self, kube_context: str, namespace: str, deployment: str | None, all_workloads: bool, historical_offset: str, use_ai: bool):
        _FakeCostAnalysisService.last_call = {
            "kube_context": kube_context,
            "namespace": namespace,
            "deployment": deployment,
            "all_workloads": all_workloads,
            "historical_offset": historical_offset,
            "use_ai": use_ai,
        }
        return _FakeFindings()


def test_cli_parses_pod_flags_and_calls_service(monkeypatch) -> None:
    monkeypatch.setattr(kube_agent_commands_module, "KubeAgentService", _FakeKubeAgentService)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    KubeAgentCommands.register(subparsers)
    args = parser.parse_args(
        [
            "kube-agent",
            "investigate",
            "pod",
            "--kube-context",
            "demo",
            "--namespace",
            "payments",
            "--pod",
            "api",
            "--use-ai",
            "true",
            "--output",
            "text",
        ]
    )
    args.func(args)
    assert _FakeKubeAgentService.last_raw_trigger["type"] == "pod"
    assert _FakeKubeAgentService.last_raw_trigger["cluster"] == "demo"
    assert _FakeKubeAgentService.last_use_ai is True


def test_cli_output_selection_json(monkeypatch, capsys) -> None:
    monkeypatch.setattr(kube_agent_commands_module, "KubeAgentService", _FakeKubeAgentService)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    KubeAgentCommands.register(subparsers)
    args = parser.parse_args(
        [
            "kube-agent",
            "investigate",
            "pod",
            "--kube-context",
            "demo",
            "--namespace",
            "payments",
            "--pod",
            "api",
            "--output",
            "json",
        ]
    )
    args.func(args)
    output = capsys.readouterr().out
    assert "incident_id" in output


def test_cli_output_selection_slack(monkeypatch, capsys) -> None:
    monkeypatch.setattr(kube_agent_commands_module, "KubeAgentService", _FakeKubeAgentService)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    KubeAgentCommands.register(subparsers)
    args = parser.parse_args(
        [
            "kube-agent",
            "investigate",
            "pod",
            "--kube-context",
            "demo",
            "--namespace",
            "payments",
            "--pod",
            "api",
            "--output",
            "slack",
        ]
    )
    args.func(args)
    output = capsys.readouterr().out
    assert "Likely root cause" in output


def test_cli_alert_command_builds_label_mapping(monkeypatch) -> None:
    monkeypatch.setattr(kube_agent_commands_module, "KubeAgentService", _FakeKubeAgentService)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    KubeAgentCommands.register(subparsers)
    args = parser.parse_args(
        [
            "kube-agent",
            "investigate",
            "alert",
            "--kube-context",
            "demo",
            "--alertname",
            "KubePodCrashLooping",
            "--namespace",
            "payments",
            "--pod",
            "api",
        ]
    )
    args.func(args)
    assert _FakeKubeAgentService.last_raw_trigger["type"] == "alert"
    assert _FakeKubeAgentService.last_raw_trigger["labels"]["namespace"] == "payments"
    assert _FakeKubeAgentService.last_raw_trigger["labels"]["pod"] == "api"


def test_cli_deployment_and_node_commands(monkeypatch) -> None:
    monkeypatch.setattr(kube_agent_commands_module, "KubeAgentService", _FakeKubeAgentService)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    KubeAgentCommands.register(subparsers)

    deployment_args = parser.parse_args(
        [
            "kube-agent",
            "investigate",
            "deployment",
            "--kube-context",
            "demo",
            "--namespace",
            "payments",
            "--deployment",
            "api",
        ]
    )
    deployment_args.func(deployment_args)
    assert _FakeKubeAgentService.last_raw_trigger["type"] == "deployment"

    node_args = parser.parse_args(
        [
            "kube-agent",
            "investigate",
            "node",
            "--kube-context",
            "demo",
            "--node",
            "node-1",
        ]
    )
    node_args.func(node_args)
    assert _FakeKubeAgentService.last_raw_trigger["type"] == "node"


def test_cli_cost_analyze_command(monkeypatch) -> None:
    monkeypatch.setattr(kube_agent_commands_module, "CostAnalysisService", _FakeCostAnalysisService)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    KubeAgentCommands.register(subparsers)
    args = parser.parse_args(
        [
            "kube-agent",
            "cost-analyze",
            "--kube-context",
            "demo",
            "--namespace",
            "payments",
            "--deployment",
            "api",
            "--historical-offset",
            "2h",
            "--use-ai",
            "true",
        ]
    )
    args.func(args)
    assert _FakeCostAnalysisService.last_call["deployment"] == "api"
    assert _FakeCostAnalysisService.last_call["historical_offset"] == "2h"
    assert _FakeCostAnalysisService.last_call["use_ai"] is True


def test_cli_cost_analyze_all_workloads_command(monkeypatch) -> None:
    monkeypatch.setattr(kube_agent_commands_module, "CostAnalysisService", _FakeCostAnalysisService)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    KubeAgentCommands.register(subparsers)
    args = parser.parse_args(
        [
            "kube-agent",
            "cost-analyze",
            "--kube-context",
            "demo",
            "--namespace",
            "payments",
            "--all-workloads",
            "--historical-offset",
            "1h",
            "--use-ai",
            "false",
        ]
    )
    args.func(args)
    assert _FakeCostAnalysisService.last_call["deployment"] is None
    assert _FakeCostAnalysisService.last_call["all_workloads"] is True


def test_cli_incidents_list_and_show(monkeypatch, capsys) -> None:
    monkeypatch.setattr(kube_agent_commands_module, "KubeAgentService", _FakeKubeAgentService)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    KubeAgentCommands.register(subparsers)

    list_args = parser.parse_args(["kube-agent", "incidents", "list"])
    list_args.func(list_args)
    list_output = capsys.readouterr().out
    assert "inc-1" in list_output

    show_args = parser.parse_args(["kube-agent", "incidents", "show", "--incident-id", "inc-1"])
    show_args.func(show_args)
    show_output = capsys.readouterr().out
    assert "incident_id: inc-1" in show_output


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__]))
