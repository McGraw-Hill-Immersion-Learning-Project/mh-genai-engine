"""Generate check endpoint."""

from fastapi import APIRouter

generate_router = APIRouter(tags=["generate"])


@generate_router.post("/generate/lesson-outline")
def generate_Outline(chapter: str, 
                     learningObjectivs: list[str]=[],
                     audience: str=None,
                     tone: str=None,
                     timeAllowed: str=None,
                     externalResources: bool=False) -> dict[str, str | list[str]]:
    """Return 200 with status ok. No auth or env-dependent logic."""
    return {"outline": "example outline",
            "keyConcepts": ["concept 1", "concept 2"],
            "misconceptions": ["misconception 1", "misconception 2"],
            "checksForUnderstanding": ["check 1", "check 2"],
            "ActivityIdeas": ["Activity 1", "Activity 2"],
            "slideOutline": "Example Outline",
            "misconceptions": ["misconception 1", "misconception 2"],
            "citations" : [
                            "chapter 1",
                            "section 1",
                            "chunk 1",
                            "example excerpt"
                          ]
            }

@generate_router.post("/generate/assessment-transform")
def generate_Assessment(question: str,
                        options: list[str]=[],
                        items: list[str]=[],
                        learningObjectives: list[str]=[],
                        ) -> dict[str, str | list[str]]:
    """Return 200 with status ok. No auth or env-dependent logic."""
    return {"openEndedQuestion": "What color is blue?",
            "rubric": "Blue",
            "expectedResponseOutline": "This is why",
            "misconceptions" : [
                            "misconception 1",
                            "misconception 2"
                          ],
            "citations" : [
                            "chapter 1",
                            "section 1",
                            "chunk 1",
                            "example excerpt"
                          ]
            }