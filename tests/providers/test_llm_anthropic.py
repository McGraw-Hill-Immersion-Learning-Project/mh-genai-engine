"""Tests for AnthropicLLMProvider skeleton."""

import pytest

from app.providers.llm.anthropic import AnthropicLLMProvider


class TestAnthropicLLMProvider:
    def test_instantiates_with_api_key_and_model(self) -> None:
        provider = AnthropicLLMProvider(api_key="sk-test", model="claude-sonnet-4-6")
        assert provider._api_key == "sk-test"
        assert provider._model == "claude-sonnet-4-6"

    @pytest.mark.asyncio
    async def test_complete_raises_not_implemented(self) -> None:
        provider = AnthropicLLMProvider(api_key="sk-test", model="claude-sonnet-4-6")
        with pytest.raises(NotImplementedError, match="not yet implemented"):
            await provider.complete([{"role": "user", "content": "hello"}])
