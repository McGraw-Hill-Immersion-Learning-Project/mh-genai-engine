"""Protocol for lesson-outline prompt strategies.

Strategies build LLM message lists from the user request and retrieved chunks.

Contract (enforced by Generator, documented here for prompt authors):

- The model must return **strict JSON** with lesson-outline fields. Do **not** rely on
  the model for ``citations``; the Generator overwrites citations from chunk metadata.
- Use ``{{`` and ``}}`` in template files for literal braces (e.g. JSON examples).
- **One** of ``rules/format_lecture_notes.md`` or ``rules/format_ppt.md`` is injected first (chosen by ``content_type``); each file begins with the same **Shared constraints**, then mode-specific **Format** instructions. The task template (with retrieved context) follows after a separator.
- Dynamic retrieval is injected via a ``{retrieved_context}`` placeholder in the template (see ``app/core/rag/prompts/templates/*.md``).
- Passage indices are **0-based** in retrieval order: ``citations[N]`` matches ``### Passage [N]`` and valid ``<grounded ref="N">`` (one citation per chunk). ``citations[N].snippet`` is a **short preview** (50 characters max) of that passage for small payloads.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from app.core.rag.retriever import RetrievedChunk

if TYPE_CHECKING:
    from app.models.generate import LessonOutlineRequest


class LessonOutlinePromptStrategy(Protocol):
    """Build chat messages for lesson-outline generation."""

    def build_messages(
        self,
        request: LessonOutlineRequest,
        chunks: list[RetrievedChunk],
    ) -> list[dict[str, str]]:
        """Return chat turns for :meth:`app.providers.llm.base.LLMProvider.complete`.

        Same provider-agnostic contract: ``role`` and ``content`` strings per turn.
        """
        ...
