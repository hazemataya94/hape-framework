import os
from typing import Any, Dict, Optional

from dotenv import dotenv_values

from core.config import Config
from core.errors.exceptions import HapeOperationError, HapeValidationError
from core.errors.messages.config_error_messages import get_config_error_message
from core.logging import LocalLogging
from utils.file_manager import FileManager


class ConfigService:
    REDACTED_VALUE = "<redacted>"
    SENSITIVE_CONFIG_KEYS = frozenset(
        {
            "GITLAB_TOKEN",
            "ATLASSIAN_API_KEY",
            "HAPE_GITHUB_TOKEN",
            "HAPE_API_ADMIN_KEY",
            "HAPE_KUBE_AGENT_GRAFANA_TOKEN",
            "HAPE_KUBE_AGENT_GRAFANA_PASSWORD",
        }
    )
    SENSITIVE_KEY_MARKERS = ("TOKEN", "PASSWORD", "SECRET", "PRIVATE_KEY", "API_KEY", "ADMIN_KEY")

    def __init__(self) -> None:
        self.file_manager = FileManager()
        self.logger = LocalLogging.get_logger("hape.config_service")

    @staticmethod
    def _get_parent_dir(path: str) -> str:
        parent_dir = os.path.dirname(path)
        return parent_dir or "."

    @staticmethod
    def _is_sensitive_config_key(key: str) -> bool:
        if key in ConfigService.SENSITIVE_CONFIG_KEYS:
            return True
        upper_key = key.upper()
        return any(marker in upper_key for marker in ConfigService.SENSITIVE_KEY_MARKERS)

    def _build_config_from_env(self, dot_env_file: Optional[str] = None) -> Dict[str, Any]:
        if dot_env_file:
            env_values = dotenv_values(dot_env_file)
            if not env_values:
                raise HapeValidationError(
                    code="CONFIG_ENV_FILE_INVALID",
                    message=get_config_error_message(
                        "CONFIG_ENV_FILE_INVALID",
                        dot_env_file=dot_env_file,
                    ),
                )
        else:
            env_values = dict(os.environ)

        config_data: Dict[str, Any] = {}
        for key in Config.get_supported_config_keys():
            value = env_values.get(key)
            if value in (None, ""):
                continue
            if key in Config.get_int_config_keys():
                try:
                    config_data[key] = int(value)
                except ValueError as exc:
                    raise HapeValidationError(
                        code="CONFIG_ENV_INT_REQUIRED",
                        message=get_config_error_message(
                            "CONFIG_ENV_INT_REQUIRED",
                            config_key=key,
                        ),
                    ) from exc
            else:
                config_data[key] = value
        return config_data

    def _redact_sensitive_values(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        redacted: Dict[str, Any] = {}
        for key, value in config_data.items():
            if self._is_sensitive_config_key(str(key)):
                redacted[key] = self.REDACTED_VALUE
            else:
                redacted[key] = value
        return redacted

    def _read_config_object(self, resolved_path: str) -> Dict[str, Any]:
        if not self.file_manager.file_exists(resolved_path):
            return {}
        try:
            config_data = self.file_manager.read_json_file(resolved_path)
        except ValueError as exc:
            raise HapeValidationError(
                code="CONFIG_FILE_INVALID",
                message=get_config_error_message(
                    "CONFIG_FILE_INVALID",
                    config_path=resolved_path,
                ),
            ) from exc
        if not isinstance(config_data, dict):
            raise HapeValidationError(
                code="CONFIG_FILE_INVALID",
                message=get_config_error_message(
                    "CONFIG_FILE_INVALID",
                    config_path=resolved_path,
                ),
            )
        return config_data

    def _ensure_parent_dir(self, resolved_path: str) -> None:
        parent_dir = self._get_parent_dir(resolved_path)
        try:
            self.file_manager.create_directory(parent_dir)
        except PermissionError as exc:
            raise HapeOperationError(
                code="CONFIG_PERMISSION_DENIED",
                message=get_config_error_message(
                    "CONFIG_PERMISSION_DENIED",
                    parent_dir=parent_dir,
                ),
            ) from exc

    def _validate_supported_key(self, config_key: str) -> str:
        normalized_key = (config_key or "").strip()
        if not normalized_key:
            raise HapeValidationError(
                code="CONFIG_KEY_REQUIRED",
                message=get_config_error_message("CONFIG_KEY_REQUIRED"),
            )
        if normalized_key not in Config.get_supported_config_keys():
            raise HapeValidationError(
                code="CONFIG_KEY_UNSUPPORTED",
                message=get_config_error_message(
                    "CONFIG_KEY_UNSUPPORTED",
                    config_key=normalized_key,
                ),
            )
        return normalized_key

    def _coerce_config_value(self, config_key: str, value: str) -> Any:
        if config_key in Config.get_int_config_keys():
            try:
                return int(value)
            except ValueError as exc:
                raise HapeValidationError(
                    code="CONFIG_ENV_INT_REQUIRED",
                    message=get_config_error_message(
                        "CONFIG_ENV_INT_REQUIRED",
                        config_key=config_key,
                    ),
                ) from exc
        return value

    def init_config_file(self, config_path: Optional[str] = None, dot_env_file: Optional[str] = None) -> str:
        resolved_path = config_path or Config.get_config_path()
        self._ensure_parent_dir(resolved_path)
        config_data = self._build_config_from_env(dot_env_file=dot_env_file)
        self.file_manager.write_json_file(resolved_path, config_data)
        return resolved_path

    def set_config_value(self, key: str, value: str, config_path: Optional[str] = None) -> Dict[str, Any]:
        resolved_path = config_path or Config.get_config_path()
        config_key = self._validate_supported_key(key)
        if value is None or str(value).strip() == "":
            raise HapeValidationError(
                code="CONFIG_VALUE_REQUIRED",
                message=get_config_error_message("CONFIG_VALUE_REQUIRED"),
            )
        coerced_value = self._coerce_config_value(config_key, str(value))
        self.logger.debug("set_config_value(key=%s, config_path=%s)", config_key, resolved_path)
        self._ensure_parent_dir(resolved_path)
        config_data = self._read_config_object(resolved_path)
        config_data[config_key] = coerced_value
        self.file_manager.write_json_file(resolved_path, config_data)
        Config.reload_config()
        return {
            "config_path": resolved_path,
            "key": config_key,
            "updated": True,
            "sensitive": self._is_sensitive_config_key(config_key),
        }

    def unset_config_value(self, key: str, config_path: Optional[str] = None) -> Dict[str, Any]:
        resolved_path = config_path or Config.get_config_path()
        config_key = self._validate_supported_key(key)
        self.logger.debug("unset_config_value(key=%s, config_path=%s)", config_key, resolved_path)
        if not self.file_manager.file_exists(resolved_path):
            raise HapeValidationError(
                code="CONFIG_FILE_NOT_FOUND",
                message=get_config_error_message(
                    "CONFIG_FILE_NOT_FOUND",
                    config_path=resolved_path,
                ),
            )
        config_data = self._read_config_object(resolved_path)
        if config_key not in config_data:
            raise HapeValidationError(
                code="CONFIG_KEY_NOT_PRESENT",
                message=get_config_error_message(
                    "CONFIG_KEY_NOT_PRESENT",
                    config_key=config_key,
                    config_path=resolved_path,
                ),
            )
        del config_data[config_key]
        self.file_manager.write_json_file(resolved_path, config_data)
        Config.reload_config()
        return {
            "config_path": resolved_path,
            "key": config_key,
            "removed": True,
        }

    def show_config_file(self, config_path: Optional[str] = None, reveal_secrets: bool = False) -> Dict[str, Any]:
        resolved_path = config_path or Config.get_config_path()
        self.logger.debug(
            "show_config_file(config_path=%s, reveal_secrets=%s)",
            resolved_path,
            reveal_secrets,
        )
        if not self.file_manager.file_exists(resolved_path):
            raise HapeValidationError(
                code="CONFIG_FILE_NOT_FOUND",
                message=get_config_error_message(
                    "CONFIG_FILE_NOT_FOUND",
                    config_path=resolved_path,
                ),
            )
        config_data = self._read_config_object(resolved_path)
        if reveal_secrets:
            values = config_data
        else:
            values = self._redact_sensitive_values(config_data)
        return {
            "config_path": resolved_path,
            "config": values,
        }
