"""Prompt strategies and registry for RAG generation."""

from app.core.rag.prompts.base import LessonOutlinePromptStrategy
from app.core.rag.prompts.default_strategy import DefaultLessonOutlineStrategy
from app.core.rag.prompts.registry import get_lesson_outline_strategy

__all__ = [
    "DefaultLessonOutlineStrategy",
    "LessonOutlinePromptStrategy",
    "get_lesson_outline_strategy",
]
