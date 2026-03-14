"""Voyage AI embedding provider."""

import asyncio

import voyageai


class VoyageEmbeddingProvider:
    """Voyage AI text embedding provider (recommended by Anthropic)."""

    def __init__(self, api_key: str, model: str) -> None:
        self._client = voyageai.Client(api_key=api_key)
        self._model = model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts and return vectors."""
        if not texts:
            return []
        # Run sync SDK call in thread pool to avoid blocking
        result = await asyncio.to_thread(
            self._client.embed,
            texts,
            model=self._model,
            input_type="document",
        )
        return result.embeddings
