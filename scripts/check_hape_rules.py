#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


SIGNATURE_MAX_LENGTH = 200
SKIP_DIR_NAMES = {".git", ".venv", ".exec-venv", "__pycache__", "dist", "build", ".pytest_cache", "htmlcov"}
TEXT_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".sh", ".cfg", ".ini", ".rst", ".csv", ".html"}
TEXT_FILENAMES = {"Makefile", "Dockerfile", ".gitignore", ".cursorignore"}
DEVICE_PATH_REGEX = re.compile(
    r"/Users/(?P<mac>[A-Za-z0-9._-]+)|/home/(?P<linux>[A-Za-z0-9._-]+)|[A-Za-z]:\\Users\\(?P<win>[A-Za-z0-9._-]+)"
)
PLACEHOLDER_DEVICE_USERS = {"...", "your-user", "username", "you", "hape"}
FORBIDDEN_REAL_DEFAULT_MARKERS = ("vault.hape.dev", "hazemataya/hape")
README_ALLOWLIST_NAMES = {"README.md"}


@dataclass
class Violation:
    file_path: Path
    line: int
    message: str


def _run_git(repo_root: Path, args: list[str]) -> str:
    result = subprocess.run(["git", "-C", str(repo_root), *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return ""
    return result.stdout


def _parse_git_status_paths(status_output: str) -> tuple[set[str], set[str]]:
    changed_paths: set[str] = set()
    new_paths: set[str] = set()
    for raw_line in status_output.splitlines():
        if not raw_line.strip():
            continue
        line = raw_line.rstrip("\n")
        if len(line) < 4:
            continue
        status = line[:2]
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if not path.endswith(".py"):
            continue
        changed_paths.add(path)
        if status in {"??", "A ", " A"}:
            new_paths.add(path)
    return changed_paths, new_paths


def _is_skipped_dir(path: Path) -> bool:
    return any(
        part in SKIP_DIR_NAMES or part.endswith(".egg-info") or part.endswith("venv") or part == "site-packages"
        for part in path.parts
    )


def _get_repo_python_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in repo_root.rglob("*.py"):
        if _is_skipped_dir(path):
            continue
        files.append(path)
    return sorted(files)


def _get_repo_text_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if _is_skipped_dir(path):
            continue
        if path.name in TEXT_FILENAMES or path.suffix in TEXT_SUFFIXES:
            files.append(path)
    return sorted(files)


def _collect_local_path_violations(file_path: Path) -> list[Violation]:
    if file_path.name == "check_hape_rules.py":
        return []
    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    violations: list[Violation] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        for match in DEVICE_PATH_REGEX.finditer(line):
            username = match.group("mac") or match.group("linux") or match.group("win") or ""
            if username in PLACEHOLDER_DEVICE_USERS:
                continue
            violations.append(
                Violation(
                    file_path=file_path,
                    line=line_number,
                    message=(
                        f"local device path '{match.group(0)}' is not allowed in this public repository; "
                        "use a placeholder such as /path/to/..."
                    ),
                )
            )
        if file_path.name not in README_ALLOWLIST_NAMES:
            for marker in FORBIDDEN_REAL_DEFAULT_MARKERS:
                if marker in line:
                    violations.append(
                        Violation(
                            file_path=file_path,
                            line=line_number,
                            message=(
                                f"real environment value '{marker}' is not allowed as a shipped default; "
                                "use a dummy placeholder."
                            ),
                        )
                    )
    return violations


def _get_changed_python_files(repo_root: Path) -> tuple[list[Path], set[Path]]:
    status_output = _run_git(repo_root, ["status", "--porcelain"])
    changed_rel, new_rel = _parse_git_status_paths(status_output)
    changed_files = sorted((repo_root / rel for rel in changed_rel if (repo_root / rel).exists()), key=lambda item: str(item))
    new_files = {repo_root / rel for rel in new_rel if (repo_root / rel).exists()}
    return changed_files, new_files


def _parse_added_line_numbers_from_diff(diff_text: str) -> set[int]:
    line_numbers: set[int] = set()
    hunk_regex = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
    for raw_line in diff_text.splitlines():
        match = hunk_regex.match(raw_line)
        if not match:
            continue
        start = int(match.group(1))
        length = int(match.group(2)) if match.group(2) is not None else 1
        if length <= 0:
            continue
        line_numbers.update(range(start, start + length))
    return line_numbers


def _get_changed_line_numbers(repo_root: Path, file_path: Path) -> set[int]:
    rel_path = str(file_path.relative_to(repo_root))
    unstaged_diff = _run_git(repo_root, ["diff", "--unified=0", "--", rel_path])
    staged_diff = _run_git(repo_root, ["diff", "--cached", "--unified=0", "--", rel_path])
    return _parse_added_line_numbers_from_diff(unstaged_diff) | _parse_added_line_numbers_from_diff(staged_diff)


def _collect_signature_violations(file_path: Path, lines: list[str]) -> list[Violation]:
    violations: list[Violation] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.lstrip()
        if not (stripped.startswith("def ") or stripped.startswith("class ")):
            index += 1
            continue
        start_line = index + 1
        if stripped.rstrip().endswith(":"):
            index += 1
            continue
        signature_parts = [stripped.strip()]
        cursor = index
        while cursor + 1 < len(lines):
            cursor += 1
            signature_parts.append(lines[cursor].strip())
            if lines[cursor].strip().endswith(":"):
                break
        single_line_signature = " ".join(part for part in signature_parts if part)
        if len(single_line_signature) <= SIGNATURE_MAX_LENGTH:
            violations.append(
                Violation(
                    file_path=file_path,
                    line=start_line,
                    message=(
                        "multi-line function/class signature is <= 200 chars; keep it on one line "
                        f"(length={len(single_line_signature)})."
                    ),
                )
            )
        index = cursor + 1
    return violations


def _collect_method_order_violations(file_path: Path, tree: ast.AST) -> list[Violation]:
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        seen_public_method = False
        for class_item in node.body:
            if not isinstance(class_item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            method_name = class_item.name
            is_dunder = method_name.startswith("__") and method_name.endswith("__")
            is_private = method_name.startswith("_") and not is_dunder
            if is_private and seen_public_method:
                violations.append(
                    Violation(
                        file_path=file_path,
                        line=class_item.lineno,
                        message=(
                            f"class '{node.name}' has private method '{method_name}' after a public method; "
                            "move private methods before public methods."
                        ),
                    )
                )
            if not is_private and not is_dunder:
                seen_public_method = True
    return violations


def _has_main_guard(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not isinstance(test, ast.Compare):
            continue
        if len(test.ops) != 1 or len(test.comparators) != 1:
            continue
        left = test.left
        right = test.comparators[0]
        if not isinstance(test.ops[0], ast.Eq):
            continue
        if isinstance(left, ast.Name) and left.id == "__name__" and isinstance(right, ast.Constant) and right.value == "__main__":
            return True
    return False


def _collect_cli_argument_violations(file_path: Path, tree: ast.AST) -> list[Violation]:
    violations: list[Violation] = []
    if "cli" not in file_path.parts:
        return violations
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "add_argument":
            continue
        if not node.args:
            continue
        first_arg = node.args[0]
        if not isinstance(first_arg, ast.Constant) or not isinstance(first_arg.value, str):
            continue
        flag = first_arg.value
        if not flag.startswith("--"):
            violations.append(
                Violation(file_path=file_path, line=node.lineno, message=f"CLI add_argument must use flag style. Found '{flag}'.")
            )
        if "_" in flag:
            violations.append(Violation(file_path=file_path, line=node.lineno, message=f"CLI flag must be kebab-case. Found '{flag}'."))
        keyword_names = {keyword.arg for keyword in node.keywords if keyword.arg}
        action_value = None
        for keyword in node.keywords:
            if keyword.arg != "action":
                continue
            if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                action_value = keyword.value.value
        required_keywords = {"required", "default", "help"}
        if action_value == "version":
            required_keywords = {"help"}
        for required_keyword in required_keywords:
            if required_keyword not in keyword_names:
                violations.append(
                    Violation(
                        file_path=file_path,
                        line=node.lineno,
                        message=f"CLI add_argument for '{flag}' must define '{required_keyword}'.",
                    )
                )
    return violations


def _check_file(file_path: Path, new_files: set[Path], changed_line_numbers: set[int] | None) -> list[Violation]:
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    violations: list[Violation] = []
    try:
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError as exc:
        return [
            Violation(
                file_path=file_path,
                line=exc.lineno or 1,
                message=f"syntax error while parsing file: {exc.msg}",
            )
        ]
    violations.extend(_collect_signature_violations(file_path=file_path, lines=lines))
    violations.extend(_collect_method_order_violations(file_path=file_path, tree=tree))
    violations.extend(_collect_cli_argument_violations(file_path=file_path, tree=tree))
    if file_path in new_files and not _has_main_guard(tree):
        violations.append(
            Violation(
                file_path=file_path,
                line=1,
                message="new Python module must include if __name__ == \"__main__\": block.",
            )
        )
    if changed_line_numbers is not None and file_path not in new_files:
        violations = [violation for violation in violations if violation.line in changed_line_numbers]
    return violations


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate HAPE coding rules on Python files.")
    parser.add_argument("--all", action="store_true", help="scan all Python files in the repository.")
    parser.add_argument("--paths", nargs="*", default=None, help="specific Python file paths to scan.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    new_files: set[Path] = set()
    changed_line_numbers_by_file: dict[Path, set[int]] | None = None
    if args.paths:
        target_files = [repo_root / item for item in args.paths if item.endswith(".py")]
    elif args.all:
        target_files = _get_repo_python_files(repo_root)
    else:
        target_files, new_files = _get_changed_python_files(repo_root)
        changed_line_numbers_by_file = {file_path: _get_changed_line_numbers(repo_root=repo_root, file_path=file_path) for file_path in target_files}
    target_files = [path for path in target_files if path.exists() and path.suffix == ".py"]
    violations: list[Violation] = []
    for file_path in target_files:
        changed_line_numbers = None if changed_line_numbers_by_file is None else changed_line_numbers_by_file.get(file_path, set())
        violations.extend(_check_file(file_path=file_path, new_files=new_files, changed_line_numbers=changed_line_numbers))
    privacy_files = _get_repo_text_files(repo_root)
    for file_path in privacy_files:
        violations.extend(_collect_local_path_violations(file_path))
    if violations:
        print("HAPE rule check failed:")
        for violation in violations:
            relative_path = violation.file_path.relative_to(repo_root)
            print(f"- {relative_path}:{violation.line}: {violation.message}")
        return 1
    print(f"HAPE rule check passed for {len(target_files)} Python file(s) and {len(privacy_files)} scanned text file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
