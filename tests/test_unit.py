"""Unit tests for core helpers and modular math domain."""

import pytest

from app.main import format_greeting
from app.modules.math.module import MathModule


def test_format_greeting_trims_and_defaults() -> None:
    assert format_greeting("  ") == "Hello, World"
    assert format_greeting("Template") == "Hello, Template"


def test_math_module_adds_and_validates() -> None:
    mod = MathModule()
    res = mod.controller.handle_add(15, 27)
    assert res.sum == 42
    assert res.history_count == 1
    with pytest.raises(ValueError, match="safe template bounds"):
        mod.controller.handle_add(2_000_000_000, 1)
