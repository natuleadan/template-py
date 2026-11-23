"""Pure domain entity for math calculation history."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CalculationEntry:
    """Recorded addition operation."""

    a: int
    b: int
    sum: int
