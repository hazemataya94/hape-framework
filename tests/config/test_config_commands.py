import argparse
import json

import pytest

import cli.commands.config_commands as config_commands_module
from cli.commands.config_commands import ConfigCommands
from services.config_service import ConfigService


class _FakeConfigService:
    last_show_call: dict[str, object] = {}

    def show_config_file(self, config_path: str | None = None, reveal_secrets: bool = False) -> dict[str, object]:
        _FakeConfigService.last_show_call = {
            "config_path": config_path,
            "reveal_secrets": reveal_secrets,
        }
        return {
            "config_path": config_path or "/tmp/config.json",
            "config": {
                "HAPE_GITLAB_DOMAIN": "https://gitlab.example.com",
                "GITLAB_TOKEN": ConfigService.REDACTED_VALUE,
            },
        }


def test_config_show_cli_prints_json(monkeypatch, capsys) -> None:
    monkeypatch.setattr(config_commands_module, "ConfigService", _FakeConfigService)
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-file-path", required=False, default=None)
    subparsers = parser.add_subparsers(dest="command")
    ConfigCommands.register(subparsers)
    args = parser.parse_args(
        ["--config-file-path", "/tmp/custom-config.json", "config", "show", "--reveal-secrets"]
    )
    args.func(args)
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["config_path"] == "/tmp/custom-config.json"
    assert payload["config"]["GITLAB_TOKEN"] == ConfigService.REDACTED_VALUE
    assert _FakeConfigService.last_show_call["config_path"] == "/tmp/custom-config.json"
    assert _FakeConfigService.last_show_call["reveal_secrets"] is True


def test_config_show_registers_parser() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-file-path", required=False, default=None)
    subparsers = parser.add_subparsers(dest="command")
    ConfigCommands.register(subparsers)
    args = parser.parse_args(["config", "show"])
    assert args.config_command == "show"
    assert args.reveal_secrets is False
    assert args.func == ConfigCommands.run_show


def test_config_set_and_unset_register_parsers() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-file-path", required=False, default=None)
    subparsers = parser.add_subparsers(dest="command")
    ConfigCommands.register(subparsers)
    set_args = parser.parse_args(
        ["config", "set", "--key", "HAPE_GITHUB_DEFAULT_OWNER", "--value", "example-org"]
    )
    unset_args = parser.parse_args(["config", "unset", "--key", "HAPE_GITHUB_TOKEN"])
    assert set_args.func == ConfigCommands.run_set
    assert set_args.key == "HAPE_GITHUB_DEFAULT_OWNER"
    assert set_args.value == "example-org"
    assert unset_args.func == ConfigCommands.run_unset
    assert unset_args.key == "HAPE_GITHUB_TOKEN"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
