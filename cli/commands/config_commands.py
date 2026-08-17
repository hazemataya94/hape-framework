import argparse
import json
from typing import Any

from core.logging import LocalLogging
from services.config_service import ConfigService


class ConfigCommands:
    @staticmethod
    def register(subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            "config",
            help="config file operations.",
        )
        parser.set_defaults(func=ConfigCommands.run_help, parser=parser)
        config_subparsers = parser.add_subparsers(
            dest="config_command",
            metavar="command",
        )
        config_subparsers.required = False

        init_parser = config_subparsers.add_parser(
            "init-config-file",
            help="generate config.json from .env.",
        )
        init_parser.add_argument(
            "--dot-env-file",
            required=False,
            default=None,
            help="path to .env file (optional). If omitted, use environment variables.",
        )
        init_parser.set_defaults(func=ConfigCommands.run_init_config_file)

        show_parser = config_subparsers.add_parser(
            "show",
            help="show values from the JSON config file.",
        )
        show_parser.add_argument(
            "--reveal-secrets",
            action="store_true",
            required=False,
            default=False,
            help="print sensitive values instead of redacting them (local debugging only).",
        )
        show_parser.set_defaults(func=ConfigCommands.run_show)

        set_parser = config_subparsers.add_parser(
            "set",
            help="set one config key in config.json without overwriting other keys.",
        )
        set_parser.add_argument(
            "--key",
            required=True,
            default=None,
            help="supported config key to set.",
        )
        set_parser.add_argument(
            "--value",
            required=True,
            default=None,
            help="value to store for the config key.",
        )
        set_parser.set_defaults(func=ConfigCommands.run_set)

        unset_parser = config_subparsers.add_parser(
            "unset",
            help="remove one config key from config.json.",
        )
        unset_parser.add_argument(
            "--key",
            required=True,
            default=None,
            help="supported config key to remove.",
        )
        unset_parser.set_defaults(func=ConfigCommands.run_unset)

    @staticmethod
    def run_init_config_file(args: Any) -> None:
        LocalLogging.bootstrap()
        config_service = ConfigService()
        config_path = config_service.init_config_file(
            config_path=args.config_file_path,
            dot_env_file=args.dot_env_file,
        )
        print(config_path)

    @staticmethod
    def run_show(args: Any) -> None:
        LocalLogging.bootstrap()
        config_service = ConfigService()
        result = config_service.show_config_file(
            config_path=args.config_file_path,
            reveal_secrets=args.reveal_secrets,
        )
        print(json.dumps(result, indent=4, sort_keys=True))

    @staticmethod
    def run_set(args: Any) -> None:
        LocalLogging.bootstrap()
        config_service = ConfigService()
        result = config_service.set_config_value(
            key=args.key,
            value=args.value,
            config_path=args.config_file_path,
        )
        print(json.dumps(result, indent=4, sort_keys=True))

    @staticmethod
    def run_unset(args: Any) -> None:
        LocalLogging.bootstrap()
        config_service = ConfigService()
        result = config_service.unset_config_value(
            key=args.key,
            config_path=args.config_file_path,
        )
        print(json.dumps(result, indent=4, sort_keys=True))

    @staticmethod
    def run_help(args: Any) -> None:
        args.parser.print_help()
