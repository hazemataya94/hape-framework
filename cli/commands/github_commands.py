import argparse
import json
import sys
from typing import Any

from core.logging import LocalLogging
from services.github_auth_service import GitHubAuthService
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

        create_parser = github_subparsers.add_parser(
            "create",
            help="create GitHub resources.",
        )
        create_subparsers = create_parser.add_subparsers(
            dest="github_create_command",
            metavar="command",
        )
        create_subparsers.required = True
        create_repo_parser = create_subparsers.add_parser(
            "repo",
            help="create a GitHub repository in an organization.",
        )
        create_repo_parser.add_argument(
            "--name",
            required=True,
            default=None,
            help="GitHub repository name to create.",
        )
        create_repo_parser.add_argument(
            "--org",
            required=True,
            default=None,
            help="GitHub organization login where the repository will be created.",
        )
        create_repo_visibility_group = create_repo_parser.add_mutually_exclusive_group(required=False)
        create_repo_visibility_group.add_argument(
            "--private",
            action="store_true",
            required=False,
            default=False,
            help="create repository as private (default).",
        )
        create_repo_visibility_group.add_argument(
            "--public",
            action="store_true",
            required=False,
            default=False,
            help="create repository as public.",
        )
        create_repo_parser.set_defaults(func=GitHubCommands.run_create_repo)

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

        clone_repos_parser = github_subparsers.add_parser(
            "clone-repos",
            help="clone all repositories from a GitHub organization.",
        )
        clone_repos_parser.add_argument(
            "--org",
            required=True,
            default=None,
            help="GitHub organization login to clone repositories from.",
        )
        clone_repos_parser.add_argument(
            "--clone-dir",
            required=True,
            default=None,
            help="directory to clone repositories into.",
        )
        clone_repos_parser.set_defaults(func=GitHubCommands.run_clone_repos)

        user_info_parser = github_subparsers.add_parser(
            "user-info",
            help="get authenticated GitHub user information.",
        )
        user_info_parser.set_defaults(func=GitHubCommands.run_user_info)

        auth_parser = github_subparsers.add_parser(
            "auth",
            help="bootstrap and inspect GitHub authentication for HAPE.",
        )
        auth_parser.set_defaults(func=GitHubCommands.run_help, parser=auth_parser)
        auth_subparsers = auth_parser.add_subparsers(
            dest="github_auth_command",
            metavar="command",
        )
        auth_subparsers.required = False

        auth_login_parser = auth_subparsers.add_parser(
            "login",
            help="authenticate with GitHub CLI and store HAPE_GITHUB_TOKEN.",
        )
        auth_login_parser.add_argument(
            "--token-stdin",
            action="store_true",
            required=False,
            default=False,
            help="read a GitHub PAT from stdin instead of using gh auth login.",
        )
        auth_login_parser.add_argument(
            "--web",
            action="store_true",
            required=False,
            default=False,
            help="use non-prompt gh web login with fixed github.com/https defaults.",
        )
        auth_login_parser.add_argument(
            "--non-interactive",
            action="store_true",
            required=False,
            default=False,
            help="require --web; fail instead of running interactive gh prompts.",
        )
        auth_login_parser.add_argument(
            "--scopes",
            required=False,
            default=None,
            help="comma-separated scopes for --web/--non-interactive login (default: repo,read:org,admin:org).",
        )
        auth_login_parser.set_defaults(func=GitHubCommands.run_auth_login)

        auth_configure_parser = auth_subparsers.add_parser(
            "configure",
            help="store HAPE_GITHUB_DEFAULT_OWNER in config.json.",
        )
        auth_configure_parser.add_argument(
            "--owner",
            required=True,
            default=None,
            help="GitHub organization or user login used as default owner.",
        )
        auth_configure_parser.set_defaults(func=GitHubCommands.run_auth_configure)

        auth_status_parser = auth_subparsers.add_parser(
            "status",
            help="show GitHub auth status without printing token values.",
        )
        auth_status_parser.set_defaults(func=GitHubCommands.run_auth_status)

        auth_bootstrap_parser = auth_subparsers.add_parser(
            "bootstrap",
            help="plan/confirm GitHub auth setup with ssh+github.com defaults.",
        )
        auth_bootstrap_parser.add_argument(
            "--owner",
            required=False,
            default=None,
            help="GitHub organization or user login (required unless --org is set).",
        )
        auth_bootstrap_parser.add_argument(
            "--org",
            required=False,
            default=None,
            help="Alias for --owner.",
        )
        auth_bootstrap_parser.add_argument(
            "--yes",
            action="store_true",
            required=False,
            default=False,
            help="approve the printed bootstrap plan without an extra confirm prompt.",
        )
        auth_bootstrap_parser.add_argument(
            "--set-github-auth-method",
            action="store_true",
            required=False,
            default=False,
            help="prompt once for git protocol (ssh/https). Default without this flag is ssh.",
        )
        auth_bootstrap_parser.add_argument(
            "--git-protocol",
            required=False,
            default=None,
            help="git protocol for gh auth login: ssh (default) or https.",
        )
        auth_bootstrap_parser.add_argument(
            "--hostname",
            required=False,
            default=None,
            help="GitHub hostname (default: github.com).",
        )
        auth_bootstrap_parser.add_argument(
            "--token-stdin",
            action="store_true",
            required=False,
            default=False,
            help="read a GitHub PAT from stdin instead of using gh auth login.",
        )
        auth_bootstrap_parser.add_argument(
            "--skip-list-repos",
            action="store_true",
            required=False,
            default=False,
            help="skip listing organization repositories after auth succeeds.",
        )
        auth_bootstrap_parser.set_defaults(func=GitHubCommands.run_auth_bootstrap)

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
    def run_create_repo(args: Any) -> None:
        LocalLogging.bootstrap()
        github_service = GitHubService()
        visibility = "public" if args.public else "private"
        result = github_service.create_repository(
            org=args.org,
            name=args.name,
            visibility=visibility,
        )
        print(json.dumps(result, indent=2, sort_keys=True))

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
    def run_clone_repos(args: Any) -> None:
        LocalLogging.bootstrap()
        github_service = GitHubService()
        result = github_service.clone_repositories(
            org=args.org,
            clone_dir=args.clone_dir,
        )
        print(json.dumps(result, indent=2, sort_keys=True))

    @staticmethod
    def run_user_info(args: Any) -> None:
        LocalLogging.bootstrap()
        github_service = GitHubService()
        user_info = github_service.get_authenticated_user_info()
        print(json.dumps(user_info, indent=2, sort_keys=True))

    @staticmethod
    def run_auth_login(args: Any) -> None:
        LocalLogging.bootstrap()
        github_auth_service = GitHubAuthService()
        if args.token_stdin:
            token = sys.stdin.read()
            result = github_auth_service.login_with_token(
                token=token,
                config_path=args.config_file_path,
            )
        else:
            result = github_auth_service.login_with_gh(
                config_path=args.config_file_path,
                web=args.web,
                scopes=args.scopes,
                non_interactive=args.non_interactive,
            )
        print(json.dumps(result, indent=2, sort_keys=True))

    @staticmethod
    def run_auth_configure(args: Any) -> None:
        LocalLogging.bootstrap()
        github_auth_service = GitHubAuthService()
        result = github_auth_service.configure_owner(
            owner=args.owner,
            config_path=args.config_file_path,
        )
        print(json.dumps(result, indent=2, sort_keys=True))

    @staticmethod
    def run_auth_status(args: Any) -> None:
        LocalLogging.bootstrap()
        github_auth_service = GitHubAuthService()
        result = github_auth_service.status(config_path=args.config_file_path)
        print(json.dumps(result, indent=2, sort_keys=True))

    @staticmethod
    def run_auth_bootstrap(args: Any) -> None:
        LocalLogging.bootstrap()
        token_stdin = sys.stdin.read() if args.token_stdin else None
        github_auth_service = GitHubAuthService()
        result = github_auth_service.bootstrap(
            owner=args.owner or args.org,
            yes=args.yes,
            list_repos=not args.skip_list_repos,
            config_path=args.config_file_path,
            token_stdin=token_stdin,
            set_github_auth_method=args.set_github_auth_method,
            git_protocol=args.git_protocol,
            hostname=args.hostname,
        )
        print(json.dumps(result, indent=2, sort_keys=True))

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
