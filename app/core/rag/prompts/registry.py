"""Registry of lesson-outline prompt strategies by style id."""

from __future__ import annotations

from app.core.rag.prompts.base import LessonOutlinePromptStrategy
from app.core.rag.prompts.template_strategy import (
    TemplatedLessonOutlineStrategy,
    load_lesson_outline_template,
)

# Research-backed template: subsection-aware lecture scaffold + one-shot JSON anchor
# (see templates/System Prompt 1.md).
_LECTURE_SCAFFOLD_ONE_SHOT = TemplatedLessonOutlineStrategy(
    template=load_lesson_outline_template("lecture_scaffold_one_shot.md"),
)

_REGISTRY: dict[str, LessonOutlinePromptStrategy] = {
    "default": TemplatedLessonOutlineStrategy(),
    "lecture_scaffold_one_shot": _LECTURE_SCAFFOLD_ONE_SHOT,
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
