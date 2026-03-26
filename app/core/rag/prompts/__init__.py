"""Prompt strategies and registry for RAG generation."""

from app.core.rag.prompts.base import LessonOutlinePromptStrategy
from app.core.rag.prompts.template_strategy import (
    TemplatedLessonOutlineStrategy,
    load_lesson_outline_template,
)
from app.core.rag.prompts.registry import (
    get_lesson_outline_strategy,
    get_lesson_outline_strategy_by_template_id,
    lesson_outline_template_api_ids,
)

__all__ = [
    "LessonOutlinePromptStrategy",
    "TemplatedLessonOutlineStrategy",
    "get_lesson_outline_strategy",
    "get_lesson_outline_strategy_by_template_id",
    "lesson_outline_template_api_ids",
    "load_lesson_outline_template",
]
