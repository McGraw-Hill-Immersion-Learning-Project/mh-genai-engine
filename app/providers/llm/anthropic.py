"""Anthropic Claude LLM provider (Messages API).

Uses the official ``anthropic`` Python SDK (``>= 0.80``) async client. API reference:
https://docs.anthropic.com/en/api/messages
"""

from __future__ import annotations

from anthropic import AsyncAnthropic
from anthropic.types import Message, MessageParam, TextBlock


def _anthropic_messages_from_chat(
    messages: list[dict[str, str]],
) -> tuple[str | None, list[MessageParam]]:
    """Map engine chat turns (:class:`~app.providers.llm.base.LLMProvider`) to Anthropic.

    Input uses the shared ``role`` / ``content`` string dicts. Output separates
    ``system`` (top-level string) from ``messages`` (``user`` / ``assistant`` only,
    as :class:`~anthropic.types.message_param.MessageParam`). Consecutive turns with
    the same role are merged so the Messages API alternating constraint holds.
    """
    system_parts: list[str] = []
    conv: list[MessageParam] = []
    for m in messages:
        role = (m.get("role") or "").strip()
        content = (m.get("content") or "").strip()
        if role == "system":
            if content:
                system_parts.append(content)
            continue
        if role not in ("user", "assistant"):
            continue
        if not content:
            continue
        if role == "user":
            if conv and conv[-1]["role"] == "user":
                prev = conv[-1]["content"]
                conv[-1] = {"role": "user", "content": f"{prev}\n\n{content}"}
            else:
                conv.append({"role": "user", "content": content})
        else:
            if conv and conv[-1]["role"] == "assistant":
                prev = conv[-1]["content"]
                conv[-1] = {"role": "assistant", "content": f"{prev}\n\n{content}"}
            else:
                conv.append({"role": "assistant", "content": content})

    system = "\n\n".join(system_parts) if system_parts else None
    return system, conv


def _text_from_message(message: Message) -> str:
    """Collect assistant-visible text from ``Message.content`` (``TextBlock`` only).

    Extended-thinking and tool-use responses may include non-text blocks; those are
    skipped so callers get plain completion text (e.g. JSON for RAG).
    """
    parts: list[str] = []
    for block in message.content:
        if isinstance(block, TextBlock):
            parts.append(block.text)
    return "".join(parts)


class AnthropicLLMProvider:
    """Claude completion via ``AsyncAnthropic.messages.create``."""

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        max_tokens: int = 8192,
    ) -> None:
        self._model = model
        self._max_tokens = max_tokens
        self._client = AsyncAnthropic(api_key=api_key)

    async def complete(self, messages: list[dict[str, str]]) -> str:
        """Implement :class:`~app.providers.llm.base.LLMProvider` via the Messages API.

        *messages* uses the engine's provider-agnostic ``role``/``content`` dicts;
        returns concatenated :class:`~anthropic.types.text_block.TextBlock` text only.
        """
        system, conv = _anthropic_messages_from_chat(messages)
        if not conv:
            raise ValueError(
                "AnthropicLLMProvider.complete requires at least one non-empty "
                "user or assistant message after extracting system prompts."
            )

        if system is not None:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                messages=conv,
                system=system,
            )
        else:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                messages=conv,
            )

        return _text_from_message(response)
