"""Golden prompts: diverse objectives through the pipeline with grounded citations."""

from __future__ import annotations

import asyncio

import pytest

from app.core.rag.generator import Generator
from app.core.rag.pipeline import LessonOutlinePipeline
from app.core.rag.prompts.template_strategy import TemplatedLessonOutlineStrategy
from app.core.rag.retriever import Retriever
from app.models.generate import (
    AudienceLevel,
    CITATION_SNIPPET_MAX_LEN,
    ContentType,
    LessonOutlineRequest,
)
from tests.mocks import FakeEmbeddingProvider, FakeLLMProvider, InMemoryVectorStore

# Distinct semantic queries; same chapter filter and chunk metadata for citation checks.
_GOLDEN_OBJECTIVES: tuple[str, ...] = (
    "Explain the role of osteoblasts in bone matrix deposition.",
    "Compare compact versus spongy bone at the microscopic level.",
    "Describe the haversian canal system within an osteon.",
    "Outline how bone remodeling maintains mineral homeostasis.",
    "Identify clinical signs associated with accelerated bone resorption.",
    "Relate trabecular architecture to mechanical load direction.",
    "Summarize stages of endochondral ossification in long bones.",
    "Differentiate osteocytes from osteoclasts by function.",
    "Explain why vitamin D deficiency affects bone mineralization.",
    "Connect exercise intensity to trabecular and cortical adaptation.",
)


@pytest.fixture
def golden_pipeline() -> LessonOutlinePipeline:
    store = InMemoryVectorStore()
    meta = {
        "title": "Golden OER — Skeletal System",
        "page_number": 200,
        "chapter": "6",
        "section": "6.2",
        "source_key": "golden.pdf",
        "chunk_id": "g0",
    }

    async def _seed() -> None:
        await store.add_documents(
            [
                "Bone tissue contains osteocytes in lacunae; remodeling couples "
                "osteoblast and osteoclast activity across trabecular and cortical regions."
            ],
            [[0.0] * 8],
            [meta],
        )

    asyncio.run(_seed())
    retriever = Retriever(FakeEmbeddingProvider(dimensions=8), store)
    gen = Generator(FakeLLMProvider(), TemplatedLessonOutlineStrategy())
    return LessonOutlinePipeline(retriever, gen, n_results=8)


@pytest.mark.asyncio
@pytest.mark.parametrize("learning_objective", _GOLDEN_OBJECTIVES)
async def test_golden_prompt_produces_structured_answer_with_citations(
    golden_pipeline: LessonOutlinePipeline,
    learning_objective: str,
) -> None:
    req = LessonOutlineRequest(
        chapter="6",
        learningObjective=learning_objective,
        contentType=ContentType.LECTURE_NOTES,
        count=45,
        audienceLevel=AudienceLevel.INTERMEDIATE,
    )
    resp = await golden_pipeline.run(req)

    assert resp.outline.strip()
    assert resp.key_concepts is not None and len(resp.key_concepts) >= 1
    assert resp.misconceptions is not None and len(resp.misconceptions) >= 1
    assert len(resp.citations) >= 1
    cite = resp.citations[0]
    assert cite.chunk_id == "golden.pdf_g0"
    assert cite.title == "Golden OER — Skeletal System"
    assert cite.chapter == "6"
    assert cite.section == "6.2"
    assert cite.page == "200"
    assert len(cite.snippet) <= CITATION_SNIPPET_MAX_LEN
    assert cite.snippet.startswith("Bone tissue") or "osteocyte" in cite.snippet
