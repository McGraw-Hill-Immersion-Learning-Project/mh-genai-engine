"""LLM provider interface."""

from typing import Protocol


class LLMProvider(Protocol):
    """Protocol for LLM completion. Implementations: gemini, anthropic."""

    async def complete(self, messages: list[dict[str, str]]) -> str:
        """Send messages to the LLM and return the generated text."""
        ...
