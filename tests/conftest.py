"""Shared pytest fixtures."""

import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

# Load .env so pytest sees DATABASE_URL etc. (e.g. for pgvector tests)
load_dotenv()

from app.main import app

@pytest.fixture
def client() -> TestClient:
    """FastAPI test client for making requests."""
    return TestClient(app)
