"""Unit tests for Retriever (mocked vector store and embedding provider)."""

import pytest

from app.core.rag.retriever import Retriever, RetrievedChunk
from app.db.vector.filters import VectorMetadataFilter


@pytest.mark.asyncio
async def test_retrieve_embeds_query_and_queries_vector_store() -> None:
    embed_calls: list[list[str]] = []
    query_calls: list[tuple[list[float], int]] = []

    class TrackEmbedder:
        async def embed(self, texts: list[str]) -> list[list[float]]:
            embed_calls.append(list(texts))
            return [[1.0, 0.0, 0.0]]

    class TrackStore:
        async def query(
            self,
            embedding: list[float],
            n_results: int = 10,
            *,
            metadata_filter=None,
        ) -> list[dict]:
            query_calls.append((embedding, n_results, metadata_filter))
            return [
                {
                    "content": "alpha",
                    "metadata": {
                        "title": "Book",
                        "page_number": 3,
                        "chapter": "2",
                        "section": "2.1",
                        "source_key": "a.pdf",
                    },
                    "distance": 0.1,
                }
            ]

    r = Retriever(TrackEmbedder(), TrackStore())
    chunks = await r.retrieve("supply and demand", n_results=5)

    assert embed_calls == [["supply and demand"]]
    assert query_calls == [([1.0, 0.0, 0.0], 5, None)]
    assert len(chunks) == 1
    assert isinstance(chunks[0], RetrievedChunk)
    assert chunks[0].content == "alpha"
    assert chunks[0].metadata["chapter"] == "2"
    assert chunks[0].metadata["page_number"] == 3


@pytest.mark.asyncio
async def test_retrieve_empty_when_embed_returns_no_vectors() -> None:
    class NoVec:
        async def embed(self, texts: list[str]) -> list[list[float]]:
            return []

    class ShouldNotCall:
        async def query(
            self,
            embedding: list[float],
            n_results: int = 10,
            *,
            metadata_filter=None,
        ) -> list[dict]:
            raise AssertionError("query should not be called")

    r = Retriever(NoVec(), ShouldNotCall())
    assert await r.retrieve("x") == []


@pytest.mark.asyncio
async def test_retrieve_normalizes_missing_metadata() -> None:
    class OneVec:
        async def embed(self, texts: list[str]) -> list[list[float]]:
            return [[0.0]]

    class RawRow:
        async def query(
            self,
            embedding: list[float],
            n_results: int = 10,
            *,
            metadata_filter=None,
        ) -> list[dict]:
            return [{"content": "body", "metadata": None, "distance": 0.0}]

    chunks = await Retriever(OneVec(), RawRow()).retrieve("q")
    assert chunks[0].metadata == {}


@pytest.mark.asyncio
async def test_retrieve_forwards_metadata_filter_to_vector_store() -> None:
    captured: list[VectorMetadataFilter | None] = []

    class OneVec:
        async def embed(self, texts: list[str]) -> list[list[float]]:
            return [[1.0]]

    class CaptureStore:
        async def query(
            self,
            embedding: list[float],
            n_results: int = 10,
            *,
            metadata_filter=None,
        ) -> list[dict]:
            captured.append(metadata_filter)
            return []

    flt = VectorMetadataFilter(chapter="3", section="3.1")
    await Retriever(OneVec(), CaptureStore()).retrieve(
        "q", n_results=2, metadata_filter=flt
    )
    assert captured == [flt]
