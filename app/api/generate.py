"""Generate endpoints: lesson outline via RAG; assessment transform still mock."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from app.core.guardrails import guardrails
from app.core.rag.generator import Generator
from app.core.rag.pipeline import LessonOutlinePipeline
from app.core.rag.prompts.registry import get_lesson_outline_strategy_by_template_id
from app.core.rag.retriever import Retriever
from app.deps import get_llm, get_retriever
from app.models.generate import (
    AssessmentTransformRequest,
    AssessmentTransformResponse,
    Citation,
    LessonOutlineRequest,
    LessonOutlineResponse,
)
from app.providers.llm.base import LLMProvider

router = APIRouter(tags=["generate"])

_ASSESSMENT_MOCK_CITATIONS = [
    Citation(
        title="Anatomy & Physiology",
        page="142",
        chapter="6",
        section="6.3 Bone Structure",
        snippet="Mock assessment citation (not from retrieval).",
    ),
    Citation(
        title="Anatomy & Physiology",
        chapter="6",
        section="6.4 Bone Formation and Development",
        snippet="Mock assessment citation (not from retrieval).",
    ),
]


@router.post("/generate/lesson-outline")
async def generate_lesson_outline(
    body: LessonOutlineRequest,
    retriever: Annotated[Retriever, Depends(get_retriever)],
    llm: Annotated[LLMProvider, Depends(get_llm)],
) -> LessonOutlineResponse:
    """Retrieve grounded passages, then generate a structured lesson outline."""
    result = guardrails.check(body.learning_objective)
    if not result.allowed:
        raise HTTPException(status_code=400, detail=result.message)

    strategy = get_lesson_outline_strategy_by_template_id(body.template)
    pipeline = LessonOutlinePipeline(retriever, Generator(llm, strategy))
    try:
        return await pipeline.run(body)
    except ValueError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Lesson outline generation failed: {e}",
        ) from e


@router.post("/generate/assessment-transform")
def generate_assessment_transform(
    body: AssessmentTransformRequest,
) -> AssessmentTransformResponse:
    """Return a mock assessment transformation. Swap for real generation later."""
    return AssessmentTransformResponse(
        open_ended_question=(
            "Explain the functional relationship between osteoblasts and "
            "osteoclasts in bone remodeling. What happens at the cellular "
            "level when this balance is disrupted?"
        ),
        rubric=(
            "## Rubric (4-point scale)\n\n"
            "| Criterion | Excellent (4) | Proficient (3) | Developing (2) | Beginning (1) |\n"
            "|-----------|--------------|----------------|----------------|----------------|\n"
            "| Accuracy | Correctly describes both cell types and remodeling cycle | "
            "Minor inaccuracy in one area | Several inaccuracies | Fundamental misunderstanding |\n"
            "| Depth | Discusses cellular mechanisms and clinical implications | "
            "Addresses mechanisms but limited clinical connection | Surface-level explanation | "
            "Vague or off-topic |\n"
            "| Use of Evidence | Cites specific structures and processes | "
            "Some specific references | Generic statements | No supporting detail |"
        ),
        expected_response_outline=(
            "A strong response should: (1) define osteoblasts as bone-forming "
            "cells and osteoclasts as bone-resorbing cells; (2) describe the "
            "remodeling cycle as a coupled process; (3) explain that disruption "
            "(e.g., excessive osteoclast activity) leads to conditions like "
            "osteoporosis; (4) optionally reference hormonal regulation "
            "(PTH, calcitonin)."
        ),
        misconceptions=[
            "Bones stop changing after growth plates close",
            "Osteoblasts and osteoclasts perform the same function",
            "Osteoporosis is caused only by calcium deficiency",
        ],
        citations=_ASSESSMENT_MOCK_CITATIONS,
    )
