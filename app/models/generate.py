"""Pydantic schemas for /generate endpoints.

"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from app.core.rag.prompts.registry import lesson_outline_template_api_ids


class ContentType(str, Enum):
    LECTURE_NOTES = "lecture_notes"
    PPT = "ppt"


class AudienceLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Citation(BaseModel):
    title: str
    page: str | None = None
    chapter: str
    section: str | None = None


class LessonOutlineRequest(BaseModel):
    book: str | None = None
    chapter: str
    section: str | None = None
    sub_section: Annotated[str | None, Field(alias="subSection")] = None
    learning_objective: Annotated[str, Field(alias="learningObjective")]
    content_type: Annotated[ContentType, Field(alias="contentType")]
    count: int
    audience_level: Annotated[AudienceLevel, Field(alias="audienceLevel")]
    regenerated_response: Annotated[bool, Field(alias="regeneratedResponse")] = False
    template: str = "default"

    model_config = {"populate_by_name": True}

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
    key_concepts: Annotated[list[str] | None, Field(alias="keyConcepts")] = None
    misconceptions: list[str] | None = None
    checks_for_understanding: Annotated[
        list[str] | None, Field(alias="checksForUnderstanding")
    ] = None
    activity_ideas: Annotated[list[str] | None, Field(alias="activityIdeas")] = None
    slide_outline: Annotated[str | None, Field(alias="slideOutline")] = None

    model_config = {"populate_by_name": True}


class LessonOutlineResponse(LessonOutlineGeneratedBody):
    """API / pipeline response: generated body plus grounded citations."""

    citations: list[Citation] = []

    model_config = {"populate_by_name": True, "by_alias": True}


class AssessmentTransformRequest(BaseModel):
    question: str
    options: list[str] = []
    learning_objectives: Annotated[
        list[str], Field(alias="learningObjectives")
    ] = []

    model_config = {"populate_by_name": True}


class AssessmentTransformResponse(BaseModel):
    open_ended_question: Annotated[str, Field(alias="openEndedQuestion")]
    rubric: str
    expected_response_outline: Annotated[
        str, Field(alias="expectedResponseOutline")
    ]
    misconceptions: list[str] = []
    citations: list[Citation] = []

    model_config = {"populate_by_name": True, "by_alias": True}
