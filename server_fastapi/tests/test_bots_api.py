import pytest
from fastapi.testclient import TestClient
from server_fastapi.main import app
import uuid

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    email = f"bots-{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post("/api/auth/register", json={"email": email, "password": "BotsPass123!", "name": "Bots User"})
    assert reg.status_code == 200, reg.text
    login = client.post("/api/auth/login", json={"email": email, "password": "BotsPass123!"})
    assert login.status_code == 200, login.text
    token = login.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}

class TestBotsAPI:
    def test_bots_unauthorized(self, client):
        res = client.get("/api/bots/")
        assert res.status_code in (401, 403)

    def test_bots_list_authenticated(self, client, auth_headers):
        res = client.get("/api/bots/", headers=auth_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)
