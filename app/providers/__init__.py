"""External service adapters (ports & adapters pattern).

Factory functions select the concrete provider based on Settings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.config import Settings
    from app.providers.llm.base import LLMProvider
    from app.providers.embeddings.base import EmbeddingProvider


def get_llm_provider(settings: Settings) -> LLMProvider:
    """Return the LLM provider configured in *settings*.

    Raises ``ValueError`` for an unknown provider name or missing API key.
    """
    provider = settings.llm_provider.lower()

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        from app.providers.llm.anthropic import AnthropicLLMProvider

        return AnthropicLLMProvider(
            api_key=settings.anthropic_api_key,
            model=settings.llm_model,
        )

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        from app.providers.llm.gemini import GeminiLLMProvider

        return GeminiLLMProvider(
            api_key=settings.gemini_api_key,
            model=settings.llm_model,
        )

    raise ValueError(
        f"Unknown LLM provider: {provider!r}. Supported: 'anthropic', 'gemini'."
    )


def get_embedding_provider(settings: Settings) -> EmbeddingProvider:
    """Return the embedding provider configured in *settings*.

    Raises ``ValueError`` for an unknown provider name or missing API key.
    """
    provider = settings.embedding_provider.lower()

    if provider == "voyage":
        if not settings.voyage_api_key:
            raise ValueError("VOYAGE_API_KEY is required when EMBEDDING_PROVIDER=voyage")
        from app.providers.embeddings.voyage import VoyageEmbeddingProvider

        return VoyageEmbeddingProvider(
            api_key=settings.voyage_api_key,
            model=settings.embedding_model,
        )

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when EMBEDDING_PROVIDER=gemini")
        from app.providers.embeddings.gemini import GeminiEmbeddingProvider

        return GeminiEmbeddingProvider(
            api_key=settings.gemini_api_key,
            model=settings.embedding_model,
        )

    raise ValueError(
        f"Unknown embedding provider: {provider!r}. Supported: 'voyage', 'gemini'."
    )
