"""Native Python AST linter, ruff runner, and mypy typecheck verifier."""

import ast
import io
import re
import subprocess
import sys
import tokenize
import tomllib
from pathlib import Path

FORBIDDEN_CALLS = {"eval", "exec", "compile", "breakpoint", "__import__", "input"}
FORBIDDEN_ATTR_CALLS = {
    ("os", "system"),
    ("os", "popen"),
    ("pickle", "load"),
    ("pickle", "loads"),
    ("marshal", "loads"),
}
REQUIRED_POLICY_FLAGS = (
    "strict_annotations",
    "forbid_mutable_defaults",
    "forbid_bare_except",
    "forbid_assert_in_src",
    "forbid_print_in_src",
    "forbid_bool_params_in_src",
    "require_public_docstrings",
    "forbid_dynamic_exec",
)
FORBIDDEN_TOOL_SECTIONS = ("black", "isort", "yapf", "autopep8")
REQUIRED_TOOL_SECTIONS = ("ruff", "mypy", "policy")
SKIP_DIRS = {".venv", ".git", "__pycache__", "dist", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


def iter_py_files(root: Path) -> list[Path]:
    """Return every Python file under root excluding cache and venv folders."""
    return sorted(
        path for path in root.rglob("*.py") if not any(part in SKIP_DIRS for part in path.parts)
    )


def _is_bool_annotation(ann: ast.expr | None) -> bool:
    return isinstance(ann, ast.Name) and ann.id == "bool"


def _contains_any_type(ann: ast.expr | None) -> bool:
    if ann is None:
        return False
    return any(
        (isinstance(sub, ast.Name) and sub.id == "Any")
        or (isinstance(sub, ast.Attribute) and sub.attr == "Any")
        for sub in ast.walk(ann)
    )


def _is_none_or_bool_constant(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and (node.value is None or isinstance(node.value, bool))


def _check_comments(rel: str, source: str, errors: list[str]) -> None:
    for tok_type, tok_str, start, _, _ in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok_type != tokenize.COMMENT:
            continue
        lineno = start[0]
        if "# noqa" in tok_str and not re.search(r"#\s*noqa:\s*[A-Za-z0-9_, ]+", tok_str):
            errors.append(f"{rel}:{lineno}: bare '# noqa' without explicit rule code")
        if "# type: ignore" in tok_str and not re.search(r"#\s*type:\s*ignore\[[^\]]+\]", tok_str):
            errors.append(f"{rel}:{lineno}: bare '# type: ignore' without [error-code]")
        if re.search(r"\b(?:TODO|FIXME)\b", tok_str):
            errors.append(f"{rel}:{lineno}: unresolved TODO or FIXME comment")


def _check_node_policy(rel: str, node: ast.AST) -> list[str]:
    found: list[str] = []
    line = getattr(node, "lineno", 0)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
        found.append(f"{rel}:{line}: forbidden print() in domain source")
    if isinstance(node, ast.ExceptHandler):
        if node.type is None:
            found.append(f"{rel}:{line}: forbidden bare 'except:' clause")
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            found.append(f"{rel}:{line}: silent exception swallowing with 'pass'")
    if isinstance(node, ast.Assert):
        found.append(f"{rel}:{line}: forbidden 'assert' in runtime source")
    if isinstance(node, ast.Global):
        found.append(f"{rel}:{line}: forbidden 'global' statement")
    if isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names):
        found.append(f"{rel}:{line}: forbidden wildcard import '*'")
    if isinstance(node, ast.Compare):
        found.extend(
            f"{rel}:{line}: use 'is'/'is not' when comparing to None/bool"
            for op, right in zip(node.ops, node.comparators, strict=True)
            if isinstance(op, ast.Eq | ast.NotEq)
            and (_is_none_or_bool_constant(node.left) or _is_none_or_bool_constant(right))
        )
    is_public_class = isinstance(node, ast.ClassDef) and not node.name.startswith("_")
    if isinstance(node, ast.ClassDef) and is_public_class and ast.get_docstring(node) is None:
        found.append(f"{rel}:{line}: public class '{node.name}' missing docstring")
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        found.extend(_check_function_policy(rel, node))
    return found


def _check_function_policy(rel: str, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    found: list[str] = []
    public = not node.name.startswith("_")
    if public and ast.get_docstring(node) is None:
        found.append(f"{rel}:{node.lineno}: public function '{node.name}' missing docstring")
    defaults = [*node.args.defaults, *(d for d in node.args.kw_defaults if d is not None)]
    found.extend(
        f"{rel}:{node.lineno}: mutable default argument in '{node.name}'"
        for default in defaults
        if isinstance(default, ast.List | ast.Dict | ast.Set | ast.Call)
    )
    if public:
        params = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        found.extend(
            f"{rel}:{node.lineno}: bool param '{arg.arg}' forbidden in public '{node.name}'"
            for arg in params
            if _is_bool_annotation(arg.annotation)
        )
    return found


def _check_src_ast(rel: str, tree: ast.Module, errors: list[str]) -> None:
    if ast.get_docstring(tree) is None:
        errors.append(f"{rel}:1: module missing docstring")
    for node in ast.walk(tree):
        errors.extend(_check_node_policy(rel, node))


def _check_call_policy(rel: str, node: ast.Call) -> list[str]:
    found: list[str] = []
    if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
        found.append(f"{rel}:{node.lineno}: forbidden call '{node.func.id}()'")
    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
        pair = (node.func.value.id, node.func.attr)
        if pair in FORBIDDEN_ATTR_CALLS:
            found.append(f"{rel}:{node.lineno}: forbidden call '{pair[0]}.{pair[1]}()'")
        if pair[0] == "subprocess":
            found.extend(
                f"{rel}:{node.lineno}: forbidden subprocess shell=True"
                for kw in node.keywords
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True
            )
        if pair == ("yaml", "load") and not any(kw.arg == "Loader" for kw in node.keywords):
            found.append(f"{rel}:{node.lineno}: yaml.load() requires SafeLoader")
    return found


def _check_pyproject(root: Path, errors: list[str]) -> None:
    raw = (root / "pyproject.toml").read_text(encoding="utf-8")
    if "@latest" in raw or "==*" in raw:
        errors.append("pyproject.toml contains unpinned wildcard or @latest")
    tool = tomllib.loads(raw).get("tool", {})
    errors.extend(
        f"pyproject.toml [tool.policy].{flag} must be true"
        for flag in REQUIRED_POLICY_FLAGS
        if tool.get("policy", {}).get(flag) is not True
    )
    errors.extend(
        f"pyproject.toml must define [tool.{section}]"
        for section in REQUIRED_TOOL_SECTIONS
        if section not in tool
    )
    errors.extend(
        f"pyproject.toml must not configure formatter [tool.{section}]"
        for section in FORBIDDEN_TOOL_SECTIONS
        if section in tool
    )
    if "format" in tool.get("ruff", {}):
        errors.append("pyproject.toml must not configure [tool.ruff.format]")


def _run_tool(args: list[str], root: Path, label: str) -> list[str]:
    res = subprocess.run(
        [sys.executable, "-m", *args], cwd=root, capture_output=True, text=True, check=False
    )
    if res.returncode == 0:
        return []
    output = (res.stdout + "\n" + res.stderr).strip()
    return output.splitlines() if output else [f"{label} failed"]


def run_lint(root: Path) -> bool:
    """Run the policy AST checks and `ruff check --no-fix`; print PASS or FAIL."""
    errors: list[str] = []
    _check_pyproject(root, errors)

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
            if isinstance(node, ast.Call):
                errors.extend(_check_call_policy(rel, node))
        if rel.startswith("src/"):
            _check_src_ast(rel, tree, errors)
            _check_comments(rel, source, errors)

    errors.extend(_run_tool(["ruff", "check", "--no-fix", "src", "tests", "tools"], root, "ruff check"))

    if errors:
        print("FAIL lint")
        for err in errors:
            print(f"  {err}")
        return False
    print("PASS lint")
    return True


def _check_signature(rel: str, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    found: list[str] = []
    if node.returns is None:
        found.append(f"{rel}:{node.lineno}: function '{node.name}' missing return annotation")
    elif _contains_any_type(node.returns):
        found.append(f"{rel}:{node.lineno}: return type of '{node.name}' forbids Any")
    args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
    args.extend(a for a in (node.args.vararg, node.args.kwarg) if a is not None)
    for arg in args:
        if arg.arg in ("self", "cls"):
            continue
        if arg.annotation is None:
            found.append(f"{rel}:{node.lineno}: arg '{arg.arg}' in '{node.name}' missing type annotation")
        elif _contains_any_type(arg.annotation):
            found.append(f"{rel}:{node.lineno}: arg '{arg.arg}' in '{node.name}' forbids Any")
    return found


def run_typecheck(root: Path) -> bool:
    """Verify annotations natively and run `mypy --strict` on `src`."""
    errors: list[str] = []
    for path in iter_py_files(root):
        rel = path.relative_to(root).as_posix()
        if not rel.startswith("src/"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                errors.extend(_check_signature(rel, node))

    mypy_args = ["mypy", "--strict", "--config-file", "pyproject.toml", "src"]
    errors.extend(_run_tool(mypy_args, root, "mypy --strict src"))

    if errors:
        print("FAIL typecheck")
        for err in errors:
            print(f"  {err}")
        return False
    print("PASS typecheck")
    return True
