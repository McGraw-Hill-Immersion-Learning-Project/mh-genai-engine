"""Tests for VoyageEmbeddingProvider skeleton."""

import pytest

from app.providers.embeddings.voyage import VoyageEmbeddingProvider


class TestVoyageEmbeddingProvider:
    def test_instantiates_with_api_key_and_model(self) -> None:
        provider = VoyageEmbeddingProvider(api_key="voy-test", model="voyage-3-large")
        assert provider._api_key == "voy-test"
        assert provider._model == "voyage-3-large"

    @pytest.mark.asyncio
    async def test_embed_raises_not_implemented(self) -> None:
        provider = VoyageEmbeddingProvider(api_key="voy-test", model="voyage-3-large")
        with pytest.raises(NotImplementedError, match="not yet implemented"):
            await provider.embed(["some text"])
