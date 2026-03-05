"""Gemini embedding provider.

Skeleton satisfying the EmbeddingProvider protocol.
Real SDK integration (google-genai package) deferred.
"""


class GeminiEmbeddingProvider:
    """Google Gemini text embedding provider."""

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError(
            "GeminiEmbeddingProvider.embed() not yet implemented — "
            "install the google-genai SDK and wire up when needed."
        )
