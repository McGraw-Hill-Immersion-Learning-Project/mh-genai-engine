from fastapi import APIRouter, Response
from app.schemas.telemetry import TelemetryEvent

router = APIRouter()


@router.post("/telemetry/log", status_code=204)
def log_telemetry(event: TelemetryEvent):
    # Mock logging
    return Response(status_code=204)
