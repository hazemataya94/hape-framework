import argparse
import sys
from importlib import metadata

from core.config import Config
from core.errors.handler import ErrorHandler
from cli.commands.init_cicd_commands import InitCicdCommands
from cli.commands.config_commands import ConfigCommands
from cli.commands.confluence_commands import ConfluenceCommands
from cli.commands.csv_commands import CsvCommands
from cli.commands.dora_commands import DoraCommands
from cli.commands.eks_deployment_cost_commands import EksDeploymentCostCommands
from cli.commands.gitlab_commands import GitLabCommands
from cli.commands.github_commands import GitHubCommands
from cli.commands.jira_commands import JiraCommands
from cli.commands.kube_agent_commands import KubeAgentCommands
from cli.commands.markdown_commands import MarkdownCommands

class _CommandHelpFormatter(argparse.HelpFormatter):
    def __init__(self, prog: str) -> None:
        # Keep long command names and their descriptions on the same line.
        super().__init__(prog, max_help_position=32)

    def _format_action(self, action) -> str:
        if isinstance(action, argparse._SubParsersAction):
            formatted = super()._format_action(action)
            lines = formatted.splitlines()
            if len(lines) > 1:
                return "\n".join(lines[1:]) + "\n"
        return super()._format_action(action)

class _HapeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_help(sys.stderr)
        self.exit(2, f"\nerror: {message}\n")

class CLI:
    @staticmethod
    def _get_version() -> str:
        try:
            return metadata.version("hape")
        except metadata.PackageNotFoundError:
            return "unknown"

    @staticmethod
    def build_parser() -> argparse.ArgumentParser:
        version = CLI._get_version()
        parser = _HapeArgumentParser(
            prog="hape",
            description="CLI for platform and DevOps automations.",
            usage="%(prog)s [-h] [command] ...",
            formatter_class=_CommandHelpFormatter,
        )
        parser.add_argument(
            "--version",
            action="version",
            version=f"hape {version}",
            help="print the installed hape version and exit.",
        )
        parser.add_argument(
            "--config-file-path",
            required=False,
            default=None,
            help="path to config.json (default: ~/.hape/config.json).",
        )
        parser._positionals.title = "commands"
        subparsers = parser.add_subparsers(
            dest="command",
            metavar="command",
            parser_class=_HapeArgumentParser,
        )
        subparsers.required = False

        ConfigCommands.register(subparsers)
        GitLabCommands.register(subparsers)
        GitHubCommands.register(subparsers)
        JiraCommands.register(subparsers)
        ConfluenceCommands.register(subparsers)
        CsvCommands.register(subparsers)
        DoraCommands.register(subparsers)
        EksDeploymentCostCommands.register(subparsers)
        KubeAgentCommands.register(subparsers)
        InitCicdCommands.register(subparsers)
        MarkdownCommands.register(subparsers)

        return parser

    @staticmethod
    def run() -> None:
        Config.ensure_env_loaded()
        parser = CLI.build_parser()
        if len(sys.argv) == 1:
            parser.print_help()
            return
        args = parser.parse_args()
        Config.set_config_path(args.config_file_path)
        if not args.command:
            parser.print_help()
            return
        try:
            args.func(args)
        except Exception as exc:
            exit_code = ErrorHandler.handle(exc)
            raise SystemExit(exit_code)

def main() -> None:
    CLI.run()

if __name__ == "__main__":
    main()
