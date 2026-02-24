"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Return 200 with status ok. No auth or env-dependent logic."""
    return {"status": "ok"}
