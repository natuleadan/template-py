"""Data transfer objects and validation for math operations."""

from dataclasses import dataclass

MAX_OPERAND_ABS = 1_000_000_000


@dataclass(frozen=True)
class AddRequest:
    """Request payload for addition."""

    a: int
    b: int


@dataclass(frozen=True)
class AddResponse:
    """Response payload returned after addition."""

    sum: int
    history_count: int


def validate_add_request(req: AddRequest) -> None:
    """Validate operand bounds before domain execution."""
    if abs(req.a) > MAX_OPERAND_ABS or abs(req.b) > MAX_OPERAND_ABS:
        raise ValueError("operand exceeds safe template bounds")
