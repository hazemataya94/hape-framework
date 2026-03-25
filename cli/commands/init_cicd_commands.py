import argparse
from typing import Any

from core.logging import LocalLogging
from services.init_cicd.init_cicd_service import InitCicdService


class InitCicdCommands:
    @staticmethod
    def _print_list_section(title: str, values: list[str]) -> None:
        print(f"{title}:")
        if not values:
            print("- none")
            return
        for value in values:
            print(f"- {value}")

    @staticmethod
    def _print_result(result) -> None:
        print("Init CI/CD")
        print(f"Project: {result.project_path}")
        print(f"Deployment type: {result.deployment_type}")
        print(f"Framework: {result.framework}")
        print(f"Build flavor: {result.build_flavor}")
        print("")
        InitCicdCommands._print_list_section("Created", result.created_files)
        print("")
        InitCicdCommands._print_list_section("Skipped", result.skipped_files)
        print("")
        InitCicdCommands._print_list_section("Warnings", result.warnings)

    @staticmethod
    def register(subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            "init-cicd",
            help="scaffold deployment and CI files for supported projects.",
        )
        parser.add_argument(
            "--project-path",
            required=True,
            default=None,
            help="path to the target application project directory.",
        )
        parser.add_argument(
            "--deployment-type",
            required=True,
            default=None,
            help="deployment target type. v1 supports: kubernetes.",
        )
        parser.set_defaults(func=InitCicdCommands.run)

    @staticmethod
    def run(args: Any) -> None:
        LocalLogging.bootstrap()
        init_cicd_service = InitCicdService()
        result = init_cicd_service.init_cicd(
            project_path=args.project_path,
            deployment_type=args.deployment_type,
        )
        InitCicdCommands._print_result(result=result)


if __name__ == "__main__":
    print(InitCicdCommands())
