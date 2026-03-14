"""Tests for provider factory functions."""

import pytest

from app.config import Settings
from app.providers import (
    get_embedding_provider,
    get_llm_provider,
    get_storage_provider,
    get_vector_store,
)
from app.db.vector.pgvector import PgvectorStore
from app.providers.embeddings.gemini import GeminiEmbeddingProvider
from app.providers.embeddings.voyage import VoyageEmbeddingProvider
from app.providers.llm.anthropic import AnthropicLLMProvider
from app.providers.llm.gemini import GeminiLLMProvider
from app.providers.storage.local import LocalStorageProvider


def _settings(**overrides) -> Settings:
    """Build a Settings object with test defaults, merging *overrides*."""
    defaults = {
        "llm_provider": "anthropic",
        "llm_model": "claude-sonnet-4-6",
        "embedding_provider": "voyage",
        "embedding_model": "voyage-4-lite",
        "anthropic_api_key": "sk-test",
        "voyage_api_key": "voy-test",
        "gemini_api_key": "",
    }
    defaults.update(overrides)
    return Settings(**defaults)


# ── get_llm_provider ────────────────────────────────────────────────


class TestGetLLMProvider:
    def test_returns_anthropic_provider(self) -> None:
        provider = get_llm_provider(_settings())
        assert isinstance(provider, AnthropicLLMProvider)

    def test_returns_gemini_provider(self) -> None:
        provider = get_llm_provider(
            _settings(llm_provider="gemini", gemini_api_key="gk-test")
        )
        assert isinstance(provider, GeminiLLMProvider)

    def test_raises_for_unknown_provider(self) -> None:
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_llm_provider(_settings(llm_provider="openai"))

    def test_raises_when_anthropic_key_missing(self) -> None:
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            get_llm_provider(_settings(anthropic_api_key=""))

    def test_raises_when_gemini_key_missing(self) -> None:
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            get_llm_provider(_settings(llm_provider="gemini", gemini_api_key=""))

    def test_provider_name_is_case_insensitive(self) -> None:
        provider = get_llm_provider(_settings(llm_provider="Anthropic"))
        assert isinstance(provider, AnthropicLLMProvider)


# ── get_embedding_provider ──────────────────────────────────────────


class TestGetEmbeddingProvider:
    def test_returns_voyage_provider(self) -> None:
        provider = get_embedding_provider(_settings())
        assert isinstance(provider, VoyageEmbeddingProvider)

    def test_returns_gemini_provider(self) -> None:
        provider = get_embedding_provider(
            _settings(embedding_provider="gemini", gemini_api_key="gk-test")
        )
        assert isinstance(provider, GeminiEmbeddingProvider)

    def test_raises_for_unknown_provider(self) -> None:
        with pytest.raises(ValueError, match="Unknown embedding provider"):
            get_embedding_provider(_settings(embedding_provider="openai"))

    def test_raises_when_voyage_key_missing(self) -> None:
        with pytest.raises(ValueError, match="VOYAGE_API_KEY"):
            get_embedding_provider(_settings(voyage_api_key=""))

    def test_raises_when_gemini_key_missing(self) -> None:
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            get_embedding_provider(
                _settings(embedding_provider="gemini", gemini_api_key="")
            )

    def test_provider_name_is_case_insensitive(self) -> None:
        provider = get_embedding_provider(_settings(embedding_provider="Voyage"))
        assert isinstance(provider, VoyageEmbeddingProvider)


# ── get_storage_provider ────────────────────────────────────────────


class TestGetStorageProvider:
    def test_returns_local_provider(self) -> None:
        provider = get_storage_provider(_settings())
        assert isinstance(provider, LocalStorageProvider)

    def test_raises_for_unknown_provider(self) -> None:
        with pytest.raises(ValueError, match="Unknown storage provider"):
            get_storage_provider(_settings(storage_provider="s3"))


# ── get_vector_store ────────────────────────────────────────────────


class TestGetVectorStore:
    def test_returns_pgvector_store(self) -> None:
        store = get_vector_store(
            _settings(
                vector_db_provider="pgvector",
                database_url="postgresql://u:p@localhost:5432/db",
            )
        )
        assert isinstance(store, PgvectorStore)

    def test_raises_for_unknown_provider(self) -> None:
        with pytest.raises(ValueError, match="Unknown vector DB provider"):
            get_vector_store(
                _settings(
                    vector_db_provider="chroma",
                    database_url="postgresql://u:p@localhost:5432/db",
                )
            )

    def test_raises_when_database_url_missing(self) -> None:
        with pytest.raises(ValueError, match="DATABASE_URL"):
            get_vector_store(
                _settings(vector_db_provider="pgvector", database_url="")
            )
