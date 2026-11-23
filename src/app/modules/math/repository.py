"""Persistence port and in-memory adapter for math calculations."""

from typing import Protocol

from app.modules.math.entity import CalculationEntry


class MathRepository(Protocol):
    """Storage abstraction for calculation records."""

    def save(self, entry: CalculationEntry) -> None: ...
    def count(self) -> int: ...
    def list_entries(self) -> list[CalculationEntry]: ...


class InMemoryMathRepository:
    """In-memory calculation store."""

    def __init__(self) -> None:
        self._entries: list[CalculationEntry] = []

    def save(self, entry: CalculationEntry) -> None:
        self._entries.append(entry)

    def count(self) -> int:
        return len(self._entries)

    def list_entries(self) -> list[CalculationEntry]:
        return list(self._entries)
