"""Anthropic LLM provider.

Skeleton satisfying the LLMProvider protocol.
Real SDK integration (anthropic package) deferred to Sprint 2.
"""


class AnthropicLLMProvider:
    """Anthropic Claude completion provider."""

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def complete(self, messages: list[dict[str, str]]) -> str:
        raise NotImplementedError(
            "AnthropicLLMProvider.complete() not yet implemented — "
            "install the anthropic SDK and wire up in Sprint 2."
        )
