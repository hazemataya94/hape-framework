ERROR_MESSAGES = {
    "CONFIG_PERMISSION_DENIED": "Permission denied creating '{parent_dir}'. Use --config-file-path with a writable location.",
    "CONFIG_ENV_FILE_INVALID": "Unable to load .env file: {dot_env_file}",
    "CONFIG_ENV_KEY_REQUIRED": "{config_key} must be set in .env.",
    "CONFIG_ENV_INT_REQUIRED": "{config_key} must be an integer in .env.",
    "CONFIG_FILE_NOT_FOUND": "Config file not found: {config_path}. Run 'hape config init-config-file' or pass --config-file-path.",
    "CONFIG_FILE_INVALID": "Config file is missing or not a valid JSON object: {config_path}.",
    "CONFIG_KEY_UNSUPPORTED": "Unsupported config key '{config_key}'. Use a key from Config.get_supported_config_keys().",
    "CONFIG_KEY_REQUIRED": "Config key is required. Set --key.",
    "CONFIG_VALUE_REQUIRED": "Config value is required. Set --value.",
    "CONFIG_KEY_NOT_PRESENT": "Config key '{config_key}' is not present in {config_path}.",
}


def get_config_error_message(message_key: str, **kwargs: str) -> str:
    template = ERROR_MESSAGES.get(message_key, "Unknown config error.")
    return template.format(**kwargs)


if __name__ == "__main__":
    print(get_config_error_message("CONFIG_PERMISSION_DENIED", parent_dir="/tmp"))
