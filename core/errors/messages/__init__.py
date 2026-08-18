"""Domain error message catalogs."""

from core.errors.messages.config_error_messages import get_config_error_message
from core.errors.messages.confluence_error_messages import get_confluence_error_message
from core.errors.messages.gitlab_error_messages import get_gitlab_error_message
from core.errors.messages.github_error_messages import get_github_error_message
from core.errors.messages.jira_error_messages import get_jira_error_message
from core.errors.messages.linkedin_error_messages import get_linkedin_error_message
from core.errors.messages.csv_error_messages import get_csv_error_message
from core.errors.messages.ecr_error_messages import get_ecr_error_message
from core.errors.messages.vault_error_messages import get_vault_error_message
from core.errors.messages.eks_deployment_cost_error_messages import get_eks_deployment_cost_error_message
from core.errors.messages.markdown_error_messages import get_markdown_error_message

__all__ = [
    "get_config_error_message",
    "get_confluence_error_message",
    "get_gitlab_error_message",
    "get_github_error_message",
    "get_jira_error_message",
    "get_linkedin_error_message",
    "get_csv_error_message",
    "get_ecr_error_message",
    "get_vault_error_message",
    "get_eks_deployment_cost_error_message",
    "get_markdown_error_message",
]


if __name__ == "__main__":
    print(get_config_error_message("CONFIG_ENV_INT_REQUIRED"))
