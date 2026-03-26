"""Single source of truth for prompt templates: API ids, workflows, and strategies."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.rag.prompts.base import LessonOutlinePromptStrategy
from app.core.rag.prompts.template_strategy import (
    TemplatedLessonOutlineStrategy,
    load_lesson_outline_template,
)

WORKFLOW_LESSON_OUTLINE = "lesson-outline"
WORKFLOW_ASSESSMENT_TRANSFORM = "assessment-transform"

WORKFLOW_SLUGS: tuple[str, ...] = (
    WORKFLOW_LESSON_OUTLINE,
    WORKFLOW_ASSESSMENT_TRANSFORM,
)

# Kebab-case API template id -> internal strategy registry key (lesson outline only).
_LESSON_OUTLINE_API_TO_INTERNAL: dict[str, str] = {
    "default": "default",
    "lecture-scaffold-one-shot": "lecture_scaffold_one_shot",
}

_LECTURE_SCAFFOLD_ONE_SHOT = TemplatedLessonOutlineStrategy(
    template=load_lesson_outline_template("lecture_scaffold_one_shot.md"),
)

_INTERNAL_STRATEGIES: dict[str, LessonOutlinePromptStrategy] = {
    "default": TemplatedLessonOutlineStrategy(),
    "lecture_scaffold_one_shot": _LECTURE_SCAFFOLD_ONE_SHOT,
}


@dataclass(frozen=True, slots=True)
class TemplateCatalogEntry:
    """One row returned by ``GET /templates/{workflow}`` (plus strategy linkage for lesson outline)."""

    workflow: str
    api_id: str
    name: str
    description: str


# Order is stable API surface for the dashboard.
_TEMPLATE_CATALOG: tuple[TemplateCatalogEntry, ...] = (
    TemplateCatalogEntry(
        workflow=WORKFLOW_LESSON_OUTLINE,
        api_id="default",
        name="Lesson outline (default)",
        description="Generate a lesson outline grounded in OER content using the default prompt.",
    ),
    TemplateCatalogEntry(
        workflow=WORKFLOW_LESSON_OUTLINE,
        api_id="lecture-scaffold-one-shot",
        name="Lecture scaffold (one-shot)",
        description=(
            "Subsection-aware lecture scaffold with a one-shot JSON anchor; "
            "same placeholders and JSON contract as the default template."
        ),
    ),
    TemplateCatalogEntry(
        workflow=WORKFLOW_ASSESSMENT_TRANSFORM,
        api_id="default",
        name="Assessment transform",
        description=(
            "Transform an MCQ into an open-ended question and rubric. "
            "Workflow 2 is a placeholder; template id is reserved for future prompt variants."
        ),
    ),
)


def _assert_catalog_consistent() -> None:
    lesson_rows = [e for e in _TEMPLATE_CATALOG if e.workflow == WORKFLOW_LESSON_OUTLINE]
    assert {e.api_id for e in lesson_rows} == set(_LESSON_OUTLINE_API_TO_INTERNAL)
    for e in lesson_rows:
        key = _LESSON_OUTLINE_API_TO_INTERNAL[e.api_id]
        assert key in _INTERNAL_STRATEGIES


_assert_catalog_consistent()


def iter_template_catalog(workflow_slug: str) -> tuple[TemplateCatalogEntry, ...]:
    """Catalog entries for *workflow_slug* (``WORKFLOW_*`` constants)."""
    return tuple[TemplateCatalogEntry, ...](e for e in _TEMPLATE_CATALOG if e.workflow == workflow_slug)


def lesson_outline_template_api_ids() -> frozenset[str]:
    """Valid ``LessonOutlineRequest.template`` values (kebab-case)."""
    return frozenset[str](_LESSON_OUTLINE_API_TO_INTERNAL)


def get_lesson_outline_strategy(internal_style_id: str = "default") -> LessonOutlinePromptStrategy:
    """Return the strategy for an *internal* registry key (e.g. ``lecture_scaffold_one_shot``)."""
    try:
        return _INTERNAL_STRATEGIES[internal_style_id]
    except KeyError as e:
        raise ValueError(
            f"Unknown lesson outline style: {internal_style_id!r}. "
            f"Known: {sorted(_INTERNAL_STRATEGIES)!r}"
        ) from e


def get_lesson_outline_strategy_by_template_id(api_template_id: str) -> LessonOutlinePromptStrategy:
    """Map a kebab-case template id from ``GET /templates/lesson-outline`` to a strategy."""
    try:
        internal = _LESSON_OUTLINE_API_TO_INTERNAL[api_template_id]
    except KeyError as e:
        allowed = sorted(lesson_outline_template_api_ids())
        raise ValueError(
            f"Unknown lesson outline template: {api_template_id!r}. Known: {allowed!r}"
        ) from e
    return get_lesson_outline_strategy(internal)
