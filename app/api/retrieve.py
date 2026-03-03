from fastapi import APIRouter
from app.schemas.retrieve import (
    RetrieveRequest,
    RetrieveResponse,
    RetrievedChunk,
)

router = APIRouter()


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(request: RetrieveRequest):
    # Mock response matching OpenAPI contract
    return RetrieveResponse(
        chunks=[
            RetrievedChunk(
                text=f"Mock chunk for query: {request.query}",
                chapter=request.chapter or "Chapter 1",
                section="Section 1.1",
                score=0.92,
            )
        ]
    )
