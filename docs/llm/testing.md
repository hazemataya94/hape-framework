# HAPE Testing Rules

Apply these rules when creating, updating, or running tests in this repository.

## Hard rules
- Hard rule: Prefer local functional tests and use `kind` for Kubernetes and EKS-like workflows.
- Hard rule: Do not create, update, or depend on real EKS clusters unless the user explicitly requests it.
- Hard rule: Default test flows must avoid billable cloud resources and external infrastructure dependencies.
- Hard rule: For cloud-related logic, use local validation plus mocks/stubs when behavior can be verified locally.
- Hard rule: For multi-node behavior, define node topology in versioned `kind` config and simulate EKS metadata with worker node labels.
- Hard rule: Functional test suites must be opt-in via environment flags and must default to cleanup after test completion.
- Hard rule: Never use `-q` in pytest commands for documentation, examples, or execution steps.
- Hard rule: For every new feature, add functional tests when the feature has runtime behavior that can be validated on local `kind`.
- Hard rule: For every new command, endpoint, service/client behavior, or other created runtime feature, add or update automated tests in the same change set.
- Hard rule: Functional tests for new features must generate real output artifacts (for example JSON, Markdown, CSV, or text outputs), not only in-memory assertions.
- Hard rule: New feature demos under `demos/` must be created from generated functional test artifacts.

## Validation requirements
- Validate output behavior, not only implementation details.
- Assert sorting and projection formulas for cost-report features.
- Verify missing request handling and default replica behavior.
- Keep tests deterministic, isolated, and repeatable on a developer laptop.

## Documentation requirements
- Keep a test README per functional suite with prerequisites, run commands, and cleanup behavior.
- State clearly that local tests do not require EKS unless explicitly requested.
- Test README files must include explicit instructions to run the feature tests on local `kind` (including cluster startup command such as `make kind-up` when applicable).
- When functional tests generate artifacts, document artifact file names and where they are written.

## Mandatory self-check before final response
- Confirm the test approach uses local `kind` and does not require EKS by default.
- Confirm default test commands do not create billable cloud resources.
- Confirm the functional test README includes local run and cleanup instructions.
- Confirm functional tests for new feature work generate real artifacts and demos are derived from those artifacts.
