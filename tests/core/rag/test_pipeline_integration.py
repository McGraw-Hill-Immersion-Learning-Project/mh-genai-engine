"""Integration test: LessonOutlinePipeline with in-memory vector store and fake LLM."""

from __future__ import annotations

import pytest

from app.core.rag.generator import Generator
from app.core.rag.pipeline import LessonOutlinePipeline
from app.core.rag.prompts.template_strategy import TemplatedLessonOutlineStrategy
from app.core.rag.retriever import Retriever
from app.models.generate import (
    AudienceLevel,
    ContentType,
    LessonOutlineRequest,
)
from tests.mocks import FakeEmbeddingProvider, FakeLLMProvider, InMemoryVectorStore


@pytest.mark.asyncio
async def test_pipeline_retrieves_then_generates_with_grounded_citations() -> None:
    store = InMemoryVectorStore()
    meta = {
        "title": "Integration Textbook",
        "page_number": 55,
        "chapter": "4",
        "section": "4.2",
        "source_key": "int.pdf",
        "chunk_id": "a",
    }
    await store.add_documents(
        ["Neurons transmit signals via action potentials along axons."],
        [[0.0] * 8],
        [meta],
    )
    retriever = Retriever(FakeEmbeddingProvider(dimensions=8), store)
    gen = Generator(FakeLLMProvider(), TemplatedLessonOutlineStrategy())
    pipeline = LessonOutlinePipeline(retriever, gen, n_results=5)

    req = LessonOutlineRequest(
        chapter="4",
        section="4.2",
        learningObjective="Describe how neurons propagate electrical signals.",
        contentType=ContentType.LECTURE_NOTES,
        count=30,
        audienceLevel=AudienceLevel.BEGINNER,
    )
    resp = await pipeline.run(req)

    assert resp.outline.startswith("I. Intro")
    assert len(resp.citations) == 1
    assert resp.citations[0].title == "Integration Textbook"
    assert resp.citations[0].chunk_id == "int.pdf_a"
    assert resp.citations[0].page == "55"
    assert resp.citations[0].chapter == "4"
    assert resp.citations[0].section == "4.2"


@pytest.mark.asyncio
async def test_pipeline_embedding_query_uses_objective_and_audience() -> None:
    """Retriever should embed the semantic query string built from the request."""

    class CaptureEmbedder:
        def __init__(self) -> None:
            self.texts: list[list[str]] = []

        async def embed(self, texts: list[str]) -> list[list[float]]:
            self.texts.append(list(texts))
            return [[0.0] * 8]

    store = InMemoryVectorStore()
    await store.add_documents(["x"], [[0.0] * 8], [{"chapter": "1", "chunk_id": 0}])
    emb = CaptureEmbedder()
    retriever = Retriever(emb, store)
    gen = Generator(FakeLLMProvider(), TemplatedLessonOutlineStrategy())
    pipeline = LessonOutlinePipeline(retriever, gen)

    req = LessonOutlineRequest(
        chapter="1",
        learningObjective="Define osmosis across membranes.",
        contentType=ContentType.LECTURE_NOTES,
        count=20,
        audienceLevel=AudienceLevel.ADVANCED,
    )
    await pipeline.run(req)

    assert len(emb.texts) == 1
    q = emb.texts[0][0]
    assert "osmosis" in q.lower()
    assert "advanced" in q.lower()
    assert "20" in q
