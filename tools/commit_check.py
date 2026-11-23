"""Commit message and git authorship policy validator."""

import re
import subprocess
import sys
from pathlib import Path

TYPES = {
    "feat", "fix", "upgrade", "docs", "style", "refactor", "perf", "test", "chore", "ci", "revert",
}
SCOPES = {
    "core", "api", "cli", "domain", "math", "tools", "ui", "config", "docs", "ci", "workflow", "hooks", "release", "license", "deps", "security",
}
# CHANGE ME: optionally pin your organization noreply email domain or handle.
NOREPLY_SUFFIX = "@users.noreply.github.com"


def validate_message(raw: str) -> str | None:
    lines = raw.replace("\r\n", "\n").rstrip("\n").split("\n")
    header = lines[0] if lines else ""
    if not header:
        return "empty commit message"
    if header.startswith("Merge ") or header.startswith("Revert ") or "dependabot[bot]" in raw:
        return None
    if len(header) > 100:
        return f"header exceeds 100 chars ({len(header)})"
    if header.endswith("."):
        return "header must not end with a period"

    match = re.match(r"^([a-z]+)\(([a-z0-9-]+)\): (.+)$", header)
    if not match:
        return f"header must match type(scope): description -> {header}"
    ctype, scope, desc = match.groups()
    if ctype not in TYPES:
        return f"invalid commit type '{ctype}'"
    if scope not in SCOPES:
        return f"invalid commit scope '{scope}'"
    words = len(desc.split())
    if words < 3 or words > 6:
        return f"description has {words} words (expected 3..6)"

    lower = raw.lower()
    for forbidden in ("co-authored-by:", "signed-off-by:", "generated-by:", "assisted-by:"):
        if forbidden in lower:
            return f"forbidden trailer '{forbidden}' present"

    if len(lines) < 2 or lines[1] != "":
        return "expected a single blank line after header"
    body_lines = [line for line in lines[2:] if not line.startswith("#")]
    if any(line == "" for line in body_lines):
        return "body bullets must not contain blank lines"
    if len(body_lines) < 3:
        return f"body has {len(body_lines)} bullets (minimum 3)"

    for line in body_lines:
        bmatch = re.match(r"^- \*\*[^*]+\*\*: (\S.*)$", line)
        if not bmatch:
            return f"bullet must match '- **Label**: text' -> {line}"
        bwords = len(bmatch.group(1).split())
        if bwords < 3 or bwords > 10:
            return f"bullet has {bwords} words (expected 3..10): {line}"
    return None


def git_cfg(root: Path, key: str) -> str:
    return subprocess.check_output(["git", "config", key], cwd=root, text=True).strip()


def run_commit_check(root: Path, args: list[str]) -> int:
    if "--range" in args:
        idx = args.index("--range")
        rev_range = args[idx + 1]
        shas = subprocess.check_output(["git", "rev-list", rev_range], cwd=root, text=True).splitlines()
        for sha in shas:
            if not sha:
                continue
            msg = subprocess.check_output(["git", "log", "-1", "--format=%B", sha], cwd=root, text=True)
            err = validate_message(msg)
            if err:
                print(f"FAIL commit-check ({sha}): {err}", file=sys.stderr)
                return 1
        print("PASS commit-check")
        return 0

    msg_file = Path(args[0])
    name = git_cfg(root, "user.name")
    email = git_cfg(root, "user.email")
    if not name:
        print("FAIL commit-check: git user.name must be configured", file=sys.stderr)
        return 1
    if not email.endswith(NOREPLY_SUFFIX):
        print(f"FAIL commit-check: git user.email must end with '{NOREPLY_SUFFIX}', got '{email}'", file=sys.stderr)
        return 1

    err = validate_message(msg_file.read_text(encoding="utf-8"))
    if err:
        print(f"FAIL commit-check: {err}", file=sys.stderr)
        return 1
    print("PASS commit-check")
    return 0
