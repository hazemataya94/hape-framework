import json
from pathlib import Path

import pytest

from core.errors.exceptions import HapeValidationError
from services.config_service import ConfigService


def test_show_config_file_redacts_sensitive_values(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "HAPE_GITLAB_DOMAIN": "https://gitlab.example.com",
                "GITLAB_TOKEN": "super-secret-token",
                "HAPE_API_PORT": 8080,
            }
        ),
        encoding="utf-8",
    )
    config_service = ConfigService()
    result = config_service.show_config_file(config_path=str(config_path), reveal_secrets=False)
    assert result["config_path"] == str(config_path)
    assert result["config"]["HAPE_GITLAB_DOMAIN"] == "https://gitlab.example.com"
    assert result["config"]["HAPE_API_PORT"] == 8080
    assert result["config"]["GITLAB_TOKEN"] == ConfigService.REDACTED_VALUE


def test_show_config_file_reveal_secrets(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"GITLAB_TOKEN": "super-secret-token"}),
        encoding="utf-8",
    )
    config_service = ConfigService()
    result = config_service.show_config_file(config_path=str(config_path), reveal_secrets=True)
    assert result["config"]["GITLAB_TOKEN"] == "super-secret-token"


def test_show_config_file_missing_raises(tmp_path: Path) -> None:
    config_service = ConfigService()
    missing_path = str(tmp_path / "missing.json")
    with pytest.raises(HapeValidationError) as exc_info:
        config_service.show_config_file(config_path=missing_path)
    assert exc_info.value.code == "CONFIG_FILE_NOT_FOUND"


def test_show_config_file_invalid_json_raises(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text("{not-json", encoding="utf-8")
    config_service = ConfigService()
    with pytest.raises(HapeValidationError) as exc_info:
        config_service.show_config_file(config_path=str(config_path))
    assert exc_info.value.code == "CONFIG_FILE_INVALID"


def test_set_config_value_merges_without_overwrite(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "HAPE_GITLAB_DOMAIN": "https://gitlab.example.com",
                "HAPE_API_PORT": 8080,
            }
        ),
        encoding="utf-8",
    )
    config_service = ConfigService()
    result = config_service.set_config_value(
        key="HAPE_GITHUB_DEFAULT_OWNER",
        value="hape-academy",
        config_path=str(config_path),
    )
    assert result["key"] == "HAPE_GITHUB_DEFAULT_OWNER"
    assert result["updated"] is True
    assert result["sensitive"] is False
    stored = json.loads(config_path.read_text(encoding="utf-8"))
    assert stored["HAPE_GITLAB_DOMAIN"] == "https://gitlab.example.com"
    assert stored["HAPE_API_PORT"] == 8080
    assert stored["HAPE_GITHUB_DEFAULT_OWNER"] == "hape-academy"


def test_set_config_value_creates_file_and_redacts_sensitive_marker(tmp_path: Path) -> None:
    config_path = tmp_path / "nested" / "config.json"
    config_service = ConfigService()
    result = config_service.set_config_value(
        key="HAPE_GITHUB_TOKEN",
        value="ghp_example_token_value",
        config_path=str(config_path),
    )
    assert result["sensitive"] is True
    stored = json.loads(config_path.read_text(encoding="utf-8"))
    assert stored["HAPE_GITHUB_TOKEN"] == "ghp_example_token_value"


def test_set_config_value_rejects_unsupported_key(tmp_path: Path) -> None:
    config_service = ConfigService()
    with pytest.raises(HapeValidationError) as exc_info:
        config_service.set_config_value(
            key="NOT_A_REAL_KEY",
            value="x",
            config_path=str(tmp_path / "config.json"),
        )
    assert exc_info.value.code == "CONFIG_KEY_UNSUPPORTED"


def test_unset_config_value_removes_key(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "HAPE_GITHUB_DEFAULT_OWNER": "hape-academy",
                "HAPE_API_PORT": 8080,
            }
        ),
        encoding="utf-8",
    )
    config_service = ConfigService()
    result = config_service.unset_config_value(
        key="HAPE_GITHUB_DEFAULT_OWNER",
        config_path=str(config_path),
    )
    assert result["removed"] is True
    stored = json.loads(config_path.read_text(encoding="utf-8"))
    assert "HAPE_GITHUB_DEFAULT_OWNER" not in stored
    assert stored["HAPE_API_PORT"] == 8080


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
