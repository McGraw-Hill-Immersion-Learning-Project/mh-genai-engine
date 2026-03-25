"""Send context + query to LLM provider and return structured lesson outline."""

from __future__ import annotations

import json
import re

from pydantic import ValidationError

from app.models.generate import (
    Citation,
    ContentType,
    LessonOutlineGeneratedBody,
    LessonOutlineRequest,
    LessonOutlineResponse,
)
from app.providers.llm.base import LLMProvider

from app.core.rag.prompts.base import LessonOutlinePromptStrategy
from app.core.rag.retriever import RetrievedChunk


def _strip_json_fence(text: str) -> str:
    stripped = text.strip()
    m = re.match(
        r"^```(?:json)?\s*\n?(.*?)\n?```\s*$",
        stripped,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    return stripped


def parse_lesson_outline_llm_json(raw: str) -> LessonOutlineGeneratedBody:
    """Parse model output into the body-only schema (strips ``citations`` if present)."""
    text = _strip_json_fence(raw)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM output is not valid JSON: {e}") from e
    if not isinstance(data, dict):
        raise ValueError("LLM JSON root must be an object")
    data.pop("citations", None)
    try:
        return LessonOutlineGeneratedBody.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"LLM JSON does not match expected schema: {e}") from e


def citations_from_chunks(chunks: list[RetrievedChunk]) -> list[Citation]:
    """Build grounded citations from chunk metadata; de-duplicate by location keys."""
    seen: set[tuple[str, str | None, str, str | None]] = set()
    out: list[Citation] = []
    for ch in chunks:
        m = ch.metadata
        title = str(m.get("title") or m.get("source_key") or "Source")
        page_num = m.get("page_number")
        page = str(page_num) if page_num is not None else None
        chapter = str(m.get("chapter") or "")
        sec = m.get("section")
        section = str(sec) if sec else None
        key = (title, page, chapter, section)
        if key in seen:
            continue
        seen.add(key)
        out.append(Citation(title=title, page=page, chapter=chapter, section=section))
    return out


class Generator:
    """Call the LLM with a prompt strategy and assemble a LessonOutlineResponse."""

    def __init__(
        self,
        llm: LLMProvider,
        prompt_strategy: LessonOutlinePromptStrategy,
    ) -> None:
        self._llm = llm
        self._prompt_strategy = prompt_strategy

    async def generate(
        self,
        chunks: list[RetrievedChunk],
        request: LessonOutlineRequest,
    ) -> LessonOutlineResponse:
        messages = self._prompt_strategy.build_messages(request, chunks)
        raw = await self._llm.complete(messages)
        body = parse_lesson_outline_llm_json(raw)

        slide_outline = body.slide_outline
        if request.content_type != ContentType.PPT:
            slide_outline = None

        citations = citations_from_chunks(chunks)
        fields = body.model_dump(mode="python")
        fields["slide_outline"] = slide_outline
        return LessonOutlineResponse(**fields, citations=citations)
