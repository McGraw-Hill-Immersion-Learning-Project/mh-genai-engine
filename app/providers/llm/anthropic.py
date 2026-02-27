"""Anthropic LLM provider using Claude."""

import anthropic

from app.config import settings


class AnthropicLLMProvider:
    """Generate responses using Anthropic's Claude."""

    def __init__(self):
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def complete(self, messages: list[dict[str, str]]) -> str:
        """Send messages to Claude and return the generated text."""
        system = ""
        user_messages = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                user_messages.append(m)

        response = await self._client.messages.create(
            model=settings.llm_model,
            max_tokens=1024,
            system=system,
            messages=user_messages,
        )
        return response.content[0].text
