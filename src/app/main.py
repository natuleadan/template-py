"""FastAPI service entry point."""

from dataclasses import dataclass

from fastapi import FastAPI, HTTPException

from app.modules.math.module import MathModule

app = FastAPI(title="Template Service", version="0.1.0")
math_module = MathModule()


@dataclass(frozen=True)
class HealthResponse:
    """Health check payload."""

    status: str


@dataclass(frozen=True)
class GreetResponse:
    """Greeting payload."""

    message: str


@dataclass(frozen=True)
class MathAddResponse:
    """Addition result payload."""

    sum: int
    history_count: int


def format_greeting(name: str) -> str:
    """Format a greeting string for the given name."""
    cleaned = name.strip() or "World"
    return f"Hello, {cleaned}"


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(status="ok")


@app.get("/greet/{name}", response_model=GreetResponse)
def greet(name: str) -> GreetResponse:
    """Return a formatted greeting for the path parameter."""
    return GreetResponse(message=format_greeting(name))


@app.get("/math/add", response_model=MathAddResponse)
def math_add(a: int, b: int) -> MathAddResponse:
    """Add two integers through the modular math controller."""
    try:
        res = math_module.controller.handle_add(a, b)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MathAddResponse(sum=res.sum, history_count=res.history_count)
