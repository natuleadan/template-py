"""Architecture and policy tripwire tests."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_uv_three_day_cooldown_configured() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'exclude-newer = "3 days"' in pyproject


def test_no_forbidden_formatter_or_js_artifacts() -> None:
    for forbidden in ["package.json", ".prettierrc", "ruff.toml", ".black.toml"]:
        assert not (ROOT / forbidden).exists(), f"forbidden artifact {forbidden}"


def test_enforces_modular_layer_boundaries() -> None:
    math_dir = ROOT / "src" / "app" / "modules" / "math"
    entity = (math_dir / "entity.py").read_text(encoding="utf-8")
    dto = (math_dir / "dto.py").read_text(encoding="utf-8")
    repo = (math_dir / "repository.py").read_text(encoding="utf-8")
    service = (math_dir / "service.py").read_text(encoding="utf-8")
    controller = (math_dir / "controller.py").read_text(encoding="utf-8")

    for forbidden in ("service", "controller", "repository"):
        assert forbidden not in entity, f"entity.py leaked {forbidden}"
        assert forbidden not in dto, f"dto.py leaked {forbidden}"
    assert "service" not in repo and "controller" not in repo
    assert "controller" not in service
    assert "repository" not in controller
