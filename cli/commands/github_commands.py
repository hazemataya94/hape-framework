import argparse
import json
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

        list_repos_parser = github_subparsers.add_parser(
            "list-repos",
            help="list GitHub repositories for user or organization context.",
        )
        list_repos_parser.add_argument(
            "--org",
            required=False,
            default=None,
            help="GitHub organization login. If omitted, user repositories are returned.",
        )
        list_repos_parser.add_argument(
            "--include-archived",
            action="store_true",
            required=False,
            default=False,
            help="include archived repositories in results.",
        )
        list_repos_parser.set_defaults(func=GitHubCommands.run_list_repos)

        user_info_parser = github_subparsers.add_parser(
            "user-info",
            help="get authenticated GitHub user information.",
        )
        user_info_parser.set_defaults(func=GitHubCommands.run_user_info)

        delete_repos_parser = github_subparsers.add_parser(
            "delete-repos",
            help="delete GitHub repositories from an organization.",
        )
        delete_repos_parser.add_argument(
            "--org",
            required=True,
            default=None,
            help="GitHub organization login to target for deletion.",
        )
        delete_repos_parser.add_argument(
            "--include",
            required=False,
            nargs="+",
            default=None,
            help="repository names (or full names) to include for deletion. Accepts comma-separated values.",
        )
        delete_repos_parser.add_argument(
            "--exclude",
            "--execlude",
            dest="exclude",
            required=False,
            nargs="+",
            default=None,
            help="repository names (or full names) to exclude from deletion. Accepts comma-separated values.",
        )
        delete_repos_parser.add_argument(
            "--all",
            action="store_true",
            required=False,
            default=False,
            help="delete all repositories in the org. Overrides --include.",
        )
        delete_repos_parser.set_defaults(func=GitHubCommands.run_delete_repos)

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
        print(f"admin_collaborator: {result['admin_login']}")

    @staticmethod
    def run_list_repos(args: Any) -> None:
        LocalLogging.bootstrap()
        github_service = GitHubService()
        repositories = github_service.list_repositories(
            org=args.org,
            include_archived=args.include_archived,
        )
        print(json.dumps(repositories, indent=2, sort_keys=True))

    @staticmethod
    def run_user_info(args: Any) -> None:
        LocalLogging.bootstrap()
        github_service = GitHubService()
        user_info = github_service.get_authenticated_user_info()
        print(json.dumps(user_info, indent=2, sort_keys=True))

    @staticmethod
    def run_delete_repos(args: Any) -> None:
        LocalLogging.bootstrap()
        github_service = GitHubService()
        repositories_for_deletion = github_service.list_repositories_for_deletion(
            org=args.org,
            include=args.include,
            exclude=args.exclude,
            delete_all=args.all,
        )
        print("Repositories scheduled for deletion:")
        for repository in repositories_for_deletion:
            print(f"- {repository['full_name']}")
        print(f"Total repositories to delete: {len(repositories_for_deletion)}")
        confirmation_phrase = github_service.get_delete_repositories_confirmation_phrase()
        entered_phrase = input(f"Type '{confirmation_phrase}' to confirm deletion: ").strip()
        if entered_phrase != confirmation_phrase:
            print("Deletion cancelled.")
            return
        result = github_service.delete_repositories(
            org=args.org,
            include=args.include,
            exclude=args.exclude,
            delete_all=args.all,
            confirmation_phrase=entered_phrase,
        )
        print(json.dumps(result, indent=2, sort_keys=True))

    @staticmethod
    def run_help(args: Any) -> None:
        args.parser.print_help()


if __name__ == "__main__":
    print(GitHubCommands)
