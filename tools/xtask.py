"""Unified Python repository automation and validation runner."""

import subprocess
import sys
from pathlib import Path

from tools.commit_check import run_commit_check
from tools.hygiene_check import run_hygiene
from tools.lint_check import run_lint, run_typecheck
from tools.notices_check import run_notices
from tools.release_check import run_release

ROOT = Path(__file__).resolve().parent.parent


def run_pytest(name: str, args: list[str]) -> bool:
    res = subprocess.run([sys.executable, "-m", "pytest", *args], cwd=ROOT, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"PASS {name}")
        return True
    print(f"FAIL {name}")
    out = (res.stdout + "\n" + res.stderr).strip()
    if out:
        print(out)
    return False


def check_cooldown() -> bool:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    if 'exclude-newer = "3 days"' in pyproject:
        print("PASS cooldown")
        return True
    print("FAIL cooldown: pyproject.toml missing exclude-newer = \"3 days\"")
    return False


def cmd_validate() -> int:
    checks = [
        run_lint(ROOT),
        run_typecheck(ROOT),
        run_pytest("unit tests", ["tests/test_unit.py", "-q"]),
        run_pytest(
            "integration and architecture tests",
            ["tests/test_integration.py", "tests/test_architecture.py", "-q"],
        ),
        check_cooldown(),
        run_hygiene(ROOT),
        run_notices(ROOT, check_only=True),
        run_release(ROOT, check_only=True, apply=False, notes_out=None),
    ]
    passed = sum(1 for ok in checks if ok)
    failed = len(checks) - passed
    print(f"TOTAL PASS={passed} FAIL={failed}")
    return 0 if failed == 0 else 1


def main() -> int:
    args = sys.argv[1:]
    cmd = args[0] if args else ""
    if cmd == "validate":
        return cmd_validate()
    if cmd == "commit-check":
        return run_commit_check(ROOT, args[1:])
    if cmd == "notices":
        return 0 if run_notices(ROOT, check_only="--check" in args) else 1
    if cmd == "release":
        notes_out = Path(args[args.index("--notes") + 1]) if "--notes" in args else None
        return 0 if run_release(ROOT, "--check" in args, "--apply" in args, notes_out) else 1
    print("Usage: python -m tools.xtask <validate|commit-check|notices [--check]|release [--check|--apply|--notes <path>]>")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
