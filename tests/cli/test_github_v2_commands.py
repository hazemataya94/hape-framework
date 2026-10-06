from __future__ import annotations

import argparse
import json

import cli.commands.github_commands as github_commands_module
from cli.commands.github_commands import GitHubCommands


class _FakeV2Service:
    last_request: dict = {}

    def create_private(self, request: dict) -> dict:
        _FakeV2Service.last_request = request
        return {"envelope_version": "github.v2", "status": "succeeded", "receipt_id": "rec-1"}


def test_v2_create_private_reads_request_file(monkeypatch, tmp_path, capsys) -> None:
    request_path = tmp_path / "create.json"
    request_path.write_text(json.dumps({"authorization_grant": "token", "operation_id": "op-1", "subject_id": "sub-1"}), encoding="utf-8")
    monkeypatch.setattr(github_commands_module, "create_github_v2_service", lambda: _FakeV2Service())
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    GitHubCommands.register(subparsers)
    args = parser.parse_args(["github", "v2", "managed-repository", "create-private", "--request-file-path", str(request_path)])
    args.func(args)
    assert _FakeV2Service.last_request["operation_id"] == "op-1"
    payload = json.loads(capsys.readouterr().out)
    assert payload["envelope_version"] == "github.v2"


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__]))
