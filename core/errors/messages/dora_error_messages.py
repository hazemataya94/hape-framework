ERROR_MESSAGES = {
    "DORA_CONFIG_PATH_REQUIRED": "DORA config path is required for {config_name}.",
    "DORA_CONFIG_NOT_FOUND": "DORA config file does not exist: {path}.",
    "DORA_CONFIG_INVALID_JSON": "DORA config file is not valid JSON: {path}.",
    "DORA_CONFIG_INVALID_SCHEMA": "DORA config schema is invalid: {reason}.",
    "DORA_PROJECT_RULES_MISSING_REFS": "Project '{project_path}' must define explicit refs.",
    "DORA_PROJECT_RULES_MISSING_PROJECT": "Project '{project_path}' is referenced in mappings but not in git rules.",
    "DORA_GITLAB_FETCH_FAILED": "Failed to fetch GitLab provider data for group_id={group_id}.",
    "DORA_GITHUB_FETCH_FAILED": "Failed to fetch GitHub provider data for organization={scope}.",
    "DORA_PROMETHEUS_QUERY_FAILED": "Prometheus query failed for project '{project_path}'.",
}


def get_dora_error_message(message_key: str, **kwargs: str) -> str:
    template = ERROR_MESSAGES.get(message_key, "Unknown DORA error.")
    return template.format(**kwargs)


if __name__ == "__main__":
    print(get_dora_error_message("DORA_CONFIG_PATH_REQUIRED", config_name="git rules"))
