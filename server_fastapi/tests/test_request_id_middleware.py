import pytest
from fastapi import FastAPI, Request
from httpx import AsyncClient

from server_fastapi.middleware.request_id import RequestIDMiddleware


@pytest.mark.asyncio
async def test_request_id_header_present():
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/check")
    async def check(request: Request):
        rid = getattr(request.state, "request_id", None)
        return {"request_id_in_state": rid}

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.get("/check")
        assert resp.status_code == 200
        assert "X-Request-ID" in resp.headers
        body = resp.json()
        assert body["request_id_in_state"] == resp.headers["X-Request-ID"]


@pytest.mark.asyncio
async def test_client_provided_request_id_preserved():
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/check2")
    async def check2(request: Request):
        return {"rid": request.state.request_id}

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.get("/check2", headers={"X-Request-ID": "my-custom-id"})
        assert resp.status_code == 200
        assert resp.headers.get("X-Request-ID") == "my-custom-id"
        assert resp.json()["rid"] == "my-custom-id"
