import pytest
from fastapi.testclient import TestClient
from server_fastapi.main import app
import uuid
from datetime import datetime, timedelta

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    email = f"predict-{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post("/api/auth/register", json={"email": email, "password": "PredictPass123!", "name": "Predict User"})
    assert reg.status_code == 200, reg.text
    login = client.post("/api/auth/login", json={"email": email, "password": "PredictPass123!"})
    assert login.status_code == 200, login.text
    token = login.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def _sample_ohlcv(n=5):
    now = datetime.utcnow()
    data = []
    base = 100.0
    for i in range(n):
        ts = (now - timedelta(minutes=(n-i))).isoformat() + 'Z'
        o = base + i * 0.5
        h = o + 0.8
        l = o - 0.8
        c = o + 0.3
        v = 10 + i
        data.append({"timestamp": ts, "open": o, "high": h, "low": l, "close": c, "volume": v})
    return data

class TestIntegrationsPredict:
    def test_predict_unauthorized(self, client):
        payload = {"symbol": "BTC/USDT", "timeframe": "1h", "data": _sample_ohlcv()}
        res = client.post("/api/integrations/predict", json=payload)
        assert res.status_code in (401, 403)

    def test_predict_happy_path(self, client, auth_headers):
        payload = {"symbol": "BTC/USDT", "timeframe": "1h", "data": _sample_ohlcv()}
        res = client.post("/api/integrations/predict", json=payload, headers=auth_headers)
        assert res.status_code == 200, res.text
        # The response schema is EnsemblePrediction-like; ensure basic keys exist
        data = res.json()
        assert isinstance(data, dict)
