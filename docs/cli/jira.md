# Jira Automation

## Convert Markdown to comment
Converts a Markdown file into Jira wiki markup and posts it as a comment.
Mermaid blocks are rendered to PNG and attached to the issue, then referenced in the comment.

Command:
```
hape jira md-to-comment --issue-key SPACE-123 --md-path /path/to/file.md
```

## Mermaid rendering (local)
Mermaid diagrams are rendered locally (no network calls).

Backend selection (first match wins):
1. `mmdc` in PATH (install via npm)
2. `docker` in PATH (runs the mermaid-cli container)

Install `mmdc` (recommended):
```
npm install -g @mermaid-js/mermaid-cli
mmdc -h
```

Use Docker (no Node install):
```
docker pull ghcr.io/mermaid-js/mermaid-cli/mermaid-cli
```

Notes:
- Jira comments do not support Confluence storage macros.
- Markdown tables are converted to Jira wiki tables.
