"""Shared pytest fixtures."""

from fastapi.testclient import TestClient
import pytest
from app.main import app

@pytest.fixture
def client() -> TestClient:
    """FastAPI test client for making requests."""
    return TestClient(app)
