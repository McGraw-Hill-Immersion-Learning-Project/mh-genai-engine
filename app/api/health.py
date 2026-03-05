"""Health check endpoint."""

from fastapi import APIRouter
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health():
    """Return 200 with status ok. No auth or env-dependent logic."""
    return HealthResponse(status="ok")
