"""Pydantic schemas for /generate endpoints.

"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from app.core.rag.prompts.registry import lesson_outline_template_api_ids
from app.db.vector.filters import VectorMetadataFilter
from app.utils import normalize_citation_snippet_text

CITATION_SNIPPET_MAX_LEN = 50


class ContentType(str, Enum):
    LECTURE_NOTES = "lecture_notes"
    PPT = "ppt"


class AudienceLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Citation(BaseModel):
    """One row per retrieved chunk; ``citations[i]`` aligns with ``<grounded ref=\"i\">``."""

    chunk_id: str = Field(
        description="Vector store row id (source_key + '_' + chunk_id from ingestion metadata).",
    )
    title: str
    page: str | None = None
    chapter: str
    section: str | None = None
    snippet: str = Field(
        max_length=CITATION_SNIPPET_MAX_LEN,
        description=(
            f"Leading characters of the retrieved passage (capped at {CITATION_SNIPPET_MAX_LEN}; "
            "whitespace normalized, ASCII controls stripped; same index as ref for UI hints)."
        ),
    )

    @field_validator("snippet", mode="before")
    @classmethod
    def _normalize_and_cap_snippet(cls, v: object) -> str:
        if v is None:
            return ""
        s = normalize_citation_snippet_text(str(v))
        return s[:CITATION_SNIPPET_MAX_LEN]

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class LessonOutlineRequest(BaseModel):
    book: str | None = None
    chapter: str | None = None
    section: str | None = None
    sub_section: str | None = None
    learning_objective: str
    content_type: ContentType
    count: int
    audience_level: AudienceLevel
    regenerated_response: bool = False
    template: str = "default"

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    @field_validator("template")
    @classmethod
    def template_must_be_listed(cls, v: str) -> str:
        allowed = lesson_outline_template_api_ids()
        if v not in allowed:
            raise ValueError(
                f"Unknown template {v!r}; must match an id from GET /templates/lesson-outline "
                f"(allowed: {sorted(allowed)})"
            )
        return v


class LessonOutlineGeneratedBody(BaseModel):
    """Fields produced by the LLM as JSON (no citations — those come from retrieval)."""

    outline: str
    key_concepts: list[str] | None = None
    misconceptions: list[str] | None = None
    checks_for_understanding: list[str] | None = None
    activity_ideas: list[str] | None = None
    slide_outline: str | None = None

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class LessonOutlineResponse(LessonOutlineGeneratedBody):
    """API / pipeline response: generated body plus grounded citations."""

    citations: list[Citation] = []

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        by_alias=True,
    )


class LessonOutlineRegenerateRequest(BaseModel):
    """Request for ``POST /generate/lesson-outline/regenerate``.

    ``previous_outline`` and ``refinement_instructions`` are required. Optional
    ``chunk_ids`` selects passages by stable vector ids from a prior response;
    omit or send an empty list to use embedding retrieval with no metadata filters.
    """

    previous_outline: LessonOutlineGeneratedBody
    refinement_instructions: str
    chunk_ids: list[str] | None = None

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    def resolved_content_type(self) -> ContentType:
        """Output mode for format rules and ``slide_outline`` (from prior outline only)."""
        so = self.previous_outline.slide_outline
        if so is not None and str(so).strip():
            return ContentType.PPT
        return ContentType.LECTURE_NOTES


class AssessmentTransformRequest(BaseModel):
    question: str
    options: list[str] = []
    learning_objectives: list[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class AssessmentTransformResponse(BaseModel):
    open_ended_question: str
    rubric: str
    expected_response_outline: str
    misconceptions: list[str] = []
    citations: list[Citation] = []

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        by_alias=True,
    )
