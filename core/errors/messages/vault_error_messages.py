ERROR_MESSAGES = {
    "VAULT_ROLE_ID_REQUIRED": "HAPE_VAULT_ROLE_ID is required for AppRole login.",
    "VAULT_SECRET_ID_FILE_REQUIRED": "AppRole secret_id file is required. Set HAPE_VAULT_SECRET_ID_FILE or HAPE_WORKSPACE_ROOT.",
    "VAULT_SECRET_ID_FILE_NOT_FOUND": "AppRole secret_id file not found: {secret_id_file}.",
    "VAULT_SECRET_ID_FILE_EMPTY": "AppRole secret_id file is empty: {secret_id_file}.",
    "VAULT_LOGIN_FAILED": "Vault AppRole login failed.",
    "VAULT_KV_READ_FAILED": "Failed to read Vault KV path '{kv_path}'.",
}


def get_vault_error_message(message_key: str, **kwargs: str) -> str:
    template = ERROR_MESSAGES.get(message_key, "Unknown Vault error.")
    return template.format(**kwargs)


if __name__ == "__main__":
    print(get_vault_error_message("VAULT_ROLE_ID_REQUIRED"))
