import pytest
from fastapi.testclient import TestClient
from server_fastapi.main import app
import uuid


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Register and login a unique user, returning Authorization header."""
    unique_email = f"prefuser-{uuid.uuid4().hex[:8]}@example.com"
    register_data = {"email": unique_email, "password": "PrefPass123!", "name": "Pref User"}
    reg_resp = client.post("/api/auth/register", json=register_data)
    assert reg_resp.status_code == 200, reg_resp.text
    login_resp = client.post("/api/auth/login", json={"email": unique_email, "password": "PrefPass123!"})
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


class TestPreferencesRecommendations:
    def test_preferences_unauthorized(self, client):
        resp = client.get("/api/preferences/")
        assert resp.status_code == 403  # FastAPI returns 403 without valid token

    def test_recommendations_unauthorized(self, client):
        resp = client.get("/api/recommendations/")
        assert resp.status_code == 403  # FastAPI returns 403 without valid token

    def test_get_preferences_defaults(self, client, auth_headers):
        resp = client.get("/api/preferences/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["theme"] in ["light", "dark"]  # default light, but allow dark if changed
        assert "uiSettings" in data and "tradingSettings" in data and "notifications" in data
        assert isinstance(data["userId"], str) and data["userId"].isdigit()

    def test_update_theme(self, client, auth_headers):
        resp = client.patch("/api/preferences/theme", json={"theme": "dark"}, headers=auth_headers)
        assert resp.status_code == 200
        j = resp.json()
        assert j["theme"] == "dark"
        # Fetch again and ensure updated
        get_resp = client.get("/api/preferences/", headers=auth_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["theme"] == "dark"

    def test_get_recommendations(self, client, auth_headers):
        resp = client.get("/api/recommendations/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "topPairs" in data and len(data["topPairs"]) >= 1
        assert data["marketSentiment"] in ["bullish", "bearish", "neutral"]
        assert "optimalRiskSettings" in data
        # quick shape checks
        first = data["topPairs"][0]
        for key in ["symbol", "currentPrice", "confidence"]:
            assert key in first
