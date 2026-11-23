"""Architecture and policy tripwire tests."""

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
FORMATTER_PACKAGES = {"black", "yapf", "autopep8", "isort"}


def _read(*parts: str) -> str:
    return ROOT.joinpath(*parts).read_text(encoding="utf-8")


def _package_name(requirement: str) -> str:
    return re.split(r"[<>=!~ \[;]", requirement, maxsplit=1)[0].lower()


def test_uv_three_day_cooldown_configured() -> None:
    assert PYPROJECT["tool"]["uv"]["exclude-newer"] == "3 days"


def test_no_forbidden_formatter_or_js_artifacts() -> None:
    forbidden_files = [
        "package.json",
        "requirements.txt",
        ".prettierrc",
        "ruff.toml",
        ".ruff.toml",
        ".black.toml",
    ]
    for forbidden in forbidden_files:
        assert not (ROOT / forbidden).exists(), f"forbidden artifact {forbidden}"

    tool = PYPROJECT["tool"]
    for section in ("black", "isort", "yapf", "autopep8"):
        assert section not in tool, f"forbidden formatter section [tool.{section}]"
    assert "format" not in tool["ruff"], "[tool.ruff.format] is forbidden"

    declared = [
        *PYPROJECT["project"]["dependencies"],
        *PYPROJECT["dependency-groups"]["dev"],
    ]
    names = {_package_name(requirement) for requirement in declared}
    assert not names & FORMATTER_PACKAGES, "formatter packages are forbidden"
    assert {"ruff", "mypy"} <= names, "ruff and mypy must stay declared as dev analyzers"


def test_locks_immutable_pyproject_policy() -> None:
    assert PYPROJECT["project"]["requires-python"] == ">=3.12"
    policy = PYPROJECT["tool"]["policy"]
    required_flags = [
        "strict_annotations",
        "forbid_mutable_defaults",
        "forbid_bare_except",
        "forbid_assert_in_src",
        "forbid_print_in_src",
        "forbid_bool_params_in_src",
        "require_public_docstrings",
        "forbid_dynamic_exec",
    ]
    for flag in required_flags:
        assert policy.get(flag) is True, f"[tool.policy].{flag} must remain true"


def test_locks_immutable_ruff_lint_policy() -> None:
    ruff = PYPROJECT["tool"]["ruff"]
    assert ruff["target-version"] == "py312"
    lint = ruff["lint"]
    select = set(lint["select"])
    required = {
        "E4", "E7", "E9", "F", "B", "BLE", "S", "ANN", "D", "T20", "UP", "SIM",
        "PERF", "FBT", "TRY", "RUF", "PGH", "DTZ", "ASYNC", "A", "C4", "ARG",
        "RET", "SLF", "PT", "N", "PL",
    }  # fmt: skip
    assert required <= select, f"missing ruff rule sets: {sorted(required - select)}"
    formatting_only = {"E501", "W", "Q", "COM", "COM812", "I", "ISC"}
    assert not select & formatting_only, "formatting-only ruff rules are forbidden"
    protected = {
        "F401", "F403", "F405", "B006", "B023", "BLE001", "S101", "S307", "S602",
        "ANN401", "D100", "D101", "D102", "D103", "T201", "FBT001", "PGH003", "PGH004",
    }  # fmt: skip
    assert not set(lint["ignore"]) & protected, "safety rules must never be ignored"
    assert lint["pydocstyle"]["convention"] == "google"


def test_locks_immutable_mypy_policy() -> None:
    mypy = PYPROJECT["tool"]["mypy"]
    assert mypy["python_version"] == "3.12"
    assert mypy["mypy_path"] == "src"
    for key in (
        "explicit_package_bases",
        "strict",
        "disallow_any_explicit",
        "warn_unreachable",
        "warn_unused_ignores",
        "strict_equality",
        "extra_checks",
    ):
        assert mypy[key] is True, f"[tool.mypy].{key} must remain true"
    required_codes = {
        "ignore-without-code",
        "redundant-expr",
        "truthy-bool",
        "truthy-iterable",
        "possibly-undefined",
        "unused-awaitable",
    }
    assert required_codes <= set(mypy["enable_error_code"])


def test_locks_immutable_ast_lint_rules() -> None:
    lint_src = _read("tools", "lint_check.py")
    required_tokens = [
        "FORBIDDEN_CALLS",
        "FORBIDDEN_ATTR_CALLS",
        "ast.ExceptHandler",
        "ast.Assert",
        "mutable default argument",
        "forbidden print()",
        "_is_bool_annotation",
        "ast.get_docstring",
        "_contains_any_type",
        "shell",
        "# noqa",
        "# type: ignore",
        '"ruff"',
        '"check"',
        '"--no-fix"',
        '"mypy"',
        '"--strict"',
    ]
    for token in required_tokens:
        assert token in lint_src, f"tools/lint_check.py missing immutable policy rule: {token}"

    guarded = [
        ("tools", "lint_check.py"),
        ("tools", "xtask.py"),
        (".githooks", "pre-commit"),
        (".githooks", "pre-push"),
        (".github", "workflows", "validate.yml"),
    ]
    for parts in guarded:
        text = _read(*parts)
        assert "ruff format" not in text, f"{'/'.join(parts)} must never run ruff format"
        assert '"ruff", "format"' not in text, f"{'/'.join(parts)} must never run ruff format"


def test_enforces_modular_layer_boundaries() -> None:
    math_dir = ("src", "app", "modules", "math")
    entity = _read(*math_dir, "entity.py")
    dto = _read(*math_dir, "dto.py")
    repo = _read(*math_dir, "repository.py")
    service = _read(*math_dir, "service.py")
    controller = _read(*math_dir, "controller.py")

    for forbidden in ("service", "controller", "repository"):
        assert forbidden not in entity, f"entity.py leaked {forbidden}"
        assert forbidden not in dto, f"dto.py leaked {forbidden}"
    assert "service" not in repo, "repository.py leaked service"
    assert "controller" not in repo, "repository.py leaked controller"
    assert "controller" not in service, "service.py leaked controller"
    assert "repository" not in controller, "controller.py leaked repository"
