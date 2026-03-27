"""Prompt strategies and registry for RAG generation."""

from app.core.rag.prompts.base import LessonOutlinePromptStrategy
from app.core.rag.prompts.template_strategy import (
    TemplatedLessonOutlineStrategy,
    load_format_rules_for_content_type,
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
    "load_format_rules_for_content_type",
    "get_lesson_outline_strategy",
    "get_lesson_outline_strategy_by_template_id",
    "lesson_outline_template_api_ids",
    "load_lesson_outline_template",
]
