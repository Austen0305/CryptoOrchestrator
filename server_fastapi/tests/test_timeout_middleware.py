import asyncio
import os

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from server_fastapi.middleware.timeout_middleware import TimeoutMiddleware


@pytest.mark.asyncio
async def test_timeout_triggers():
    # Short timeout to trigger 504
    os.environ["REQUEST_TIMEOUT"] = "1"
    app = FastAPI()
    app.add_middleware(TimeoutMiddleware, timeout_seconds=1)

    @app.get("/sleep")
    async def sleep_route():
        await asyncio.sleep(2)
        return {"ok": True}

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.get("/sleep", timeout=10)
        assert resp.status_code == 504
        data = resp.json()
        assert data.get("timeout_seconds") == 1


@pytest.mark.asyncio
async def test_fast_request_ok():
    os.environ["REQUEST_TIMEOUT"] = "5"
    app = FastAPI()
    app.add_middleware(TimeoutMiddleware, timeout_seconds=5)

    @app.get("/fast")
    async def fast_route():
        return {"ok": True}

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.get("/fast")
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}
