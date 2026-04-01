# HAPE Documentation Rules

Apply these rules when creating or updating documentation in this repository.

## Documentation updates
- Update relevant documentation for every implemented change.
- If a change modifies `infrastructure/`, always update corresponding pages under `docs/infra/` in the same change.
- If a change modifies `Makefile`, always update `docs/makefile.md` in the same change.
- Use simple, clear words and short sentences; avoid ambiguous words (`it`, `this`, `that`, `soon`, `latest`, `correct`).
- Write explicit statements with subject, condition, and expected result; prefer simple words (`fix` over `resolve`, `use` over `utilize`).
- For documents under `docs/services/`, add a Mermaid flowchart when it helps provide a clear general workflow overview.
- For every new or updated file under `docs/services/`, always include a final `## Related documentation` section with links to the most relevant docs under `docs/cli/`, `docs/infra/`, `docs/exporters/`, and `docs/architectures/` when applicable.

## Command examples in docs
- When writing documentation command examples for Python, always use `python` (never virtualenv-prefixed interpreter paths or `python3`).
- Keep commands copy-paste ready from repository root unless a different working directory is required.

## Demo README requirements
- Every feature demo under `demos/` must include a README with complete end-to-end reproduction instructions so a user can run the full workflow independently.
- Demo README steps must include: prerequisites, environment setup, infrastructure startup commands (when needed), feature execution commands, artifact locations, verification checks, and cleanup steps.
- Demo README instructions must be concrete and executable from repository root without relying on implicit context.
- Demo README files must include screenshots (or equivalent visual output captures) that show the feature outputs after successful execution.
- Every demo README under `demos/*/README.md` must include a `## Files` section.
- In demo READMEs, place the `Screenshots` section immediately after the `Files` section.
- For exporter demos, use the Kubernetes runtime-source deployment pattern (ConfigMap + initContainer dependencies) and avoid Docker build/load steps in README instructions unless explicitly required by the feature.
- Every demo README under `demos/*/README.md` must end with a final `## Related documentation` section linking to the corresponding user guide and service documentation, plus supporting infra/exporter/architecture docs when relevant.
- Once a demo folder is created, do not modify it for new feature demonstrations.
- For any new or changed feature demonstration, create a new demo folder by default.
