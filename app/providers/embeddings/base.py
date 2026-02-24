"""Embedding provider interface."""

from typing import Protocol


class EmbeddingProvider(Protocol):
    """Protocol for embedding texts. Implementations: gemini."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts and return vectors."""
        ...
