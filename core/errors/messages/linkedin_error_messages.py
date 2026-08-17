ERROR_MESSAGES = {
    "LINKEDIN_PROFILE_URL_REQUIRED": "LinkedIn profile URL is required.",
    "LINKEDIN_PROFILE_URL_INVALID": "LinkedIn profile URL must be a public /in/<slug> URL.",
    "LINKEDIN_OUTPUT_DIR_REQUIRED": "Output directory is required.",
    "LINKEDIN_MAX_POSTS_INVALID": "max_posts must be an integer greater than zero.",
    "LINKEDIN_FORMAT_INVALID": "format must be one of: json, markdown, both.",
    "LINKEDIN_PUBLIC_VIEW_UNAVAILABLE": "LinkedIn public view is unavailable for '{profile_url}' (auth wall, challenge, or empty guest page). Run 'hape linkedin posts prepare --profile-url {profile_url}' first, save Recent activity as HTML, then re-run download with --html-file.",
    "LINKEDIN_BROWSER_OPEN_FAILED": "Unable to open a browser for '{url}'. Open that URL manually and follow the printed instructions.",
    "LINKEDIN_FETCH_FAILED": "Failed to fetch LinkedIn public page for '{profile_url}'.",
    "LINKEDIN_PARSE_FAILED": "Failed to parse LinkedIn public posts from '{profile_url}'.",
    "LINKEDIN_WRITE_FAILED": "Failed to write LinkedIn export under '{output_dir}'.",
    "LINKEDIN_HTML_FILE_REQUIRED": "HTML file path is required when using --html-file.",
    "LINKEDIN_HTML_FILE_NOT_FOUND": "HTML file not found: {html_file}",
}


def get_linkedin_error_message(message_key: str, **kwargs: str) -> str:
    template = ERROR_MESSAGES.get(message_key, "Unknown LinkedIn error.")
    return template.format(**kwargs)


if __name__ == "__main__":
    print(get_linkedin_error_message("LINKEDIN_PROFILE_URL_REQUIRED"))
