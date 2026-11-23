# Project Template (CHANGE ME)

Production-ready Python (`uv` + FastAPI) repository template featuring a native Python `tools.xtask` validation suite, layered modular domain architecture, strict Git hygiene, 3-day dependency cooldown enforcement, and automated GitHub Actions pipelines.

## Key Features

- **100% Native Python + `uv` Tooling**: Managed via `uv` (`pyproject.toml` + `uv.lock`) with native AST/compilation checks (`tools/*.py`) and zero Node.js or external formatter dependencies.
- **Strict AST & Annotation Policy Lock**: Enforces complete sync/async type annotations, forbids `Any`, bare `except:`, mutable default args, `assert`/`print` in `src/`, dynamic `eval`/`exec`/`shell=True`, and public `bool` parameter flags; `tests/test_architecture.py` locks all `[tool.policy]` settings.
- **Layered Modular Architecture**: Reference domain module (`src/app/modules/math/`) separating `entity`, `dto`, `repository`, `service`, `controller`, and `module` layers with automated boundary tests.
- **Eight Standardized Validation Gates**: `lint`, `typecheck`, `unit tests`, `integration and architecture tests`, `cooldown`, `hygiene`, `notices`, and `release`.
- **Supply-Chain Hardening**: 3-day dependency publish-age cooldown (`exclude-newer = "3 days"`), CodeQL static analysis, and automated SBOM/dependency inventory artifacts.
- **Zero Formatter Drift**: Automated formatters (`black`, `ruff format`, `prettier`) are intentionally excluded from hooks and CI so diffs stay focused on logic.

## Repository Layout

```text
.
├── .githooks/                   # Versioned commit-msg, pre-commit, and pre-push hooks
├── .github/
│   ├── CODEOWNERS               # Code ownership rules (CHANGE ME)
│   ├── dependabot.yml           # uv and GitHub Actions updates with 3-day cooldown
│   └── workflows/               # validate.yml, nightly-tag.yml, security.yml
├── src/app/
│   ├── main.py                  # FastAPI entrypoint (/health, /greet/{name}, /math/add)
│   └── modules/math/            # Layered domain module (entity, dto, repository, service, controller, module)
├── tests/                       # Unit, FastAPI integration, and architecture boundary tests
├── tools/                       # Native validation CLI (uv run python -m tools.xtask <cmd>)
├── ARCHITECTURE.md              # Modular architecture and dependency boundary guide
├── AGENTS.md                    # Autonomous agent operating rules
├── CONTRIBUTING.md              # Contributor workflow and commit grammar
├── SECURITY.md                  # Supply-chain controls and vulnerability reporting
├── LICENSE                      # Apache-2.0 License (Copyright (c) 2026 CHANGE_ME)
└── ThirdPartyNotices.txt        # Generated dependency notice inventory
```

## Quickstart

Enable repository hooks, sync dependencies, and run the full 8-gate validation suite:

```sh
git config core.hooksPath .githooks
uv sync --locked
uv run python -m tools.xtask validate
```

Other `xtask` commands:

```sh
uv run python -m tools.xtask notices          # Regenerate ThirdPartyNotices.txt from uv.lock
uv run python -m tools.xtask release --check  # Verify pyproject.toml version matches CHANGELOG.md
```

## Validation Gates

| Gate | Implementation | Purpose |
| :--- | :--- | :--- |
| `lint` | `tools/lint_check.py` | Strict AST security/idiom rules, docstrings, policy lock |
| `typecheck` | `tools/lint_check.py` | Sync/async annotation checks and `Any` prohibition |
| `unit tests` | `uv run pytest tests/test_unit.py` | Fast unit test execution |
| `integration and architecture tests` | `uv run pytest tests/test_integration.py tests/test_architecture.py` | FastAPI endpoints and layer boundaries |
| `cooldown` | `pyproject.toml` (`exclude-newer = "3 days"`) | 3-day package release cooldown |
| `hygiene` | `tools/hygiene_check.py` | 500-line limit, anti-leak, markdown hygiene |
| `notices` | `tools/notices_check.py` | License inventory parity |
| `release` | `tools/release_check.py` | SemVer and `CHANGELOG.md` consistency |

## Branching & Release Workflow

- **`dev`**: Active integration branch protected against deletion. Every push updates the rolling `dev` tag, `dev-<short_sha>` tag, and `dev` pre-release snapshot.
- **`main`**: Protected release branch. Accepts rebase-only pull requests from `dev` after all status checks pass. Merging triggers automatic `vX.Y.Z` tagging, GitHub Release creation, and `dev` fast-forward sync.

## Template Customization (CHANGE ME)

When bootstrapping a new repository from this template, update the following placeholders:

- **`README.md`**: Replace `# Project Template (CHANGE ME)` with your project title and description.
- **`LICENSE` and `NOTICE`**: Replace `Copyright (c) 2026 CHANGE_ME` with your copyright holder.
- **`.github/CODEOWNERS`**: Uncomment and set your GitHub handle or team (`* @your-handle`, CHANGE ME).
- **Package Manifest**: Update `name` and `description` in `pyproject.toml` (`CHANGE ME`).
- **Git Identity**: Configure `git config user.name` and a GitHub noreply address (`<id>+<handle>@users.noreply.github.com`) locally before committing.

## License

Licensed under the [Apache-2.0 License](LICENSE). Copyright (c) 2026 CHANGE_ME.
