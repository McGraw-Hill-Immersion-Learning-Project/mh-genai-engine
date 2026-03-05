"""Voyage AI embedding provider.

Skeleton satisfying the EmbeddingProvider protocol.
Real SDK integration (voyageai package) deferred to Sprint 2.
"""


class VoyageEmbeddingProvider:
    """Voyage AI text embedding provider (recommended by Anthropic)."""

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError(
            "VoyageEmbeddingProvider.embed() not yet implemented — "
            "install the voyageai SDK and wire up in Sprint 2."
        )
