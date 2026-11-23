"""Transport-facing controller for the math domain."""

from app.modules.math.dto import AddRequest, AddResponse
from app.modules.math.service import MathService


class MathController:
    """Entrypoint adapter delegating validated requests to MathService."""

    def __init__(self, service: MathService) -> None:
        self._service = service

    def handle_add(self, a: int, b: int) -> AddResponse:
        """Handle an addition request and return the formatted response."""
        return self._service.add(AddRequest(a=a, b=b))
