"""Native Python AST linter and typecheck verifier."""

import ast
from pathlib import Path

FORBIDDEN_CALLS = {"eval", "exec", "breakpoint"}
SKIP_DIRS = {".venv", ".git", "__pycache__", "dist", ".pytest_cache"}


def iter_py_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def run_lint(root: Path) -> bool:
    errors: list[str] = []
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    if "@latest" in pyproject or "==*" in pyproject:
        errors.append("pyproject.toml contains unpinned wildcard or @latest")

    for path in iter_py_files(root):
        rel = path.relative_to(root).as_posix()
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=rel)
        except SyntaxError as exc:
            errors.append(f"{rel}:{exc.lineno}: syntax error: {exc.msg}")
            continue

        if rel.startswith("tools/"):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in FORBIDDEN_CALLS:
                    errors.append(f"{rel}:{node.lineno}: forbidden call '{node.func.id}()'")

    if errors:
        print("FAIL lint")
        for err in errors:
            print(f"  {err}")
        return False
    print("PASS lint")
    return True


def run_typecheck(root: Path) -> bool:
    errors: list[str] = []
    for path in iter_py_files(root):
        rel = path.relative_to(root).as_posix()
        if not rel.startswith("src/"):
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=rel)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.returns is None:
                    errors.append(f"{rel}:{node.lineno}: function '{node.name}' missing return annotation")
                for arg in node.args.args:
                    if arg.arg != "self" and arg.annotation is None:
                        errors.append(f"{rel}:{node.lineno}: arg '{arg.arg}' in '{node.name}' missing type annotation")

    if errors:
        print("FAIL typecheck")
        for err in errors:
            print(f"  {err}")
        return False
    print("PASS typecheck")
    return True
