import argparse

import pytest

import cli.commands.init_cicd_commands as init_cicd_commands_module
from cli.commands.init_cicd_commands import InitCicdCommands


class _FakeInitCicdResult:
    def __init__(self) -> None:
        self.project_path = "/tmp/react-app"
        self.deployment_type = "kubernetes"
        self.framework = "reactjs"
        self.build_flavor = "vite"
        self.created_files = ["deployments/deployment.yaml", "Dockerfile"]
        self.skipped_files = []
        self.warnings = []


class _FakeInitCicdService:
    last_project_path = None
    last_deployment_type = None

    def init_cicd(self, project_path: str, deployment_type: str):
        _FakeInitCicdService.last_project_path = project_path
        _FakeInitCicdService.last_deployment_type = deployment_type
        return _FakeInitCicdResult()


def test_init_cicd_cli_invokes_service(monkeypatch, capsys) -> None:
    monkeypatch.setattr(init_cicd_commands_module, "InitCicdService", _FakeInitCicdService)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    InitCicdCommands.register(subparsers)
    args = parser.parse_args(["init-cicd", "--project-path", "/tmp/react-app", "--deployment-type", "kubernetes"])
    args.func(args)
    output = capsys.readouterr().out
    assert "Init CI/CD" in output
    assert "Project: /tmp/react-app" in output
    assert "Deployment type: kubernetes" in output
    assert _FakeInitCicdService.last_project_path == "/tmp/react-app"
    assert _FakeInitCicdService.last_deployment_type == "kubernetes"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
