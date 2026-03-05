from fastapi import APIRouter
from app.schemas.template import Template, TemplateList

router = APIRouter()


@router.get("/templates", response_model=TemplateList)
def list_templates():
    return TemplateList(
        templates=[
            Template(
                id="lesson-outline",
                name="Lesson Outline",
                description="Generate a lesson outline grounded in OER content",
            ),
            Template(
                id="assessment-transform",
                name="Assessment Transform",
                description="Transform an MCQ into an open-ended question + rubric",
            ),
        ]
    )
