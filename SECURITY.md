# Security Policy

## Supply-Chain & Hygiene Controls

This template enforces automated defense-in-depth across local hooks and GitHub Actions:

1. **Three-Day Dependency Cooldown**: `exclude-newer = "3 days"` in `pyproject.toml` and `.github/dependabot.yml` (`cooldown: default-days: 3`) prevent immediate adoption of newly published or compromised Python packages.
2. **Static Analysis (CodeQL)**: `.github/workflows/security.yml` runs GitHub CodeQL analysis for Python on every push, pull request, and weekly schedule.
3. **Dependency Audit & SBOM**: `uv export` inventories are exported as CI build artifacts on every security run.
4. **Anti-Leak Hygiene Gate**: `tools/hygiene_check.py` blocks hardcoded user paths, restricted tokens, and oversized files before code can be pushed.

## Reporting a Vulnerability

Please report suspected security issues privately using GitHub Security Advisories for this repository rather than opening public issues.
