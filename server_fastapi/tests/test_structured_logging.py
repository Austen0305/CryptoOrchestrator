import json
import logging

import pytest
from fastapi import FastAPI, Request
from httpx import AsyncClient

from server_fastapi.middleware.request_id import RequestIDMiddleware
from server_fastapi.middleware.structured_logging import StructuredLoggingMiddleware
from server_fastapi.services.logging_config import StructuredFormatter


@pytest.mark.asyncio
async def test_structured_log_includes_request_id(caplog):
    caplog.set_level(logging.INFO)
    # Use an in-memory stream to capture formatted output
    import io

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(StructuredFormatter())
    root = logging.getLogger()
    # Temporarily replace handlers
    old_handlers = list(root.handlers)
    for h in old_handlers:
        root.removeHandler(h)
    root.addHandler(handler)

    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(StructuredLoggingMiddleware)

    @app.get("/logme")
    async def logme(request: Request):
        logging.getLogger("test").info("user-action", extra={"user_id": "u1"})
        return {"ok": True}

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.get("/logme")
        assert resp.status_code == 200

    # Flush handler and restore previous handlers
    handler.flush()
    output = stream.getvalue()
    root.removeHandler(handler)
    for h in old_handlers:
        root.addHandler(h)

    # Parse each line of output as JSON and assert request_id exists
    found = False
    for line in output.splitlines():
        try:
            parsed = json.loads(line)
            if "request_id" in parsed:
                found = True
                break
        except Exception:
            continue

    assert found, f"No structured log with request_id found in output: {output}"
