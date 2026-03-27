from typing import Literal

from fastapi import APIRouter

from app.core.rag.prompts.registry import iter_template_catalog
from app.schemas.template import Template, TemplateList

router = APIRouter()

TemplateWorkflowSlug = Literal["lesson-outline", "assessment-transform"]


@router.get("/templates/{workflow}", response_model=TemplateList)
def list_templates(workflow: TemplateWorkflowSlug) -> TemplateList:
    """List Engine-approved templates for one workflow (kebab-case template ``id`` values)."""
    rows = iter_template_catalog(workflow)
    return TemplateList(
        templates=[
            Template(id=e.api_id, name=e.name, description=e.description) for e in rows
        ]
    )
