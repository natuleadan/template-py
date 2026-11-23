"""Integration tests for FastAPI endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_greet_endpoint() -> None:
    resp = client.get("/greet/Python")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Hello, Python"}


def test_math_add_endpoint() -> None:
    resp = client.get("/math/add?a=15&b=27")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["sum"] == 42
    assert payload["history_count"] >= 1
