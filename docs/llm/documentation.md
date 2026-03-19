# HAPE Documentation Rules

Apply these rules when creating or updating documentation in this repository.

## Documentation updates
- Update relevant documentation for every implemented change.
- If a change modifies `infrastructure/`, always update corresponding pages under `docs/infra/` in the same change.
- If a change modifies `Makefile`, always update `docs/makefile.md` in the same change.
- Use simple, clear words and short sentences; avoid ambiguous words (`it`, `this`, `that`, `soon`, `latest`, `correct`).
- Write explicit statements with subject, condition, and expected result; prefer simple words (`fix` over `resolve`, `use` over `utilize`).
- For documents under `docs/ops/`, add a Mermaid flowchart when it helps provide a clear general workflow overview.

## Command examples in docs
- When writing documentation command examples for Python, always use `python` (never virtualenv-prefixed interpreter paths or `python3`).
- Keep commands copy-paste ready from repository root unless a different working directory is required.

## Demo README requirements
- Every feature demo under `demos/` must include a README with complete end-to-end reproduction instructions so a user can run the full workflow independently.
- Demo README steps must include: prerequisites, environment setup, infrastructure startup commands (when needed), feature execution commands, artifact locations, verification checks, and cleanup steps.
- Demo README instructions must be concrete and executable from repository root without relying on implicit context.
- Demo README files must include screenshots (or equivalent visual output captures) that show the feature outputs after successful execution.
- In demo READMEs, place the `Screenshots` section immediately after `Prerequisites`.
- For exporter demos, use the Kubernetes runtime-source deployment pattern (ConfigMap + initContainer dependencies) and avoid Docker build/load steps in README instructions unless explicitly required by the feature.
- Once a demo folder is created, do not modify it for new feature demonstrations.
- For any new or changed feature demonstration, create a new demo folder by default.
