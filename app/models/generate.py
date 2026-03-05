"""Pydantic schemas for /generate endpoints.

"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


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
    sub_section: str | None = Field(None, alias="subSection")
    learning_objective: str = Field(..., alias="learningObjective")
    content_type: ContentType = Field(..., alias="contentType")
    count: int
    audience_level: AudienceLevel = Field(..., alias="audienceLevel")
    regenerated_response: bool = Field(False, alias="regeneratedResponse")

    model_config = {"populate_by_name": True}


class LessonOutlineResponse(BaseModel):
    outline: str
    key_concepts: list[str] | None = Field(None, alias="keyConcepts")
    misconceptions: list[str] | None = None
    checks_for_understanding: list[str] | None = Field(
        None, alias="checksForUnderstanding"
    )
    activity_ideas: list[str] | None = Field(None, alias="activityIdeas")
    slide_outline: str | None = Field(None, alias="slideOutline")
    citations: list[Citation] = []

    model_config = {"populate_by_name": True, "by_alias": True}


class AssessmentTransformRequest(BaseModel):
    question: str
    options: list[str] = []
    learning_objectives: list[str] = Field([], alias="learningObjectives")

    model_config = {"populate_by_name": True}


class AssessmentTransformResponse(BaseModel):
    open_ended_question: str = Field(..., alias="openEndedQuestion")
    rubric: str
    expected_response_outline: str = Field(..., alias="expectedResponseOutline")
    misconceptions: list[str] = []
    citations: list[Citation] = []

    model_config = {"populate_by_name": True, "by_alias": True}
