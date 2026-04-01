# Markdown Automation

## Export markdown tables to CSV
Export all standard pipe tables from a markdown file into CSV files.
Each CSV file name uses the markdown file stem with a counter suffix.

Command:
```
hape markdown export-tables-to-csv --md-file /path/to/file.md --output-dir /path/to/output
```

Output naming:
- `file_01.csv`
- `file_02.csv`
- `file_03.csv`

Optional:
- `--delimiter` (default: `,`)

## Import CSV as markdown table
Append a CSV file into a markdown file as a markdown table.
If target markdown file does not exist, hape creates it.

Command:
```
hape markdown import-csv-table --csv-file /path/to/input.csv --md-file /path/to/target.md
```

Optional:
- `--delimiter` (default: `,`)
- `--table-title` (default heading: `## Table: <csv filename without extension>`)

Append format:
- Adds a heading before each imported table.
- Uses blank line separators between existing content and appended table block.
