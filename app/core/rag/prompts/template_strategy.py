"""Lesson-outline prompt strategy: load a markdown template from disk, inject request + RAG context via ``str.format()``."""

from __future__ import annotations

from pathlib import Path

from app.models.generate import LessonOutlineRequest

from app.core.rag.retriever import RetrievedChunk

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def load_lesson_outline_template(filename: str) -> str:
    """Load a ``.format()``-compatible markdown template from ``templates/``."""
    return (_TEMPLATES_DIR / filename).read_text(encoding="utf-8")


def _load_default_template() -> str:
    """Template used when ``TemplatedLessonOutlineStrategy()`` is called with no ``template`` argument."""
    return load_lesson_outline_template("default_lesson_outline.md")


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
        system_content = self._template.format(
            learning_objective=request.learning_objective,
            audience_level=request.audience_level.value,
            content_type=request.content_type.value,
            chapter=request.chapter,
            section=request.section or "",
            sub_section=request.sub_section or "",
            book=request.book or "",
            count=str(request.count),
            retrieved_context=retrieved_context,
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
