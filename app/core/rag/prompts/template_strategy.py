"""Lesson-outline prompt strategy: load a markdown template from disk, inject request + RAG context via ``str.format()``."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from app.core.rag.retriever import RetrievedChunk

if TYPE_CHECKING:
    from app.models.generate import LessonOutlineRegenerateRequest, LessonOutlineRequest

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
_RULES_DIR = Path(__file__).resolve().parent / "rules"
_FORMAT_LECTURE_NOTES_PATH = _RULES_DIR / "format_lecture_notes.md"
_FORMAT_PPT_PATH = _RULES_DIR / "format_ppt.md"


@lru_cache(maxsize=1)
def _load_format_rules_lecture_notes() -> str:
    return _FORMAT_LECTURE_NOTES_PATH.read_text(encoding="utf-8").strip()


@lru_cache(maxsize=1)
def _load_format_rules_ppt() -> str:
    return _FORMAT_PPT_PATH.read_text(encoding="utf-8").strip()


def load_format_rules_for_content_type(content_type: str) -> str:
    """Format rules for the active output mode only (smaller prompt than both at once).

    *content_type* is the request enum value: ``lecture_notes`` or ``ppt``.
    """
    if content_type == "ppt":
        return _load_format_rules_ppt()
    return _load_format_rules_lecture_notes()


def load_lesson_outline_template(filename: str) -> str:
    """Load a ``.format()``-compatible markdown template from ``templates/``."""
    return (_TEMPLATES_DIR / filename).read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _load_default_template() -> str:
    """Template used when ``TemplatedLessonOutlineStrategy()`` is called with no ``template`` argument."""
    return load_lesson_outline_template("default_lesson_outline.md")


@lru_cache(maxsize=1)
def _load_refinement_template() -> str:
    return load_lesson_outline_template("refine_lesson_outline.md")


def _expand_placeholders(template: str, parts: dict[str, str]) -> str:
    """Substitute ``{key}`` without ``str.format`` (safe when values contain ``{`` / ``}``, e.g. JSON)."""
    out = template
    for key in sorted(parts.keys(), key=len, reverse=True):
        out = out.replace("{" + key + "}", parts[key])
    return out


def _format_retrieved_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "(No passages retrieved. Say so briefly in the outline and keep claims generic.)"
    parts: list[str] = []
    for i, ch in enumerate(chunks):
        meta = ch.metadata
        title = meta.get("title") or ""
        src = meta.get("source_key") or ""
        page = meta.get("page_number")
        chapter = meta.get("chapter") or ""
        section = meta.get("section") or ""
        header = f"### Passage [{i}]"
        if title or src:
            header += f" — {title or src}"
        loc = []
        if page is not None:
            loc.append(f"page {page}")
        if chapter:
            loc.append(f"chapter: {chapter}")
        if section:
            loc.append(f"section: {section}")
        if loc:
            header += f" ({', '.join(loc)})"
        parts.append(f"{header}\n{ch.content.strip()}")
    return "\n\n".join(parts)


class TemplatedLessonOutlineStrategy:
    """Build one system turn from a format-string template plus retrieved passages."""

    def __init__(self, template: str | None = None) -> None:
        self._template = template if template is not None else _load_default_template()

    def build_messages(
        self,
        request: LessonOutlineRequest,
        chunks: list[RetrievedChunk],
    ) -> list[dict[str, str]]:
        retrieved_context = _format_retrieved_context(chunks)
        task_body = self._template.format(
            learning_objective=request.learning_objective,
            audience_level=request.audience_level.value,
            content_type=request.content_type.value,
            chapter=request.chapter or "",
            section=request.section or "",
            sub_section=request.sub_section or "",
            book=request.book or "",
            count=str(request.count),
            retrieved_context=retrieved_context,
        )
        system_content = "\n\n---\n\n".join(
            (
                load_format_rules_for_content_type(request.content_type.value),
                task_body,
            )
        )
        return [
            {"role": "system", "content": system_content},
            {
                "role": "user",
                "content": (
                    "Produce the JSON object now for the lesson outline "
                    "per the system instructions."
                ),
            },
        ]


class TemplatedLessonOutlineRefinementStrategy:
    """System prompt for **editing** a prior outline; same format rules + fresh retrieval context."""

    def __init__(self, template: str | None = None) -> None:
        self._template = template if template is not None else _load_refinement_template()

    def build_messages(
        self,
        request: LessonOutlineRegenerateRequest,
        chunks: list[RetrievedChunk],
    ) -> list[dict[str, str]]:
        retrieved_context = _format_retrieved_context(chunks)
        previous_json = json.dumps(
            request.previous_outline.model_dump(mode="json", by_alias=True),
            ensure_ascii=False,
            indent=2,
        )
        task_body = _expand_placeholders(
            self._template,
            {
                "retrieved_context": retrieved_context,
                "previous_outline_json": previous_json,
                "refinement_instructions": request.refinement_instructions,
            },
        )
        ct = request.resolved_content_type().value
        system_content = "\n\n---\n\n".join(
            (
                load_format_rules_for_content_type(ct),
                task_body,
            )
        )
        return [
            {"role": "system", "content": system_content},
            {
                "role": "user",
                "content": (
                    "Apply the refinement instructions and return the updated JSON object "
                    "per the system instructions."
                ),
            },
        ]
