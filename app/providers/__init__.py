"""External service adapters (ports & adapters pattern).

Factory functions select the concrete provider based on Settings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.utils import make_pgvector_table_name

if TYPE_CHECKING:
    from app.config import Settings
    from app.providers.llm.base import LLMProvider
    from app.providers.embeddings.base import EmbeddingProvider
    from app.providers.storage.base import StorageProvider
    from app.db.vector.base import VectorStore


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

    if provider == "dev":
        from app.providers.embeddings.dev import DevEmbeddingProvider

        return DevEmbeddingProvider(dimensions=settings.embedding_dimensions)

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
        f"Unknown embedding provider: {provider!r}. Supported: 'dev', 'voyage', 'gemini'."
    )


def get_storage_provider(settings: Settings) -> StorageProvider:
    """Return the storage provider configured in *settings*."""
    provider = settings.storage_provider.lower()

    if provider == "local":
        from app.providers.storage.local import LocalStorageProvider

        return LocalStorageProvider(base_path=settings.storage_local_path)

    raise ValueError(
        f"Unknown storage provider: {provider!r}. Supported: 'local'."
    )


def get_vector_store(settings: Settings) -> VectorStore:
    """Return the vector store configured in *settings*.

    Raises ``ValueError`` for an unknown provider or missing database_url.
    """
    provider = settings.vector_db_provider.lower()

    if provider == "pgvector":
        if not settings.database_url:
            raise ValueError(
                "DATABASE_URL is required when VECTOR_DB_PROVIDER=pgvector"
            )
        from app.db.vector.pgvector import PgvectorStore

        table_name = make_pgvector_table_name(
            prefix="chunks",
            embedding_provider=settings.embedding_provider,
            embedding_model=settings.embedding_model,
            embedding_dimensions=settings.embedding_dimensions,
        )

        return PgvectorStore(
            database_url=settings.database_url,
            table_name=table_name,
            dimensions=settings.embedding_dimensions,
        )

    raise ValueError(
        f"Unknown vector DB provider: {provider!r}. Supported: 'pgvector'."
    )
