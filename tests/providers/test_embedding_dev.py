"""Tests for DevEmbeddingProvider."""

import pytest

from app.providers.embeddings.dev import DevEmbeddingProvider


class TestDevEmbeddingProvider:
    def test_instantiates_with_dimensions(self) -> None:
        provider = DevEmbeddingProvider(dimensions=16)
        assert provider._dimensions == 16

    @pytest.mark.asyncio
    async def test_embed_returns_deterministic_vectors(self) -> None:
        provider = DevEmbeddingProvider(dimensions=8)

        v1 = await provider.embed(["hello", "world"])
        v2 = await provider.embed(["hello", "world"])

        assert v1 == v2
        assert len(v1) == 2
        assert len(v1[0]) == 8
        assert len(v1[1]) == 8

    @pytest.mark.asyncio
    async def test_embed_empty_list_returns_empty(self) -> None:
        provider = DevEmbeddingProvider(dimensions=8)
        result = await provider.embed([])
        assert result == []

