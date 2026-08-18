import argparse
from typing import Any

from core.config import Config
from core.logging import LocalLogging
from services.gitlab_service import GitLabService
from utils.datetime_utils import DatetimeUtils


class GitLabCommands:
    @staticmethod
    def register(subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            "gitlab",
            help="GitLab operations.",
        )
        parser.set_defaults(func=GitLabCommands.run_help, parser=parser)
        gitlab_subparsers = parser.add_subparsers(
            dest="gitlab_command",
            metavar="command",
        )
        gitlab_subparsers.required = False

        clone_parser = gitlab_subparsers.add_parser(
            "clone",
            help="clone all projects from a GitLab group.",
        )
        clone_parser.add_argument(
            "--group-id",
            required=False,
            type=int,
            default=None,
            help="gitlab group ID (default: GITLAB_DEFAULT_GROUP_ID).",
        )
        clone_parser.add_argument(
            "--clone-dir",
            required=True,
            default=None,
            help="directory to clone projects into.",
        )
        clone_parser.set_defaults(func=GitLabCommands.run_clone)

        counts_parser = gitlab_subparsers.add_parser(
            "mr-count-per-day",
            help="count merge requests per day from a date.",
        )
        counts_parser.add_argument(
            "--created-after",
            required=True,
            default=None,
            help="start date (dd.mm.yyyy, dd-mm-yyyy, or dd/mm/yyyy).",
        )
        scope_group = counts_parser.add_mutually_exclusive_group(required=True)
        scope_group.add_argument(
            "--group-id",
            required=False,
            type=int,
            default=None,
            help="gitlab group ID.",
        )
        scope_group.add_argument(
            "--project-id",
            required=False,
            type=int,
            default=None,
            help="gitlab project ID.",
        )
        counts_parser.add_argument(
            "--username",
            required=False,
            default=None,
            help="filter by author username (optional).",
        )
        counts_parser.set_defaults(func=GitLabCommands.run_mr_counts)

    @staticmethod
    def run_clone(args: Any) -> None:
        LocalLogging.bootstrap()
        service = GitLabService()
        group_id = args.group_id or Config.get_gitlab_default_group_id()
        service.clone_group_projects(group_id, args.clone_dir)

    @staticmethod
    def run_mr_counts(args: Any) -> None:
        LocalLogging.bootstrap()
        service = GitLabService()
        if args.group_id is not None and args.project_id is not None:
            raise ValueError("Use only one of --group-id or --project-id.")

        counts = service.count_merge_requests_per_day(
            created_after=args.created_after,
            group_id=args.group_id,
            project_id=args.project_id,
            username=args.username,
        )
        created_after = DatetimeUtils.normalize_date_format(args.created_after)

        if args.username:
            print(f"MR counts since {created_after} (group_id={args.group_id}, project_id={args.project_id}, username={args.username})")
        else:
            print(f"MR counts since {created_after} (group_id={args.group_id}, project_id={args.project_id})")
        for day in sorted(counts.keys()):
            print(f"{day}: {counts[day]}")
        print(f"Total: {sum(counts.values())}")

    @staticmethod
    def run_help(args: Any) -> None:
        args.parser.print_help()
