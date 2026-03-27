"""Bound total request handling time (all HTTP endpoints)."""

from __future__ import annotations

import asyncio

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    """Cancel the request handler if it does not finish within *timeout_seconds*."""

    def __init__(self, app, timeout_seconds: float) -> None:
        super().__init__(app)
        self._timeout_seconds = timeout_seconds

    async def dispatch(self, request: Request, call_next) -> Response:
        if self._timeout_seconds <= 0:
            return await call_next(request)
        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=self._timeout_seconds,
            )
        except TimeoutError:
            return JSONResponse(
                status_code=504,
                content={"detail": "Request timed out"},
            )
