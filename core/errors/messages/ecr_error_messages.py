ERROR_MESSAGES = {
    "ECR_METADATA_REQUIRED": "Metadata path is required.",
    "ECR_METADATA_NOT_FOUND": "Metadata file not found: {metadata_path}.",
    "ECR_METADATA_INVALID_JSON": "Metadata file is not valid JSON: {metadata_path}.",
    "ECR_METADATA_INVALID": "Metadata validation failed: {reason}.",
    "ECR_PROVIDER_UNSUPPORTED": "Registry provider '{provider}' is unsupported. Only 'ecr' is supported.",
    "ECR_REGION_REQUIRED": "ECR region is required from metadata.registry.region or --region.",
    "ECR_REPOSITORIES_EMPTY": "No enabled ECR repositories were selected from metadata.",
    "ECR_SERVICES_UNKNOWN": "Unknown service names in --services: {services}.",
    "ECR_ENSURE_CANCELLED": "ECR ensure-repos cancelled before any create.",
    "ECR_DESCRIBE_FAILED": "Failed to describe ECR repository '{repository_name}' in region '{region}'.",
    "ECR_CREATE_FAILED": "Failed to create ECR repository '{repository_name}' in region '{region}'.",
    "ECR_ACCOUNT_LOOKUP_FAILED": "Failed to resolve AWS caller identity for the ensure plan.",
}


def get_ecr_error_message(message_key: str, **kwargs: str) -> str:
    template = ERROR_MESSAGES.get(message_key, "Unknown ECR error.")
    return template.format(**kwargs)


if __name__ == "__main__":
    print(get_ecr_error_message("ECR_ENSURE_CANCELLED"))
