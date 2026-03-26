"""Registry of lesson-outline prompt strategies by style id."""

from __future__ import annotations

from app.core.rag.prompts.base import LessonOutlinePromptStrategy
from app.core.rag.prompts.default_strategy import DefaultLessonOutlineStrategy

_REGISTRY: dict[str, LessonOutlinePromptStrategy] = {
    "default": DefaultLessonOutlineStrategy(),
}


def get_lesson_outline_strategy(style_id: str = "default") -> LessonOutlinePromptStrategy:
    """Return the strategy for *style_id*. Raises ValueError if unknown."""
    try:
        return _REGISTRY[style_id]
    except KeyError as e:
        raise ValueError(
            f"Unknown lesson outline style: {style_id!r}. "
            f"Known: {sorted(_REGISTRY)!r}"
        ) from e
