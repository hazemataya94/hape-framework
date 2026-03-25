import argparse
import json
from typing import Any

from core.logging import LocalLogging
from services.kube_agent.cost.cost_analysis_service import CostAnalysisService
from services.kube_agent.investigation.findings.json_formatter import JsonFormatter
from services.kube_agent.investigation.findings.markdown_formatter import MarkdownFormatter
from services.kube_agent.investigation.findings.slack_formatter import SlackFormatter
from services.kube_agent.kube_agent_service import KubeAgentService


class KubeAgentCommands:
    @staticmethod
    def _build_investigate_raw_trigger(args: Any, trigger_type: str, name: str, namespace: str | None = None) -> dict[str, str]:
        raw_trigger = {
            "type": trigger_type,
            "cluster": args.kube_context,
            "name": name,
            "source": "cli",
        }
        if namespace:
            raw_trigger["namespace"] = namespace
        return raw_trigger

    @staticmethod
    def _parse_bool_text(value: str) -> bool:
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _print_json(payload: Any) -> None:
        print(json.dumps(payload, indent=2, default=str))

    @staticmethod
    def _print_findings(findings, output: str) -> None:
        if output == "json":
            print(JsonFormatter.format(findings=findings))
            return
        if output == "markdown":
            markdown_formatter = MarkdownFormatter()
            print(markdown_formatter.format(findings=findings))
            return
        if output == "slack":
            slack_formatter = SlackFormatter()
            print(slack_formatter.format(findings=findings))
            return
        print(findings.summary)

    def _register_investigate_parser(investigate_subparsers: argparse._SubParsersAction) -> None:
        pod_parser = investigate_subparsers.add_parser(
            "pod",
            help="investigate a pod incident.",
        )
        pod_parser.add_argument(
            "--kube-context",
            required=True,
            default=None,
            help="Kubernetes context (cluster) name.",
        )
        pod_parser.add_argument(
            "--namespace",
            required=True,
            default=None,
            help="namespace for the target pod.",
        )
        pod_parser.add_argument(
            "--pod",
            required=True,
            default=None,
            help="pod name.",
        )
        pod_parser.add_argument(
            "--output",
            required=False,
            default="text",
            help="output format: text|json|markdown|slack.",
        )
        pod_parser.add_argument(
            "--use-ai",
            required=False,
            default="false",
            help="enable optional AI explanation: true|false.",
        )
        pod_parser.set_defaults(func=KubeAgentCommands.run_investigate_pod)

        deployment_parser = investigate_subparsers.add_parser(
            "deployment",
            help="investigate a deployment incident.",
        )
        deployment_parser.add_argument(
            "--kube-context",
            required=True,
            default=None,
            help="Kubernetes context (cluster) name.",
        )
        deployment_parser.add_argument(
            "--namespace",
            required=True,
            default=None,
            help="namespace for the target deployment.",
        )
        deployment_parser.add_argument(
            "--deployment",
            required=True,
            default=None,
            help="deployment name.",
        )
        deployment_parser.add_argument(
            "--output",
            required=False,
            default="text",
            help="output format: text|json|markdown|slack.",
        )
        deployment_parser.add_argument(
            "--use-ai",
            required=False,
            default="false",
            help="enable optional AI explanation: true|false.",
        )
        deployment_parser.set_defaults(func=KubeAgentCommands.run_investigate_deployment)

        node_parser = investigate_subparsers.add_parser(
            "node",
            help="investigate a node incident.",
        )
        node_parser.add_argument(
            "--kube-context",
            required=True,
            default=None,
            help="Kubernetes context (cluster) name.",
        )
        node_parser.add_argument(
            "--node",
            required=True,
            default=None,
            help="node name.",
        )
        node_parser.add_argument(
            "--output",
            required=False,
            default="text",
            help="output format: text|json|markdown|slack.",
        )
        node_parser.add_argument(
            "--use-ai",
            required=False,
            default="false",
            help="enable optional AI explanation: true|false.",
        )
        node_parser.set_defaults(func=KubeAgentCommands.run_investigate_node)

        alert_parser = investigate_subparsers.add_parser(
            "alert",
            help="investigate an alert incident.",
        )
        alert_parser.add_argument(
            "--kube-context",
            required=True,
            default=None,
            help="Kubernetes context (cluster) name.",
        )
        alert_parser.add_argument(
            "--alertname",
            required=True,
            default=None,
            help="alert name.",
        )
        alert_parser.add_argument(
            "--namespace",
            required=False,
            default=None,
            help="optional namespace hint for alert investigation.",
        )
        alert_parser.add_argument(
            "--pod",
            required=False,
            default=None,
            help="optional pod label hint from alert payload.",
        )
        alert_parser.add_argument(
            "--node",
            required=False,
            default=None,
            help="optional node label hint from alert payload.",
        )
        alert_parser.add_argument(
            "--output",
            required=False,
            default="text",
            help="output format: text|json|markdown|slack.",
        )
        alert_parser.add_argument(
            "--use-ai",
            required=False,
            default="false",
            help="enable optional AI explanation: true|false.",
        )
        alert_parser.set_defaults(func=KubeAgentCommands.run_investigate_alert)

    @staticmethod
    def _register_cost_analyze_parser(kube_agent_subparsers: argparse._SubParsersAction) -> None:
        cost_parser = kube_agent_subparsers.add_parser(
            "cost-analyze",
            help="analyze deployment cost metrics from eks-deployment-cost exporter.",
        )
        cost_parser.add_argument(
            "--kube-context",
            required=True,
            default=None,
            help="Kubernetes context (cluster) name.",
        )
        cost_parser.add_argument(
            "--namespace",
            required=True,
            default=None,
            help="namespace scope for cost analysis.",
        )
        target_group = cost_parser.add_mutually_exclusive_group(required=True)
        target_group.add_argument(
            "--deployment",
            default=None,
            help="deployment name.",
        )
        target_group.add_argument(
            "--all-workloads",
            action="store_true",
            help="analyze all workloads in the namespace.",
        )
        cost_parser.add_argument(
            "--historical-offset",
            required=False,
            default="1h",
            help="historical Prometheus offset for increase-ratio checks, for example: 30m or 1h.",
        )
        cost_parser.add_argument(
            "--output",
            required=False,
            default="text",
            help="output format: text|json|markdown|slack.",
        )
        cost_parser.add_argument(
            "--use-ai",
            required=False,
            default="false",
            help="enable optional AI explanation: true|false.",
        )
        cost_parser.set_defaults(func=KubeAgentCommands.run_cost_analyze)

    def register(subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            "kube-agent",
            help="investigate Kubernetes incidents from CLI triggers.",
        )
        parser.set_defaults(func=KubeAgentCommands.run_help, parser=parser)
        kube_agent_subparsers = parser.add_subparsers(dest="kube_agent_command", metavar="command")
        kube_agent_subparsers.required = False

        investigate_parser = kube_agent_subparsers.add_parser("investigate", help="investigate a Kubernetes incident trigger.")
        investigate_subparsers = investigate_parser.add_subparsers(dest="investigate_kind", metavar="kind")
        investigate_subparsers.required = True
        KubeAgentCommands._register_investigate_parser(investigate_subparsers=investigate_subparsers)
        KubeAgentCommands._register_cost_analyze_parser(kube_agent_subparsers=kube_agent_subparsers)

        incidents_parser = kube_agent_subparsers.add_parser("incidents", help="list or show stored incidents.")
        incidents_subparsers = incidents_parser.add_subparsers(dest="incidents_command", metavar="command")
        incidents_subparsers.required = True

        list_parser = incidents_subparsers.add_parser("list", help="list stored incidents.")
        list_parser.add_argument("--output", required=False, default="text", help="output format: text|json.")
        list_parser.set_defaults(func=KubeAgentCommands.run_incidents_list)

        show_parser = incidents_subparsers.add_parser("show", help="show one stored incident.")
        show_parser.add_argument("--incident-id", required=True, default=None, help="incident identifier.")
        show_parser.add_argument("--output", required=False, default="text", help="output format: text|json.")
        show_parser.set_defaults(func=KubeAgentCommands.run_incidents_show)

    @staticmethod
    def run_investigate_pod(args: Any) -> None:
        LocalLogging.bootstrap()
        kube_agent_service = KubeAgentService()
        findings = kube_agent_service.investigate(
            raw_trigger=KubeAgentCommands._build_investigate_raw_trigger(
                args=args,
                trigger_type="pod",
                namespace=args.namespace,
                name=args.pod,
            ),
            use_ai=KubeAgentCommands._parse_bool_text(args.use_ai),
        )
        KubeAgentCommands._print_findings(findings=findings, output=args.output)

    @staticmethod
    def run_investigate_deployment(args: Any) -> None:
        LocalLogging.bootstrap()
        kube_agent_service = KubeAgentService()
        findings = kube_agent_service.investigate(
            raw_trigger=KubeAgentCommands._build_investigate_raw_trigger(
                args=args,
                trigger_type="deployment",
                namespace=args.namespace,
                name=args.deployment,
            ),
            use_ai=KubeAgentCommands._parse_bool_text(args.use_ai),
        )
        KubeAgentCommands._print_findings(findings=findings, output=args.output)

    @staticmethod
    def run_investigate_node(args: Any) -> None:
        LocalLogging.bootstrap()
        kube_agent_service = KubeAgentService()
        findings = kube_agent_service.investigate(
            raw_trigger=KubeAgentCommands._build_investigate_raw_trigger(
                args=args,
                trigger_type="node",
                name=args.node,
            ),
            use_ai=KubeAgentCommands._parse_bool_text(args.use_ai),
        )
        KubeAgentCommands._print_findings(findings=findings, output=args.output)

    @staticmethod
    def run_investigate_alert(args: Any) -> None:
        LocalLogging.bootstrap()
        kube_agent_service = KubeAgentService()
        labels: dict[str, str] = {}
        if args.namespace:
            labels["namespace"] = args.namespace
        if args.pod:
            labels["pod"] = args.pod
        if args.node:
            labels["node"] = args.node
        findings = kube_agent_service.investigate(
            raw_trigger={
                "type": "alert",
                "cluster": args.kube_context,
                "name": args.alertname,
                "source": "cli",
                "labels": labels,
                "namespace": args.namespace,
            },
            use_ai=KubeAgentCommands._parse_bool_text(args.use_ai),
        )
        KubeAgentCommands._print_findings(findings=findings, output=args.output)

    @staticmethod
    def run_cost_analyze(args: Any) -> None:
        LocalLogging.bootstrap()
        cost_analysis_service = CostAnalysisService()
        is_all_workloads = bool(args.all_workloads)
        findings = cost_analysis_service.analyze(
            kube_context=args.kube_context,
            namespace=args.namespace,
            deployment=args.deployment,
            all_workloads=is_all_workloads,
            historical_offset=args.historical_offset,
            use_ai=KubeAgentCommands._parse_bool_text(args.use_ai),
        )
        KubeAgentCommands._print_findings(findings=findings, output=args.output)

    def run_incidents_list(args: Any) -> None:
        LocalLogging.bootstrap()
        kube_agent_service = KubeAgentService()
        incidents = kube_agent_service.list_incidents()
        if args.output == "json":
            KubeAgentCommands._print_json({"incidents": [item.__dict__ for item in incidents]})
            return
        for incident in incidents:
            print(f"{incident.incident_id} | {incident.last_seen.isoformat()} | {incident.latest_likely_cause or 'unknown'}")

    @staticmethod
    def run_incidents_show(args: Any) -> None:
        LocalLogging.bootstrap()
        kube_agent_service = KubeAgentService()
        incident = kube_agent_service.get_incident(incident_id=args.incident_id)
        if not incident:
            print(f"Incident not found: {args.incident_id}")
            return
        if args.output == "json":
            KubeAgentCommands._print_json(incident.__dict__)
            return
        print(f"incident_id: {incident.incident_id}")
        print(f"fingerprint: {incident.fingerprint}")
        print(f"first_seen: {incident.first_seen.isoformat()}")
        print(f"last_seen: {incident.last_seen.isoformat()}")
        print(f"occurrence_count: {incident.occurrence_count}")
        print(f"latest_likely_cause: {incident.latest_likely_cause or 'unknown'}")

    @staticmethod
    def run_help(args: Any) -> None:
        args.parser.print_help()


if __name__ == "__main__":
    print(KubeAgentCommands())
