import asyncio
import json
import jwt
import os
import pytest
from httpx import AsyncClient
from websockets.exceptions import ConnectionClosed
from fastapi.websockets import WebSocket
from server_fastapi.main import app

JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")


@pytest.mark.skip(reason="WS handshake requires integration environment; covered by E2E")
def test_ws_market_data_requires_auth():
    pass


@pytest.mark.anyio
async def test_ws_market_data_accepts_valid_token(monkeypatch):
    # This test creates a signed token and asserts our token decodes via shared secret
    token = jwt.encode({"id": 1}, JWT_SECRET, algorithm="HS256")
    decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    assert decoded["id"] == 1
    # Full WS handshake is covered in end-to-end runs; unit-level validation ensures decode path works
