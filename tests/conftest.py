"""Shared pytest fixtures."""

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

# Load .env so pytest sees DATABASE_URL etc. (e.g. for pgvector tests)
load_dotenv()

from app.core.rag.retriever import Retriever
from app.deps import get_llm, get_retriever
from app.main import app
from tests.mocks import (
    AdaptiveLessonOutlineFakeLLM,
    FakeEmbeddingProvider,
    seed_default_lesson_outline_store,
)


@pytest.fixture
def client() -> TestClient:
    """HTTP client with RAG deps overridden (in-memory store + fake LLM, no live APIs)."""
    store = seed_default_lesson_outline_store()
    embedder = FakeEmbeddingProvider(dimensions=8)
    fake_llm = AdaptiveLessonOutlineFakeLLM()

    app.dependency_overrides[get_retriever] = lambda: Retriever(embedder, store)
    app.dependency_overrides[get_llm] = lambda: fake_llm

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
