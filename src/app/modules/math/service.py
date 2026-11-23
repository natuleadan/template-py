"""Business logic service for math operations."""

from app.modules.math.dto import AddRequest, AddResponse, validate_add_request
from app.modules.math.entity import CalculationEntry
from app.modules.math.repository import MathRepository


class MathService:
    """Orchestrates validated addition and history persistence."""

    def __init__(self, repo: MathRepository) -> None:
        self._repo = repo

    def add(self, req: AddRequest) -> AddResponse:
        """Validate, sum, and record an addition request."""
        validate_add_request(req)
        total = req.a + req.b
        self._repo.save(CalculationEntry(a=req.a, b=req.b, sum=total))
        return AddResponse(sum=total, history_count=self._repo.count())
