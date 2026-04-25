# CLI Usage

## Global options
- `--version` prints the installed version.
- `--config-file-path` overrides the default config path (`~/.hape/config.json`).

## Help
```
hape --help
hape {command} --help
hape {command} {sub-command} --help
```

## Command layout
Commands are grouped by integration. Each group has subcommands where needed.

## Commands
- `config` - [config.md](config.md)
- `gitlab` - [gitlab.md](gitlab.md)
- `github` - [github.md](github.md)
- `jira` - [jira.md](jira.md)
- `confluence` - [confluence.md](confluence.md)
- `csv` - [csv.md](csv.md)
- `dora` - [dora.md](dora.md)
- `eks-deployment-cost` - [eks-deployment-cost.md](eks-deployment-cost.md)
- `markdown` - [markdown.md](markdown.md)
- `kube-agent` - [kube-agent.md](kube-agent.md)

Argument and validation errors print command help automatically.

## Error Handling
- Runtime errors are handled centrally by HAPE core.
- Known HAPE errors print a user-friendly message and return a stable exit code.
- Unknown errors print a generic message and return exit code `99`.
