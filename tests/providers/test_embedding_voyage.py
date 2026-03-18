"""Tests for VoyageEmbeddingProvider."""

from unittest.mock import MagicMock

import pytest

from app.providers.embeddings.voyage import VoyageEmbeddingProvider


class TestVoyageEmbeddingProvider:
    def test_instantiates_with_api_key_and_model(self) -> None:
        provider = VoyageEmbeddingProvider(api_key="voy-test", model="voyage-4-lite")
        assert provider._model == "voyage-4-lite"
        assert provider._client is not None

    @pytest.mark.asyncio
    async def test_embed_returns_vectors(self) -> None:
        provider = VoyageEmbeddingProvider(api_key="voy-test", model="voyage-4-lite")
        fake_result = MagicMock()
        fake_result.embeddings = [[0.1] * 1024, [0.2] * 1024]
        provider._client.embed = MagicMock(return_value=fake_result)

        result = await provider.embed(["text one", "text two"])

        assert len(result) == 2
        assert len(result[0]) == 1024
        assert result[0][0] == 0.1
        provider._client.embed.assert_called_once()
