# Build and Install

Avoid installing Python packages into the system interpreter, because it can break OS-managed tools and create version conflicts.

## Virtual environments

Splitting build and runtime environments keeps development/build dependencies out of the execution environment and reduces dependency drift.

Use two virtual environments:
- `.venv` for coding, development, and build steps
- `.exec-venv` for installing and running the executable

## Build
Create distributable build artifacts in the `dist/` directory.

```
source .venv/bin/activate
python -m pip install -r requirements-build.txt
make build
```

## Install
Place the built package into the runtime venv where the executable is used.

```
source .exec-venv/bin/activate
make install
```

## Shell alias
Add an alias to your shell rc file based on the shell you use:
- zsh: `~/.zshrc`
- bash: `~/.bashrc`
- other shells: `~/.<shell>rc`

Example alias:
```
alias hape="<path-to-hape-repo>/.exec-venv/bin/hape"
```

Then reload your shell config:
```
source ~/.zshrc
# or
source ~/.bashrc
# or
source ~/.<shell>rc
```
