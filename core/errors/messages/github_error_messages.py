ERROR_MESSAGES = {
    "GITHUB_REPO_PATH_NOT_FOUND": "Repository path does not exist: {repo_path}.",
    "GITHUB_REPO_PATH_NOT_DIRECTORY": "Repository path must be a directory: {repo_path}.",
    "GITHUB_REPO_ALREADY_INITIALIZED": "Repository is already initialized with git: {repo_path}.",
    "GITHUB_VISIBILITY_INVALID": "Repository visibility must be private or public. Value is '{visibility}'.",
    "GITHUB_OWNER_UNRESOLVED": "Unable to resolve GitHub owner. Set --owner, HAPE_GITHUB_DEFAULT_OWNER, or use a token with user/org access.",
    "GITHUB_CREATE_REPO_FAILED": "Failed to create GitHub repository '{owner}/{repo_name}'.",
    "GITHUB_CREATE_REPO_FAILED_WITH_REASON": "Failed to create GitHub repository '{owner}/{repo_name}'. Reason: {reason}.",
    "GITHUB_CREATE_REPO_INVALID_RESPONSE": "GitHub create repository response is invalid for '{owner}/{repo_name}'.",
    "GITHUB_LOCAL_GIT_INIT_FAILED": "Failed to initialize local git repository at {repo_path}.",
}


def get_github_error_message(message_key: str, **kwargs: str) -> str:
    template = ERROR_MESSAGES.get(message_key, "Unknown GitHub error.")
    return template.format(**kwargs)


if __name__ == "__main__":
    print(get_github_error_message("GITHUB_REPO_PATH_NOT_FOUND", repo_path="/path/to/repo"))
