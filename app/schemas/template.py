from pydantic import BaseModel
from typing import List


class Template(BaseModel):
    id: str
    name: str
    description: str


class TemplateList(BaseModel):
    templates: List[Template]
