ERROR_MESSAGES = {
    "GITHUB_REPO_PATH_NOT_FOUND": "Repository path does not exist: {repo_path}.",
    "GITHUB_REPO_PATH_NOT_DIRECTORY": "Repository path must be a directory: {repo_path}.",
    "GITHUB_REPO_ALREADY_INITIALIZED": "Repository is already initialized with git: {repo_path}.",
    "GITHUB_VISIBILITY_INVALID": "Repository visibility must be private or public. Value is '{visibility}'.",
    "GITHUB_OWNER_UNRESOLVED": "Unable to resolve GitHub owner. Set --owner, HAPE_GITHUB_DEFAULT_OWNER, or use a token with user/org access.",
    "GITHUB_CREATE_REPO_ORG_REQUIRED": "Organization is required for repository creation. Set --org.",
    "GITHUB_CREATE_REPO_NAME_REQUIRED": "Repository name is required for repository creation. Set --name.",
    "GITHUB_CREATE_REPO_FAILED": "Failed to create GitHub repository '{owner}/{repo_name}'.",
    "GITHUB_CREATE_REPO_FAILED_WITH_REASON": "Failed to create GitHub repository '{owner}/{repo_name}'. Reason: {reason}.",
    "GITHUB_CREATE_REPO_INVALID_RESPONSE": "GitHub create repository response is invalid for '{owner}/{repo_name}'.",
    "GITHUB_LOCAL_GIT_INIT_FAILED": "Failed to initialize local git repository at {repo_path}.",
    "GITHUB_GLOBAL_GIT_EMAIL_UNAVAILABLE": "Unable to read global git email from host. Run 'git config --global user.email <email>' and retry.",
    "GITHUB_USER_LOOKUP_FAILED": "Failed to resolve GitHub user login for email '{email}'.",
    "GITHUB_USER_LOGIN_UNRESOLVED": "Could not resolve any GitHub login for host global git email '{email}'.",
    "GITHUB_ADD_ADMIN_COLLABORATOR_FAILED": "Failed to add GitHub admin collaborator '{username}' to '{owner}/{repo_name}'.",
    "GITHUB_LIST_REPO_SCOPE_INVALID": "Repository scope must be 'user' or 'org'. Value is '{scope}'.",
    "GITHUB_LIST_REPO_ORG_NAME_REQUIRED": "Organization name is required when repository scope is 'org'. Set --org.",
    "GITHUB_LIST_REPOS_FAILED": "Failed to list GitHub repositories for scope '{scope}' and target '{scope_target}'.",
    "GITHUB_AUTHENTICATED_USER_INFO_FAILED": "Failed to fetch authenticated GitHub user information.",
    "GITHUB_DELETE_REPOS_ORG_REQUIRED": "Organization is required for repository deletion. Set --org.",
    "GITHUB_DELETE_REPOS_SELECTION_REQUIRED": "Select repositories to delete using --all or --include.",
    "GITHUB_DELETE_REPOS_INCLUDE_NOT_FOUND": "Requested repositories in --include were not found in the organization: {missing}.",
    "GITHUB_DELETE_REPOS_EMPTY_AFTER_FILTERS": "No repositories remain for deletion after applying include/exclude filters.",
    "GITHUB_DELETE_REPOS_CONFIRMATION_MISMATCH": "Deletion cancelled. Confirmation phrase does not match. Expected phrase: '{expected_phrase}'.",
    "GITHUB_DELETE_REPOS_LIST_FAILED": "Failed to list organization repositories for deletion in '{org}'.",
    "GITHUB_DELETE_REPO_FAILED": "Failed to delete GitHub repository '{full_name}'.",
    "GITHUB_CLONE_REPOS_ORG_REQUIRED": "Organization is required for cloning repositories. Set --org.",
    "GITHUB_CLONE_REPOS_DIR_REQUIRED": "Clone directory is required. Set --clone-dir.",
    "GITHUB_CLONE_REPO_FAILED": "Failed to clone GitHub repository '{full_name}'.",
}


def get_github_error_message(message_key: str, **kwargs: str) -> str:
    template = ERROR_MESSAGES.get(message_key, "Unknown GitHub error.")
    return template.format(**kwargs)


if __name__ == "__main__":
    print(get_github_error_message("GITHUB_REPO_PATH_NOT_FOUND", repo_path="/path/to/repo"))
