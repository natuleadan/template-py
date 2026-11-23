# AGENTS.md

Technical operating rules for this Python (`uv` + FastAPI) repository template.

## 1. Repository Scope

- Public Python (`uv` + FastAPI) workspace template with native `tools.xtask` validation.
- Update template placeholders (`CHANGE_ME`) in `pyproject.toml`, `LICENSE`, `NOTICE`, `README.md`, and `.github/CODEOWNERS` before production use.

## 2. Toolchain & Validation

- Package & environment manager: `uv` with `pyproject.toml` and `uv.lock` (`requirements.txt` and Node.js tooling are forbidden).
- Compiler & static safety: preserve `[tool.policy]` flags in `pyproject.toml` and AST rules in `tools/lint_check.py` (strict parameter/return annotations, no `Any`, no bare `except:`, no mutable defaults, no `assert`/`print` in `src/`, no `eval`/`exec`/`shell=True`, no boolean flag parameters in public APIs).
- Enable hooks locally with `git config core.hooksPath .githooks` and run `uv run python -m tools.xtask validate` (`TOTAL PASS=8 FAIL=0`) before opening or updating any pull request.
- Do not run `black`, `ruff format`, or `prettier` in hooks, CI, or pre-commit steps.

## 3. Code Layout & Architecture

- Organize domain logic under `src/app/modules/<domain>/` as a six-file layered modular layout (`entity.py`, `dto.py`, `repository.py`, `service.py`, `controller.py`, `module.py`).
- Enforce unidirectional imports: `controller` calls `service` and `dto` (never `repository`); `entity` and `dto` must not import `service`, `repository`, or `controller`.
- Document all modules and public classes/functions in `src/` with docstrings and keep every source and documentation file at or below **500 lines**.

## 4. Commit, Dependency & License Policy

- Set Git Author and Committer identically to your maintainer handle and GitHub noreply email (`<id>+<handle>@users.noreply.github.com`).
- Format commits as `type(scope): description` (3 to 6 lowercase words, no trailing period, max 100 chars), a single blank line, and 3+ consecutive `- **Label**: text` bullets (3 to 10 words each) without trailers.
- External dependencies must pass the 3-day publish cooldown (`exclude-newer = "3 days"` in `pyproject.toml`); run `uv lock` and `uv run python -m tools.xtask notices` after dependency edits.
- Code and documentation are released under the Apache License 2.0 (`Copyright (c) 2026 CHANGE_ME`).
