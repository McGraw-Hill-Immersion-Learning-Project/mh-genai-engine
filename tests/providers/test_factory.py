"""Tests for provider factory functions."""

import pytest

from app.config import Settings
from app.providers import get_llm_provider, get_embedding_provider
from app.providers.llm.anthropic import AnthropicLLMProvider
from app.providers.llm.gemini import GeminiLLMProvider
from app.providers.embeddings.voyage import VoyageEmbeddingProvider
from app.providers.embeddings.gemini import GeminiEmbeddingProvider


def _settings(**overrides) -> Settings:
    """Build a Settings object with test defaults, merging *overrides*."""
    defaults = {
        "llm_provider": "anthropic",
        "llm_model": "claude-sonnet-4-6",
        "embedding_provider": "voyage",
        "embedding_model": "voyage-3-large",
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
