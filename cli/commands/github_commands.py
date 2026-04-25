import argparse
from typing import Any

from core.logging import LocalLogging
from services.github_service import GitHubService


class GitHubCommands:
    @staticmethod
    def register(subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            "github",
            help="GitHub operations.",
        )
        parser.set_defaults(func=GitHubCommands.run_help, parser=parser)
        github_subparsers = parser.add_subparsers(
            dest="github_command",
            metavar="command",
        )
        github_subparsers.required = False

        init_repo_parser = github_subparsers.add_parser(
            "init-repo",
            help="initialize local git repo and create GitHub repository.",
        )
        init_repo_parser.add_argument(
            "--repo-path",
            required=True,
            default=None,
            help="local repository path to initialize.",
        )
        init_repo_parser.add_argument(
            "--owner",
            required=False,
            default=None,
            help="GitHub owner login (organization or user).",
        )
        init_repo_parser.add_argument(
            "--name",
            required=False,
            default=None,
            help="GitHub repository name (default: repo-path basename).",
        )
        visibility_group = init_repo_parser.add_mutually_exclusive_group(required=False)
        visibility_group.add_argument(
            "--private",
            action="store_true",
            required=False,
            default=False,
            help="create repository as private (default).",
        )
        visibility_group.add_argument(
            "--public",
            action="store_true",
            required=False,
            default=False,
            help="create repository as public.",
        )
        init_repo_parser.set_defaults(func=GitHubCommands.run_init_repo)

    @staticmethod
    def run_init_repo(args: Any) -> None:
        LocalLogging.bootstrap()
        github_service = GitHubService()
        visibility = "public" if args.public else "private"
        result = github_service.init_repo(
            repo_path=args.repo_path,
            owner=args.owner,
            name=args.name,
            visibility=visibility,
        )
        print(f"repository: {result['full_name']}")
        print(f"url: {result['html_url']}")
        print(f"clone_url: {result['clone_url']}")
        print(f"local_path: {result['local_path']}")

    @staticmethod
    def run_help(args: Any) -> None:
        args.parser.print_help()


if __name__ == "__main__":
    print(GitHubCommands)
