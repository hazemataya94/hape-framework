import argparse
import json
from typing import Any

from core.logging import LocalLogging
from services.ecr_service import EcrService


class EcrCommands:
    @staticmethod
    def register(subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            "ecr",
            help="ensure AWS ECR repositories for hape* release metadata.",
        )
        parser.set_defaults(func=EcrCommands.run_help, parser=parser)
        ecr_subparsers = parser.add_subparsers(
            dest="ecr_command",
            metavar="command",
        )
        ecr_subparsers.required = False

        ensure_parser = ecr_subparsers.add_parser(
            "ensure-repos",
            help="create missing ECR repositories from system metadata (idempotent).",
        )
        ensure_parser.add_argument(
            "--metadata",
            required=True,
            help="path to hape-*-system-metadata.json.",
        )
        ensure_parser.add_argument(
            "--services",
            required=False,
            default=None,
            help="comma-separated metadata service names. If omitted, all enabled services with ecr_repository are used.",
        )
        ensure_parser.add_argument(
            "--region",
            required=False,
            default=None,
            help="optional ECR region override (defaults to metadata.registry.region).",
        )
        ensure_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="print the ensure plan only; do not create repositories and do not prompt.",
        )
        ensure_parser.add_argument(
            "--yes",
            action="store_true",
            help="approve the printed plan and execute creates without an interactive prompt.",
        )
        ensure_parser.set_defaults(func=EcrCommands.run_ensure_repos)

    @staticmethod
    def run_help(args: Any) -> None:
        args.parser.print_help()

    @staticmethod
    def run_ensure_repos(args: Any) -> None:
        LocalLogging.bootstrap()
        service = EcrService()
        result = service.ensure_repositories(
            metadata_path=args.metadata,
            services=args.services,
            region=args.region,
            dry_run=args.dry_run,
            yes=args.yes,
        )
        if args.dry_run:
            print(json.dumps({"executed": result.get("executed"), "dry_run": True}, indent=2, sort_keys=True))


if __name__ == "__main__":
    print(EcrCommands)
