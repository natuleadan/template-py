"""Repository hygiene checks: line limits, anti-leak, markdown hyphens, shell syntax."""

import subprocess
from pathlib import Path

MAX_LINES = 500
SKIP_DIRS = {".venv", ".git", "__pycache__", "dist", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
CHECK_EXTS = {".py", ".md", ".sh", ".toml", ".yml", ".yaml"}
FORBIDDEN_FILES = [
    "package.json",
    "requirements.txt",
    ".prettierrc",
    "ruff.toml",
    ".ruff.toml",
    ".black.toml",
]


def run_hygiene(root: Path) -> bool:
    errors: list[str] = [
        f"forbidden artifact '{forbidden}' present"
        for forbidden in FORBIDDEN_FILES
        if (root / forbidden).exists()
    ]
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts) or not path.is_file():
            continue
        if path.suffix not in CHECK_EXTS:
            continue
        rel = path.relative_to(root).as_posix()
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        lines = content.splitlines()
        if len(lines) > MAX_LINES:
            errors.append(f"{rel} has {len(lines)} lines (max {MAX_LINES})")
        if rel != "tools/hygiene_check.py" and "/Users/" in content:
            errors.append(f"{rel} contains hardcoded '/Users/' path")
        if path.suffix == ".md":
            in_code = False
            for idx, line in enumerate(lines, start=1):
                if line.lstrip().startswith("```"):
                    in_code = not in_code
                    continue
                if in_code or line.startswith("- ") or line.startswith("|"):
                    continue
                if " - " in line.replace("2023 - Present", "2023PRESENT"):
                    errors.append(f"{rel}:{idx} contains spaced hyphen ' - ' in prose")
        if path.suffix == ".sh":
            res = subprocess.run(["sh", "-n", str(path)], capture_output=True, text=True)
            if res.returncode != 0:
                errors.append(f"{rel} failed 'sh -n' syntax check")

    if errors:
        print("FAIL hygiene")
        for err in errors:
            print(f"  {err}")
        return False
    print("PASS hygiene")
    return True
