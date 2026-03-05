"""Generate endpoints - mock handlers returning hardcoded JSON.

Responses match the schemas defined in docs/api/openapi.yaml (v0.2.0).
Replace mock data with real RAG pipeline calls when providers are built.
"""

from fastapi import APIRouter

from app.models.generate import (
    AssessmentTransformRequest,
    AssessmentTransformResponse,
    Citation,
    LessonOutlineRequest,
    LessonOutlineResponse,
)

generate_router = APIRouter(tags=["generate"])

_MOCK_CITATIONS = [
    Citation(
        title="Anatomy & Physiology",
        page="142",
        chapter="6",
        section="6.3 Bone Structure",
    ),
    Citation(
        title="Anatomy & Physiology",
        chapter="6",
        section="6.4 Bone Formation and Development",
    ),
]


@generate_router.post("/generate/lesson-outline")
def generate_lesson_outline(
    body: LessonOutlineRequest,
) -> LessonOutlineResponse:
    """Return a mock lesson outline. Swap for real generation later."""
    return LessonOutlineResponse(
        outline=(
            "I. Introduction to Bone Structure (5 min)\n"
            "   - Overview of skeletal system functions\n"
            "   - Types of bone tissue\n"
            "II. Compact vs. Spongy Bone (15 min)\n"
            "   - Osteon structure and haversian systems\n"
            "   - Trabecular architecture\n"
            "III. Bone Cells and Remodeling (15 min)\n"
            "   - Osteoblasts, osteoclasts, osteocytes\n"
            "   - Remodeling cycle\n"
            "IV. Clinical Connections & Wrap-up (10 min)\n"
            "   - Osteoporosis as a remodeling imbalance\n"
            "   - Review questions"
        ),
        keyConcepts=[
            "Compact bone vs. spongy bone architecture",
            "Osteon as the structural unit of compact bone",
            "Bone remodeling cycle: osteoblast and osteoclast roles",
        ],
        misconceptions=[
            "Bones are static, non-living structures",
            "Spongy bone is weaker and less important than compact bone",
        ],
        checksForUnderstanding=[
            "Compare and contrast the structure of compact and spongy bone.",
            "Explain how osteoblasts and osteoclasts maintain bone homeostasis.",
        ],
        activityIdeas=[
            "5-min think-pair-share: predict what happens when osteoclast activity exceeds osteoblast activity",
            "Label a diagram of an osteon with key structures",
        ],
        slideOutline=(
            "Slide 1: Title — Bone Structure & Remodeling\n"
            "Slide 2: Learning Objective\n"
            "Slide 3: Compact vs. Spongy Bone (diagram)\n"
            "Slide 4: The Osteon — Labeled Cross-Section\n"
            "Slide 5: Bone Cells Overview\n"
            "Slide 6: Remodeling Cycle\n"
            "Slide 7: Clinical Connection — Osteoporosis\n"
            "Slide 8: Review Questions"
        )
        if body.content_type.value == "ppt"
        else None,
        citations=_MOCK_CITATIONS,
    )


@generate_router.post("/generate/assessment-transform")
def generate_assessment_transform(
    body: AssessmentTransformRequest,
) -> AssessmentTransformResponse:
    """Return a mock assessment transformation. Swap for real generation later."""
    return AssessmentTransformResponse(
        openEndedQuestion=(
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
        expectedResponseOutline=(
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
        citations=_MOCK_CITATIONS,
    )