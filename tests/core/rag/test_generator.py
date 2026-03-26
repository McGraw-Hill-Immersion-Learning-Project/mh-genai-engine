"""Unit tests for Generator (mock LLM)."""

import json

import pytest

from app.models.generate import (
    AudienceLevel,
    ContentType,
    LessonOutlineRequest,
)
from app.core.rag.generator import Generator, citations_from_chunks
from app.core.rag.prompts.template_strategy import TemplatedLessonOutlineStrategy
from app.core.rag.prompts.registry import get_lesson_outline_strategy
from app.core.rag.retriever import RetrievedChunk

from tests.mocks import FakeLLMProvider


def _outline_request(
    *,
    content_type: ContentType = ContentType.LECTURE_NOTES,
) -> LessonOutlineRequest:
    return LessonOutlineRequest(
        chapter="6",
        learningObjective="Describe bone structure",
        contentType=content_type,
        count=45,
        audienceLevel=AudienceLevel.INTERMEDIATE,
    )


@pytest.mark.asyncio
async def test_generator_calls_llm_and_merges_citations_from_chunks() -> None:
    llm = FakeLLMProvider()
    gen = Generator(llm, TemplatedLessonOutlineStrategy())
    chunks = [
        RetrievedChunk(
            content="Osteons form compact bone.",
            metadata={
                "title": "Anatomy",
                "page_number": 142,
                "chapter": "6",
                "section": "6.3",
                "source_key": "ap.pdf",
            },
        )
    ]
    resp = await gen.generate(chunks, _outline_request())

    assert resp.outline.startswith("I. Intro")
    assert resp.key_concepts == ["Concept A", "Concept B"]
    assert len(resp.citations) == 1
    assert resp.citations[0].title == "Anatomy"
    assert resp.citations[0].page == "142"
    assert resp.citations[0].chapter == "6"
    assert resp.citations[0].section == "6.3"

    assert len(llm.calls) == 1
    messages = llm.calls[0]
    assert messages[0]["role"] == "system"
    assert "Osteons form compact bone" in messages[0]["content"]
    assert messages[1]["role"] == "user"


@pytest.mark.asyncio
async def test_generator_forces_slide_outline_none_for_lecture_notes() -> None:
    payload = {
        "outline": "X",
        "keyConcepts": [],
        "misconceptions": [],
        "checksForUnderstanding": [],
        "activityIdeas": [],
        "slideOutline": "Should not appear",
    }
    llm = FakeLLMProvider(json.dumps(payload))
    gen = Generator(llm, TemplatedLessonOutlineStrategy())
    resp = await gen.generate([], _outline_request(content_type=ContentType.LECTURE_NOTES))
    assert resp.slide_outline is None


@pytest.mark.asyncio
async def test_generator_keeps_slide_outline_for_ppt() -> None:
    payload = {
        "outline": "X",
        "keyConcepts": [],
        "misconceptions": [],
        "checksForUnderstanding": [],
        "activityIdeas": [],
        "slideOutline": "Slide 1: Title",
    }
    llm = FakeLLMProvider(json.dumps(payload))
    gen = Generator(llm, TemplatedLessonOutlineStrategy())
    resp = await gen.generate([], _outline_request(content_type=ContentType.PPT))
    assert resp.slide_outline == "Slide 1: Title"


def test_citations_from_chunks_dedupes_and_handles_sparse_metadata() -> None:
    chunks = [
        RetrievedChunk("a", {"title": "T", "page_number": 1, "chapter": "1"}),
        RetrievedChunk("b", {"title": "T", "page_number": 1, "chapter": "1"}),
        RetrievedChunk("c", {"source_key": "only.pdf", "chapter": ""}),
    ]
    cites = citations_from_chunks(chunks)
    assert len(cites) == 2
    assert cites[1].title == "only.pdf"
    assert cites[1].page is None
    assert cites[1].chapter == ""


def test_get_lesson_outline_strategy_default() -> None:
    s = get_lesson_outline_strategy("default")
    assert s.build_messages is not None


def test_get_lesson_outline_strategy_lecture_scaffold_one_shot() -> None:
    s = get_lesson_outline_strategy("lecture_scaffold_one_shot")
    assert s.build_messages is not None


def test_lecture_scaffold_one_shot_injects_request_and_context() -> None:
    req = _outline_request()
    chunks = [
        RetrievedChunk(
            content="Sample passage for grounding.",
            metadata={"title": "Book A", "chapter": "6"},
        )
    ]
    messages = get_lesson_outline_strategy("lecture_scaffold_one_shot").build_messages(
        req, chunks
    )
    system = messages[0]["content"]
    assert req.learning_objective in system
    assert req.audience_level.value in system
    assert req.content_type.value in system
    assert "Sample passage for grounding." in system
    assert "### Passage [0]" in system
    assert "{learning_objective}" not in system


def test_get_lesson_outline_strategy_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unknown lesson outline style"):
        get_lesson_outline_strategy("nope")
