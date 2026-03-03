from pydantic import BaseModel
from typing import Optional


class TelemetryEvent(BaseModel):
    eventType: str
    latencyMs: Optional[float] = None
    timestamp: Optional[str] = None
