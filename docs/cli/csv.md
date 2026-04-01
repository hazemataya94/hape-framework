# CSV Automation

## Convert JSON to CSV
Convert JSON input into a CSV file.

Use JSON file input:
```
hape csv from-json --json-file /path/to/input.json --output-file /path/to/output.csv
```

Use raw JSON input:
```
hape csv from-json --json-content '[{"name":"alpha","value":1}]' --output-file /path/to/output.csv
```

Rules:
- Provide exactly one source: `--json-file` or `--json-content`.
- `--output-file` is required.
- JSON input must be an array of objects.

Optional:
- `--delimiter` (default: `,`)

## Convert CSV to JSON
Convert CSV input into a JSON file.

Command:
```
hape csv to-json --csv-file /path/to/input.csv --output-file /path/to/output.json
```

Optional:
- `--delimiter` (default: `,`)
