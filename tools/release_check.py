"""Native semantic version planner, RELEASE_NOTES generator, and CHANGELOG verifier."""

import re
import subprocess
from pathlib import Path


def read_text_or_empty(path: Path, default: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return default


def latest_v_tag(root: Path) -> str | None:
    res = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0", "--match", "v[0-9]*"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        return None
    tag = res.stdout.strip()
    return tag or None


def commits_since(root: Path, tag: str | None) -> list[str]:
    rev_range = f"{tag}..HEAD" if tag else "HEAD"
    res = subprocess.run(["git", "log", rev_range, "--format=%s"], cwd=root, capture_output=True, text=True)
    if res.returncode != 0:
        return []
    return [line for line in res.stdout.splitlines() if line]


def next_version(base: str, commits: list[str]) -> str:
    maj, min_v, pat = [int(x) for x in base.split(".")]
    if any(c.startswith("upgrade(") or "!:" in c for c in commits):
        return f"{maj + 1}.0.0"
    if any(c.startswith("feat(") for c in commits):
        return f"{maj}.{min_v + 1}.0"
    if any(c.startswith(("fix(", "perf(", "revert(")) for c in commits):
        return f"{maj}.{min_v}.{pat + 1}"
    return base


def run_release(root: Path, check_only: bool, apply: bool, notes_out: Path | None) -> bool:
    pyproject_path = root / "pyproject.toml"
    pyproject = pyproject_path.read_text(encoding="utf-8")
    m = re.search(r'^version = "([^"]+)"', pyproject, re.MULTILINE)
    if not m:
        print("FAIL release: version missing in pyproject.toml")
        return False
    current_ver = m.group(1)

    tag = latest_v_tag(root)
    commits = commits_since(root, tag)
    if notes_out is not None:
        parts = [f"# Release v{current_ver}\n"]
        for kind in ("feat", "fix", "perf", "refactor", "docs", "ci", "chore", "upgrade"):
            items = [c for c in commits if c.startswith(f"{kind}(")]
            if items:
                parts.append(f"## {kind}\n")
                parts.extend(f"- {item}" for item in items)
                parts.append("")
        notes_out.write_text("\n".join(parts) + "\n", encoding="utf-8")
        print(f"PASS release: wrote notes to {notes_out}")
        return True

    expected = next_version(tag.lstrip("v"), commits) if tag else current_ver
    changelog_path = root / "CHANGELOG.md"
    changelog = read_text_or_empty(changelog_path, "# Changelog\n\n")

    if apply and expected != current_ver:
        pyproject_path.write_text(
            pyproject.replace(f'version = "{current_ver}"', f'version = "{expected}"', 1),
            encoding="utf-8",
        )
        if f"## {expected}" not in changelog:
            bullets = "\n".join(f"- {c}" for c in commits if not c.startswith("Merge "))
            entry = f"## {expected}\n\n{bullets or '- Automated release preparation.'}\n\n"
            body = re.sub(r"^# Changelog\s*\n+", "", changelog)
            changelog_path.write_text(f"# Changelog\n\n{entry}{body}", encoding="utf-8")
        print(f"PASS release: prepared {expected}")
        return True

    if check_only:
        if current_ver != expected:
            print(f"FAIL release: pyproject.toml {current_ver} != expected {expected}")
            return False
        if f"## {current_ver}" not in changelog:
            print(f"FAIL release: CHANGELOG.md missing '## {current_ver}'")
            return False
        print(f"PASS release ({current_ver})")
        return True

    print(f"PASS release: current={current_ver} expected={expected}")
    return True
