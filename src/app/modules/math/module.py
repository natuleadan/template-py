"""Module container wiring the math domain layers."""

from app.modules.math.controller import MathController
from app.modules.math.repository import InMemoryMathRepository
from app.modules.math.service import MathService


class MathModule:
    """Assembled math module exposing the domain controller."""

    def __init__(self) -> None:
        repo = InMemoryMathRepository()
        service = MathService(repo)
        self.controller = MathController(service)
