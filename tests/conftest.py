"""Shared pytest fixtures."""

from fastapi.testclient import TestClient

from app.main import app


def client() -> TestClient:
    """FastAPI test client for making requests."""
    return TestClient(app)
