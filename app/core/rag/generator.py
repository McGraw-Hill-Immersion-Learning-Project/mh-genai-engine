"""Send context + query to LLM provider and return structured lesson outline."""

from __future__ import annotations

import json
import re

from pydantic import ValidationError

from app.models.generate import (
    Citation,
    ContentType,
    LessonOutlineGeneratedBody,
    LessonOutlineRegenerateRequest,
    LessonOutlineRequest,
    LessonOutlineResponse,
)
from app.db.vector.ids import chunk_document_id
from app.providers.llm.base import LLMProvider

from app.core.rag.prompts.base import (
    LessonOutlinePromptStrategy,
    LessonOutlineRefinementPromptStrategy,
)
from app.core.rag.retriever import RetrievedChunk
from app.utils import get_logger

logger = get_logger(__name__)


def _preview_text(text: str, *, head: int = 2500, tail: int = 2500) -> str:
    """Log-friendly slice when *text* is long (shows start + end)."""
    if len(text) <= head + tail + 80:
        return text
    return (
        f"{text[:head]}\n... [{len(text)} chars total, middle omitted] ...\n{text[-tail:]}"
    )


def _snippet_at_index(text: str, index: int | None, *, radius: int = 120) -> str:
    """Extract *text* around *index* for JSON error debugging."""
    if index is None or index < 0 or not text:
        return ""
    lo = max(0, index - radius)
    hi = min(len(text), index + radius)
    snippet = text[lo:hi]
    marker_pos = index - lo
    pointer = " " * max(0, marker_pos) + "^"
    return f"snippet around pos {index} (lo={lo} hi={hi}):\n{snippet}\n{pointer}"


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


def _repair_unescaped_blockquote_dialogue_quotes(text: str) -> str:
    """Escape ``"`` that opens dialogue after Markdown blockquotes (common LLM mistake).

    Models often emit ``> "Imagine ...`` inside a JSON string; the bare ``"`` ends the
    JSON string early. A backslash before that quote restores valid JSON.
    """
    return re.sub(
        r'(>\s+)"([A-Za-z0-9])',
        lambda m: m.group(1) + '\\"' + m.group(2),
        text,
    )


def parse_lesson_outline_llm_json(raw: str) -> LessonOutlineGeneratedBody:
    """Parse model output into the body-only schema (strips ``citations`` if present)."""
    text = _strip_json_fence(raw)
    first_err: json.JSONDecodeError | None = None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        first_err = e
        repaired = _repair_unescaped_blockquote_dialogue_quotes(text)
        if repaired != text:
            try:
                data = json.loads(repaired)
            except json.JSONDecodeError:
                data = None
            else:
                logger.info(
                    "lesson_outline_llm_json_repaired_unescaped_blockquote_dialogue_quotes"
                )
        else:
            data = None

    if not isinstance(data, dict):
        assert first_err is not None
        pos = getattr(first_err, "pos", None)
        logger.warning(
            "lesson_outline_llm_json_decode_failed: %s\n%s\nraw_after_fence_preview:\n%s",
            first_err,
            _snippet_at_index(text, pos),
            _preview_text(text, head=1800, tail=1800),
        )
        raise ValueError(f"LLM output is not valid JSON: {first_err}") from first_err
    if not isinstance(data, dict):
        raise ValueError("LLM JSON root must be an object")
    data.pop("citations", None)
    try:
        return LessonOutlineGeneratedBody.model_validate(data)
    except ValidationError as e:
        logger.warning(
            "lesson_outline_llm_json_schema_mismatch: %s keys_in_payload=%s",
            e,
            list(data.keys()) if isinstance(data, dict) else None,
        )
        raise ValueError(f"LLM JSON does not match expected schema: {e}") from e


def _bibliographic_fields(metadata: dict) -> tuple[str, str | None, str, str | None]:
    """title, page, chapter, section for API citations (from chunk metadata)."""
    m = metadata or {}
    title = str(m.get("title") or m.get("source_key") or "Source")
    page_num = m.get("page_number")
    page = str(page_num) if page_num is not None else None
    chapter = str(m.get("chapter") or "")
    sec = m.get("section")
    section = str(sec) if sec else None
    return (title, page, chapter, section)


def citations_from_chunks(chunks: list[RetrievedChunk]) -> list[Citation]:
    """One citation per chunk, same order as ``### Passage [i]`` / ``ref=\"i\"``."""
    out: list[Citation] = []
    for i, ch in enumerate(chunks):
        title, page, chapter, section = _bibliographic_fields(ch.metadata)
        out.append(
            Citation(
                chunk_id=chunk_document_id(ch.metadata, i),
                title=title,
                page=page,
                chapter=chapter,
                section=section,
                snippet=ch.content,
            )
        )
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
        for m in messages:
            logger.info(
                "lesson_outline_llm_message role=%s content_length=%d",
                m.get("role"),
                len(m.get("content") or ""),
            )
        joined = "\n".join(
            f"[{m.get('role')}]\n{m.get('content', '')}" for m in messages
        )
        logger.debug("lesson_outline_llm_messages_full:\n%s", joined)

        raw = await self._llm.complete(messages)
        logger.info("lesson_outline_llm_completion length=%d", len(raw))
        logger.debug("lesson_outline_llm_completion_raw:\n%s", raw)

        body = parse_lesson_outline_llm_json(raw)

        slide_outline = body.slide_outline
        if request.content_type != ContentType.PPT:
            slide_outline = None

        citations = citations_from_chunks(chunks)
        fields = body.model_dump(mode="python")
        fields["slide_outline"] = slide_outline
        return LessonOutlineResponse(**fields, citations=citations)

    async def regenerate(
        self,
        chunks: list[RetrievedChunk],
        request: LessonOutlineRegenerateRequest,
        refinement_strategy: LessonOutlineRefinementPromptStrategy,
    ) -> LessonOutlineResponse:
        """LLM refines ``request.previous_outline`` using the same JSON + citation contract as :meth:`generate`."""
        messages = refinement_strategy.build_messages(request, chunks)
        for m in messages:
            logger.info(
                "lesson_outline_refinement_llm_message role=%s content_length=%d",
                m.get("role"),
                len(m.get("content") or ""),
            )
        joined = "\n".join(
            f"[{m.get('role')}]\n{m.get('content', '')}" for m in messages
        )
        logger.debug("lesson_outline_refinement_llm_messages_full:\n%s", joined)

        raw = await self._llm.complete(messages)
        logger.info("lesson_outline_refinement_llm_completion length=%d", len(raw))
        logger.debug("lesson_outline_refinement_llm_completion_raw:\n%s", raw)

        body = parse_lesson_outline_llm_json(raw)

        slide_outline = body.slide_outline
        if request.resolved_content_type() != ContentType.PPT:
            slide_outline = None

        citations = citations_from_chunks(chunks)
        fields = body.model_dump(mode="python")
        fields["slide_outline"] = slide_outline
        return LessonOutlineResponse(**fields, citations=citations)
