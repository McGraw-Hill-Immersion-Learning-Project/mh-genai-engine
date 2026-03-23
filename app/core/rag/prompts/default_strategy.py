"""Default lesson-outline prompt: load template from disk, inject context via .format()."""

from __future__ import annotations

from pathlib import Path

from app.models.generate import LessonOutlineRequest

from app.core.rag.retriever import RetrievedChunk


def _load_template() -> str:
    path = Path(__file__).resolve().parent / "default_lesson_outline.md"
    return path.read_text(encoding="utf-8")


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


class DefaultLessonOutlineStrategy:
    """Single system message: instructions + formatted request + retrieved context."""

    def __init__(self, template: str | None = None) -> None:
        self._template = template if template is not None else _load_template()

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
