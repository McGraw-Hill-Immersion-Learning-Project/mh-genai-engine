"""Tests for AnthropicLLMProvider (SDK integration)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from anthropic.types import TextBlock

from app.providers.llm.anthropic import (
    AnthropicLLMProvider,
    _anthropic_messages_from_chat,
    _text_from_message,
)


class TestAnthropicHelpers:
    def test_split_system_and_merges_same_role(self) -> None:
        system, conv = _anthropic_messages_from_chat(
            [
                {"role": "system", "content": "A"},
                {"role": "system", "content": "B"},
                {"role": "user", "content": "Hi"},
                {"role": "user", "content": "Again"},
                {"role": "assistant", "content": "Hey"},
            ]
        )
        assert system == "A\n\nB"
        assert conv == [
            {"role": "user", "content": "Hi\n\nAgain"},
            {"role": "assistant", "content": "Hey"},
        ]

    def test_text_from_message_joins_text_blocks(self) -> None:
        from anthropic.types import Message

        msg = Message(
            id="msg_1",
            content=[
                TextBlock(text="Hello ", type="text"),
                TextBlock(text="world", type="text"),
            ],
            model="claude-sonnet-4-20250514",
            role="assistant",
            stop_reason="end_turn",
            type="message",
            usage={"input_tokens": 1, "output_tokens": 2},
        )
        assert _text_from_message(msg) == "Hello world"


class TestAnthropicLLMProvider:
    def test_stores_model_and_max_tokens(self) -> None:
        with patch("app.providers.llm.anthropic.AsyncAnthropic"):
            provider = AnthropicLLMProvider(
                api_key="sk-test", model="claude-sonnet-4-20250514", max_tokens=1024
            )
        assert provider._model == "claude-sonnet-4-20250514"
        assert provider._max_tokens == 1024

    @pytest.mark.asyncio
    async def test_complete_calls_messages_create_and_returns_text(self) -> None:
        from anthropic.types import Message

        api_response = Message(
            id="msg_1",
            content=[TextBlock(text="JSON here", type="text")],
            model="m",
            role="assistant",
            stop_reason="end_turn",
            type="message",
            usage={"input_tokens": 1, "output_tokens": 2},
        )

        mock_client = MagicMock()
        mock_client.messages = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=api_response)

        with patch(
            "app.providers.llm.anthropic.AsyncAnthropic",
            return_value=mock_client,
        ):
            provider = AnthropicLLMProvider(api_key="sk-test", model="m", max_tokens=512)

        out = await provider.complete(
            [
                {"role": "system", "content": "sys"},
                {"role": "user", "content": "go"},
            ]
        )

        assert out == "JSON here"
        mock_client.messages.create.assert_awaited_once()
        call_kw = mock_client.messages.create.await_args.kwargs
        assert call_kw["model"] == "m"
        assert call_kw["max_tokens"] == 512
        assert call_kw["system"] == "sys"
        assert call_kw["messages"] == [{"role": "user", "content": "go"}]

    @pytest.mark.asyncio
    async def test_complete_omits_system_when_none(self) -> None:
        from anthropic.types import Message

        api_response = Message(
            id="msg_1",
            content=[TextBlock(text="x", type="text")],
            model="m",
            role="assistant",
            stop_reason="end_turn",
            type="message",
            usage={"input_tokens": 1, "output_tokens": 1},
        )
        mock_client = MagicMock()
        mock_client.messages = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=api_response)
        with patch(
            "app.providers.llm.anthropic.AsyncAnthropic",
            return_value=mock_client,
        ):
            provider = AnthropicLLMProvider(api_key="k", model="m")
        await provider.complete([{"role": "user", "content": "hi"}])
        call_kw = mock_client.messages.create.await_args.kwargs
        assert "system" not in call_kw

    @pytest.mark.asyncio
    async def test_complete_raises_when_no_user_messages(self) -> None:
        with patch("app.providers.llm.anthropic.AsyncAnthropic"):
            provider = AnthropicLLMProvider(api_key="sk-test", model="m")
        with pytest.raises(ValueError, match="at least one non-empty"):
            await provider.complete([{"role": "system", "content": "only system"}])
