# Purpose
Apply these rules when changing code in this repository.

# Repository safety
- Always ignore any virtual environment files (for example `.venv`, `.exec-venv`). Do not modify them. Only scan or read when necessary and more efficient for llm usage than any other available method.

# Restructuring and file moves
- When the task is repository restructuring or moving files, use filesystem commands (`mkdir`, `mv`, `rm`) for the move operation.
- After file moves, validate the result by checking that new paths exist and old paths are removed.
- For move-focused tasks, avoid rewriting full code files when import/path updates are sufficient.

# Typing and return values
- Add type annotations for function parameters and return values.
- Functions that aggregate counts across keys should return `collections.Counter`.

# Function and class organization
- Use blank lines to separate logical code sections.
- Always, Hard Rule: In classes, place private methods before public methods.
- For any newly created Python module, include an `if __name__ == "__main__":` block that exercises all public functions; if it doesn’t exist, add it.
- For new classes, define default values as class-level constants and reference them in `__init__` defaults.

# Naming conventions
- Use snake_case variable names and CamelCase class names.
- When instantiating a class, name the variable as snake_case of the class name (example: `MyService` -> `my_service = MyService(...)`).
- Logger names for classes should use `hape.<class_name_snake_case>`.
- In `utils`, if a class has only static methods then it must be named `*Utils`. If it has instance methods and an `__init__`, it must be named `*Manager`.

# HTTP and logging behavior
- When using `requests`, call `response.raise_for_status()` before parsing response data.
- Use logging (not print) in all modules for debug and failure context. Except for core and utils modules, don't implement logging for them.
- For newly created code, add logging and service-layer error handling.
- Before implementing logging in new code, consult `docs/dev/logging-guide.md` (and `docs/dev/code-policy-error-handling.md` when relevant); if docs are insufficient, mirror patterns from existing HAPE classes.

# Runtime and command output
- Use the HAPE virtual environment for Python execution.
- Hard rule: In `hape-framework`, command examples in documentation must use `python` (never `python3`).
- In CLI files (`cli/*.py`), include `required`, `default`, and `help` for each `add_argument` call when applicable.
- In CLI files (`cli/*.py`), write all `add_argument` calls in multiline form.
- In CLI files (`cli/*.py`), `add_argument` should always define arguments as flags (no positional args) in kebab-case (for example, `--argument-name`).

# Formatting preferences
- Hard rule (pass/fail): function and class signatures MUST stay on one line when the full signature length is <= 200 characters.
- Hard rule (pass/fail): multi-line function/class signatures are allowed only when the full single-line signature length would be > 200 characters.
- Hard rule (pass/fail): if a function/class signature is split across lines while length is <= 200 characters, it is invalid and MUST be rewritten to one line.
- Prefer one f-string over concatenating multiple formatted string fragments.

# Mandatory self-check before final response
- Before final response, scan all edited Python files and fix every function/class signature that is multi-line while length is <= 200 characters.
- After running all code checks, always run `python scripts/check_hape_rules.py` as a final validation step and fix all reported violations before final response.
