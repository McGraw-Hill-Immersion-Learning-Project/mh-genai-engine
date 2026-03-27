"""Request timeout middleware."""

import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.timeout import RequestTimeoutMiddleware


def test_middleware_allows_fast_response() -> None:
    app = FastAPI()

    @app.get("/ok")
    async def ok() -> dict[str, str]:
        return {"status": "ok"}

    app.add_middleware(RequestTimeoutMiddleware, timeout_seconds=5.0)
    with TestClient(app) as client:
        r = client.get("/ok")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_middleware_returns_504_when_handler_exceeds_limit() -> None:
    app = FastAPI()

    @app.get("/slow")
    async def slow() -> dict[str, str]:
        await asyncio.sleep(1.0)
        return {"status": "done"}

    app.add_middleware(RequestTimeoutMiddleware, timeout_seconds=0.05)
    with TestClient(app) as client:
        r = client.get("/slow")
    assert r.status_code == 504
    assert r.json() == {"detail": "Request timed out"}


def test_middleware_disabled_when_timeout_zero() -> None:
    app = FastAPI()

    @app.get("/slow")
    async def slow() -> dict[str, str]:
        await asyncio.sleep(0.02)
        return {"status": "done"}

    app.add_middleware(RequestTimeoutMiddleware, timeout_seconds=0.0)
    with TestClient(app) as client:
        r = client.get("/slow")
    assert r.status_code == 200
