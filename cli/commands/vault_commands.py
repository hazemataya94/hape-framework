import argparse
import json
from typing import Any

from core.logging import LocalLogging
from services.vault_service import VaultService


class VaultCommands:
    @staticmethod
    def register(subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            "vault",
            help="authenticate to Vault as the platform agent and read KV fields.",
        )
        parser.set_defaults(func=VaultCommands.run_help, parser=parser)
        vault_subparsers = parser.add_subparsers(
            dest="vault_command",
            metavar="command",
        )
        vault_subparsers.required = False

        get_parser = vault_subparsers.add_parser(
            "kv-get",
            help="login with AppRole and print one Vault KV field value.",
        )
        get_parser.add_argument(
            "--secret-id-file",
            required=False,
            default=None,
            help="path to AppRole secret_id file (default: HAPE_VAULT_SECRET_ID_FILE or HAPE_WORKSPACE_ROOT/secret.id).",
        )
        get_parser.add_argument(
            "--role-id",
            required=False,
            default=None,
            help="AppRole role_id override (default: HAPE_VAULT_ROLE_ID).",
        )
        get_parser.add_argument(
            "--vault-addr",
            required=False,
            default=None,
            help="Vault address override (default: HAPE_VAULT_ADDR or https://vault.example.com).",
        )
        get_parser.add_argument(
            "--auth-path",
            required=False,
            default=None,
            help="AppRole auth mount path override (default: HAPE_VAULT_AUTH_PATH or approle).",
        )
        get_parser.add_argument(
            "--kv-mount",
            required=False,
            default=None,
            help="KV v2 mount override (default: HAPE_VAULT_KV_MOUNT or kv).",
        )
        get_parser.add_argument(
            "--kv-path",
            required=False,
            default=None,
            help="KV relative path override (default: HAPE_VAULT_KV_PATH or example/pypi).",
        )
        get_parser.add_argument(
            "--kv-field",
            required=False,
            default=None,
            help="KV field name override (default: HAPE_VAULT_KV_FIELD or token).",
        )
        get_parser.add_argument(
            "--omit-value",
            action="store_true",
            required=False,
            default=False,
            help="return retrieval metadata without printing the secret value.",
        )
        get_parser.set_defaults(func=VaultCommands.run_kv_get)

    @staticmethod
    def run_help(args: Any) -> None:
        args.parser.print_help()

    @staticmethod
    def run_kv_get(args: Any) -> None:
        LocalLogging.bootstrap()
        vault_service = VaultService()
        result = vault_service.kv_get(
            omit_value=args.omit_value,
            vault_addr=args.vault_addr,
            role_id=args.role_id,
            secret_id_file=args.secret_id_file,
            auth_path=args.auth_path,
            kv_mount=args.kv_mount,
            kv_relative_path=args.kv_path,
            kv_field=args.kv_field,
        )
        if args.omit_value:
            print(json.dumps(result, indent=2, sort_keys=True))
            return
        print(result["value"], end="")


if __name__ == "__main__":
    print(VaultCommands)
