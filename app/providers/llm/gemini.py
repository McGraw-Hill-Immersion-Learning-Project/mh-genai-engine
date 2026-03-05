"""Gemini LLM provider.

Skeleton satisfying the LLMProvider protocol.
Real SDK integration (google-genai package) deferred.
"""


class GeminiLLMProvider:
    """Google Gemini completion provider."""

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def complete(self, messages: list[dict[str, str]]) -> str:
        raise NotImplementedError(
            "GeminiLLMProvider.complete() not yet implemented — "
            "install the google-genai SDK and wire up when needed."
        )
