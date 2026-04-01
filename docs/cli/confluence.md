# Confluence Automation

## Get a page
Fetch a Confluence page by ID and print the JSON response.

Command:
```
hape confluence get-page --page-id 123456 --expand body.storage
```

Defaults:
- Expand: `body.storage`

## Create a page
Create a Confluence page under a parent page ID.

Command:
```
hape confluence create-page --parent-page-id 123456 --page-title "Page Title" --page-body "<p>body</p>"
```

Optional:
- `--labels` (zero or more)

## Create a page from Markdown
Convert a Markdown file to Confluence storage format and create a page.

Command:
```
hape confluence md-to-page --md-path /path/to/file.md
```

Defaults:
- Parent page ID: `CONFLUENCE_TEST_PARENT_PAGE_ID` from config.json
- README path: `README.md`
Optional:
- `--labels` (zero or more)

## Mermaid
Mermaid blocks are converted to Confluence Mermaid macros.
The macro must be enabled in your Confluence instance.

## Notes
- Tables are converted by the Markdown parser.
- Page width is set to full width after creation.
