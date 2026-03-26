"""Integration tests for LessonOutlinePipeline (all external deps mocked)."""

import pytest

from app.models.generate import (
    AudienceLevel,
    ContentType,
    LessonOutlineRequest,
)
from app.core.rag.generator import Generator
from app.db.vector.filters import VectorMetadataFilter
from app.core.rag.pipeline import LessonOutlinePipeline
from app.core.rag.prompts.template_strategy import TemplatedLessonOutlineStrategy
from app.core.rag.retriever import Retriever

from tests.mocks import FakeEmbeddingProvider, FakeLLMProvider, InMemoryVectorStore


@pytest.mark.asyncio
async def test_pipeline_end_to_end_with_mocks() -> None:
    store = InMemoryVectorStore()
    await store.add_documents(
        documents=["Chunk about osteons."],
        embeddings=[[0.0] * 8],
        metadatas=[
            {
                "source_key": "bio.pdf",
                "chunk_id": 0,
                "title": "Biology",
                "page_number": 10,
                "chapter": "4",
                "section": "4.2",
            }
        ],
    )

    retriever = Retriever(FakeEmbeddingProvider(dimensions=8), store)
    generator = Generator(FakeLLMProvider(), TemplatedLessonOutlineStrategy())
    pipeline = LessonOutlinePipeline(retriever, generator, n_results=5)

    request = LessonOutlineRequest(
        chapter="4",
        section="4.2",
        learningObjective="Explain osteons",
        contentType=ContentType.LECTURE_NOTES,
        count=30,
        audienceLevel=AudienceLevel.BEGINNER,
    )

    resp = await pipeline.run(request)

    assert "Intro" in resp.outline or "osteon" in resp.outline.lower()
    assert len(resp.citations) >= 1
    assert resp.citations[0].chapter == "4"
    assert resp.citations[0].title == "Biology"


def test_build_embedding_query_uses_objective_audience_and_duration() -> None:
    req = LessonOutlineRequest(
        chapter="1",
        learningObjective="Objective",
        contentType=ContentType.LECTURE_NOTES,
        count=10,
        audienceLevel=AudienceLevel.ADVANCED,
        book="My Book",
    )
    q = LessonOutlinePipeline.build_embedding_query(req)
    assert "Objective" in q
    assert "advanced" in q.lower()
    assert "10" in q
    assert "minutes" in q.lower()
    assert "My Book" not in q


def test_metadata_filter_for_request_maps_structural_fields() -> None:
    req = LessonOutlineRequest(
        chapter="2",
        section="2.1",
        subSection="2.1.0",
        book="Physics 101",
        learningObjective="X",
        contentType=ContentType.LECTURE_NOTES,
        count=5,
        audienceLevel=AudienceLevel.BEGINNER,
    )
    f = LessonOutlinePipeline.metadata_filter_for_request(req)
    assert f == VectorMetadataFilter(
        chapter="2",
        section="2.1",
        sub_section="2.1.0",
        book="Physics 101",
    )


@pytest.mark.asyncio
async def test_pipeline_metadata_filter_excludes_wrong_chapter() -> None:
    store = InMemoryVectorStore()
    await store.add_documents(
        documents=["Wrong chapter text"],
        embeddings=[[0.0] * 8],
        metadatas=[
            {
                "source_key": "a.pdf",
                "chunk_id": 0,
                "title": "Bio",
                "page_number": 1,
                "chapter": "99",
                "section": "4.2",
            }
        ],
    )
    retriever = Retriever(FakeEmbeddingProvider(dimensions=8), store)
    generator = Generator(FakeLLMProvider(), TemplatedLessonOutlineStrategy())
    pipeline = LessonOutlinePipeline(retriever, generator, n_results=5)

    request = LessonOutlineRequest(
        chapter="4",
        section="4.2",
        learningObjective="Explain osteons",
        contentType=ContentType.LECTURE_NOTES,
        count=30,
        audienceLevel=AudienceLevel.BEGINNER,
    )
    resp = await pipeline.run(request)
    assert "Passage [0]" not in (resp.outline or "")
    assert resp.citations == []
