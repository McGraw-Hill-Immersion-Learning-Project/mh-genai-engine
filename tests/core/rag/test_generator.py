"""Unit tests for Generator (mock LLM)."""

import json

import pytest

from app.models.generate import (
    AudienceLevel,
    ContentType,
    LessonOutlineGeneratedBody,
    LessonOutlineRegenerateRequest,
    LessonOutlineRequest,
)
from app.models.generate import CITATION_SNIPPET_MAX_LEN, Citation

from app.core.rag.generator import (
    Generator,
    citations_from_chunks,
    parse_lesson_outline_llm_json,
)
from app.core.rag.prompts.template_strategy import (
    TemplatedLessonOutlineRefinementStrategy,
    TemplatedLessonOutlineStrategy,
)
from app.core.rag.prompts.registry import (
    get_lesson_outline_strategy,
    get_lesson_outline_strategy_by_template_id,
)
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


def _regenerate_request(
    *,
    previous_slide_outline: str | None = None,
) -> LessonOutlineRegenerateRequest:
    return LessonOutlineRegenerateRequest(
        previous_outline=LessonOutlineGeneratedBody(
            outline="Prior outline section I–III.",
            slide_outline=previous_slide_outline,
        ),
        refinement_instructions="Expand the introduction.",
    )


@pytest.mark.asyncio
async def test_regenerate_uses_refinement_prompt_and_citations_from_chunks() -> None:
    llm = FakeLLMProvider()
    gen = Generator(llm, TemplatedLessonOutlineStrategy())
    refine = TemplatedLessonOutlineRefinementStrategy()
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
    resp = await gen.regenerate(chunks, _regenerate_request(), refine)

    assert resp.outline.startswith("I. Intro")
    assert len(resp.citations) == 1
    assert len(llm.calls) == 1
    messages = llm.calls[0]
    system = messages[0]["content"]
    assert "refining" in system.lower() and "existing lesson outline" in system.lower()
    assert "Surgical field edits" in system
    assert "Lesson scope" not in system
    assert "Prior outline section" in system
    assert "Expand the introduction" in system
    assert messages[1]["role"] == "user"
    assert "refinement" in messages[1]["content"].lower()


@pytest.mark.asyncio
async def test_regenerate_resolves_ppt_when_previous_has_slide_outline() -> None:
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
    refine = TemplatedLessonOutlineRefinementStrategy()
    resp = await gen.regenerate(
        [],
        _regenerate_request(previous_slide_outline="Slide 1: Old"),
        refine,
    )
    assert resp.slide_outline == "Slide 1: Title"


@pytest.mark.asyncio
async def test_generator_calls_llm_and_builds_citations_from_chunks() -> None:
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
    assert resp.citations[0].chunk_id == "ap.pdf_0"
    assert resp.citations[0].title == "Anatomy"
    assert resp.citations[0].page == "142"
    assert resp.citations[0].chapter == "6"
    assert resp.citations[0].section == "6.3"
    assert resp.citations[0].snippet == "Osteons form compact bone."
    assert len(resp.citations[0].snippet) <= CITATION_SNIPPET_MAX_LEN

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


def test_citations_from_chunks_one_per_chunk_preserves_order_and_snippets() -> None:
    chunks = [
        RetrievedChunk("a", {"title": "T", "page_number": 1, "chapter": "1", "chunk_id": 0}),
        RetrievedChunk("b", {"title": "T", "page_number": 1, "chapter": "1", "chunk_id": 1}),
        RetrievedChunk("c", {"source_key": "only.pdf", "chapter": "", "chunk_id": 2}),
    ]
    cites = citations_from_chunks(chunks)
    assert len(cites) == 3
    assert cites[0].chunk_id == "_0"
    assert cites[1].chunk_id == "_1"
    assert cites[2].chunk_id == "only.pdf_2"
    assert cites[0].snippet == "a" and cites[1].snippet == "b"
    assert cites[1].title == "T" and cites[1].page == "1"
    assert cites[2].title == "only.pdf"
    assert cites[2].page is None
    assert cites[2].chapter == ""
    assert cites[2].snippet == "c"


def test_citation_snippet_normalizes_pdf_noise_then_caps() -> None:
    raw = "PREDICTIONS\nOF\nSUPPL\x02\x03Y\nAND\nDEMAND\n" + "x" * 80
    c = Citation(chunk_id="t0", title="t", chapter="1", snippet=raw)
    assert len(c.snippet) == CITATION_SNIPPET_MAX_LEN
    assert c.snippet.startswith("PREDICTIONS OF SUPPLY")


def test_citations_from_chunks_truncates_long_snippet() -> None:
    long = "x" * 200
    cites = citations_from_chunks(
        [RetrievedChunk(long, {"title": "T", "chapter": "1"})]
    )
    assert len(cites) == 1
    assert len(cites[0].snippet) == CITATION_SNIPPET_MAX_LEN
    assert cites[0].snippet == "x" * CITATION_SNIPPET_MAX_LEN


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


def test_lecture_notes_prompt_includes_only_lecture_format_block() -> None:
    messages = TemplatedLessonOutlineStrategy().build_messages(_outline_request(), [])
    system = messages[0]["content"]
    assert "## Shared constraints" in system
    assert "## Format: `lecture_notes`" in system
    assert "## Format: `ppt`" not in system
    assert system.count("\n---\n") >= 1
    assert "instructional designer" in system.lower()


def test_ppt_prompt_includes_only_ppt_format_block() -> None:
    messages = TemplatedLessonOutlineStrategy().build_messages(
        _outline_request(content_type=ContentType.PPT), []
    )
    system = messages[0]["content"]
    assert "## Shared constraints" in system
    assert "## Format: `ppt`" in system
    assert "## Format: `lecture_notes`" not in system


def test_get_lesson_outline_strategy_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unknown lesson outline style"):
        get_lesson_outline_strategy("nope")


def test_get_lesson_outline_strategy_by_template_id_default() -> None:
    s = get_lesson_outline_strategy_by_template_id("default")
    assert s.build_messages is not None


def test_get_lesson_outline_strategy_by_template_id_lecture_scaffold() -> None:
    s = get_lesson_outline_strategy_by_template_id("lecture-scaffold-one-shot")
    assert s.build_messages is not None


def test_get_lesson_outline_strategy_by_template_id_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unknown lesson outline template"):
        get_lesson_outline_strategy_by_template_id("lecture_scaffold_one_shot")


def test_parse_lesson_outline_llm_json_repairs_blockquote_dialogue_quotes() -> None:
    """LLMs often emit ``> "Word`` inside JSON strings without escaping the quote."""
    raw = (
        '{"outline": "## Plan\\n\\n> '
        + '"'
        + 'Imagine <grounded ref=\\"0\\">x</grounded>", '
        '"keyConcepts": [], "misconceptions": [], '
        '"checksForUnderstanding": [], "activityIdeas": [], "slideOutline": null}'
    )
    body = parse_lesson_outline_llm_json(raw)
    assert "\n> \"Imagine" in body.outline
    assert '<grounded ref="0">x</grounded>' in body.outline


def test_parse_lesson_outline_llm_json_still_raises_when_unrepairable() -> None:
    raw = '{"outline": "not closed'
    with pytest.raises(ValueError, match="not valid JSON"):
        parse_lesson_outline_llm_json(raw)
