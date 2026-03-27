"""Optional metadata constraints for vector search (AND semantics)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VectorMetadataFilter:
    """All set fields must match chunk JSON metadata (string comparisons).

    - *chapter*, *section*: exact match on ``metadata->>'chapter'`` / ``section``.
    - *sub_section*: stored ``section`` must start with this string (prefix), e.g.
      TOC section label ``6.3.1 Intro`` matches ``sub_section="6.3.1"``.
    - *book*: substring match, case-insensitive, against ``metadata->>'title'``
      **or** ``metadata->>'source_key'`` (so ingestion keys like ``eepsam.pdf`` work when
      PDF title metadata is empty).
    """

    chapter: str | None = None
    section: str | None = None
    sub_section: str | None = None
    book: str | None = None

    def has_any(self) -> bool:
        return any(
            x is not None and str(x).strip() != ""
            for x in (self.chapter, self.section, self.sub_section, self.book)
        )
