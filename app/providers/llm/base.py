"""LLM provider interface."""

from typing import Protocol


class LLMProvider(Protocol):
    """Protocol for LLM completion. Implementations: gemini, anthropic."""

    async def complete(self, messages: list[dict[str, str]]) -> str:
        """Send chat turns and return the assistant-visible text.

        *messages* is the engine's **provider-agnostic** format: ordered dicts with
        string ``role`` (e.g. ``system``, ``user``, ``assistant``) and string
        ``content``. Each adapter maps this shape to its vendor API.
        """
        ...
