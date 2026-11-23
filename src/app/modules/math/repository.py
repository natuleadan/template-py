"""Persistence port and in-memory adapter for math calculations."""

from typing import Protocol

from app.modules.math.entity import CalculationEntry


class MathRepository(Protocol):
    """Storage abstraction for calculation records."""

    def save(self, entry: CalculationEntry) -> None:
        """Persist a calculation entry."""
        ...

    def count(self) -> int:
        """Return total number of recorded entries."""
        ...

    def list_entries(self) -> list[CalculationEntry]:
        """Return a snapshot list of recorded entries."""
        ...


class InMemoryMathRepository:
    """In-memory calculation store."""

    def __init__(self) -> None:
        self._entries: list[CalculationEntry] = []

    def save(self, entry: CalculationEntry) -> None:
        """Append a calculation entry to memory."""
        self._entries.append(entry)

    def count(self) -> int:
        """Return total number of stored entries."""
        return len(self._entries)

    def list_entries(self) -> list[CalculationEntry]:
        """Return a shallow copy of stored entries."""
        return list(self._entries)
