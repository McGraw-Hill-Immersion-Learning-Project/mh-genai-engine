"""Protocol for lesson-outline prompt strategies.

Strategies build LLM message lists from the user request and retrieved chunks.

Contract (enforced by Generator, documented here for prompt authors):

- The model must return **strict JSON** with lesson-outline fields. Do **not** rely on
  the model for ``citations``; the Generator overwrites citations from chunk metadata.
- Use ``{{`` and ``}}`` in template files for literal braces (e.g. JSON examples).
- Dynamic retrieval is injected via a ``{retrieved_context}`` placeholder in the template (see ``app/core/rag/prompts/templates/*.md``).
- Passages are listed with 0-based indices; prompts may instruct the model to emit ``<grounded ref="N">…</grounded>`` where ``N`` matches the passage index for client-side styling / future citation links.
"""

from __future__ import annotations

from typing import Protocol

from app.models.generate import LessonOutlineRequest

from app.core.rag.retriever import RetrievedChunk


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
