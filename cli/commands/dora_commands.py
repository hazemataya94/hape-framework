import argparse
import json
from typing import Any

from core.logging import LocalLogging
from services.dora_config_service import DoraConfigService
from services.dora_service import DoraService


class DoraCommands:
    @staticmethod
    def register(subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            "dora",
            help="DORA metrics operations.",
        )
        parser.set_defaults(func=DoraCommands.run_help, parser=parser)
        dora_subparsers = parser.add_subparsers(
            dest="dora_command",
            metavar="command",
        )
        dora_subparsers.required = False

        validate_parser = dora_subparsers.add_parser(
            "validate-config",
            help="validate DORA config files.",
        )
        validate_parser.add_argument(
            "--git-rules-path",
            required=False,
            default="config/dora/git-rules.json",
            help="path to git-rules.json.",
        )
        validate_parser.add_argument(
            "--kubernetes-mappings-path",
            required=False,
            default="config/dora/kubernetes-mappings.json",
            help="path to kubernetes-mappings.json.",
        )
        validate_parser.set_defaults(func=DoraCommands.run_validate_config)

        list_projects_parser = dora_subparsers.add_parser(
            "list-projects",
            help="list configured DORA projects.",
        )
        list_projects_parser.add_argument(
            "--group-ids",
            required=False,
            default="",
            help="comma-separated GitLab group IDs.",
        )
        list_projects_parser.set_defaults(func=DoraCommands.run_list_projects)

        list_deployments_parser = dora_subparsers.add_parser(
            "list-deployments",
            help="list detected deployment events.",
        )
        list_deployments_parser.add_argument(
            "--project-path",
            required=True,
            default=None,
            help="project path with namespace.",
        )
        list_deployments_parser.set_defaults(func=DoraCommands.run_list_deployments)

        compute_project_parser = dora_subparsers.add_parser(
            "compute-project",
            help="compute DORA metrics for one project.",
        )
        compute_project_parser.add_argument(
            "--project-path",
            required=True,
            default=None,
            help="project path with namespace.",
        )
        compute_project_parser.set_defaults(func=DoraCommands.run_compute_project)

    @staticmethod
    def run_validate_config(args: Any) -> None:
        LocalLogging.bootstrap()
        config_service = DoraConfigService()
        project_rules, kube_mappings = config_service.load_resolved_configuration(
            git_rules_path=args.git_rules_path,
            kubernetes_mappings_path=args.kubernetes_mappings_path,
        )
        print(f"Validated git rules for {len(project_rules)} projects.")
        print(f"Validated Kubernetes mappings for {len(kube_mappings)} projects.")

    @staticmethod
    def run_list_projects(args: Any) -> None:
        LocalLogging.bootstrap()
        dora_service = DoraService()
        snapshot = dora_service.collect_snapshot()
        rows = snapshot.get("project_rows", [])
        unique_projects = sorted({row.get("project_path", "") for row in rows})
        for project_path in unique_projects:
            print(project_path)
        print(f"Total projects: {len(unique_projects)}")

    @staticmethod
    def run_list_deployments(args: Any) -> None:
        LocalLogging.bootstrap()
        dora_service = DoraService()
        snapshot = dora_service.collect_snapshot()
        rows = [row for row in snapshot.get("project_rows", []) if row.get("project_path") == args.project_path]
        print(json.dumps(rows, indent=2, sort_keys=True))

    @staticmethod
    def run_compute_project(args: Any) -> None:
        LocalLogging.bootstrap()
        dora_service = DoraService()
        snapshot = dora_service.collect_snapshot()
        rows = [row for row in snapshot.get("project_rows", []) if row.get("project_path") == args.project_path]
        print(json.dumps(rows, indent=2, sort_keys=True))

    @staticmethod
    def run_help(args: Any) -> None:
        args.parser.print_help()


if __name__ == "__main__":
    print(DoraCommands)
