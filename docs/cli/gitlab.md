# GitLab Automation

## Clone all projects in a group
```
hape gitlab clone --clone-dir /path/to/repos
hape gitlab clone --group-id 88221 --clone-dir /path/to/repos
```

Defaults:
- `--group-id` defaults to `GITLAB_DEFAULT_GROUP_ID` from `config.json`
- `--clone-dir` defaults to `/Users/hazem.ataya/workspace/repos`

## Merge request count per day
```
hape gitlab mr-count-per-day --created-after 01.01.2024 --group-id 88221
```

Options:
- `--created-after` is required and accepts `dd.mm.yyyy`, `dd-mm-yyyy`, or `dd/mm/yyyy`
- Use `--project-id` instead of `--group-id` for a single project
- Exactly one of `--group-id` or `--project-id` is required
- `--username` filters by author (optional)

## Configuration
Requires:
- `HAPE_GITLAB_DOMAIN`
- `GITLAB_TOKEN`
- `GITLAB_DEFAULT_GROUP_ID`
