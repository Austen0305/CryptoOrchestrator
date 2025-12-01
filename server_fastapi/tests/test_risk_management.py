from fastapi.testclient import TestClient
from server_fastapi.main import app

client = TestClient(app)


def test_get_metrics():
    resp = client.get("/api/risk-management/metrics")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    # required keys
    for key in [
        "portfolioRisk",
        "maxDrawdown",
        "var95",
        "var99",
        "sharpeRatio",
        "correlationScore",
        "diversificationRatio",
        "exposureByAsset",
        "leverageRisk",
        "liquidityRisk",
        "concentrationRisk",
    ]:
        assert key in data


def test_get_alerts_and_acknowledge():
    resp = client.get("/api/risk-management/alerts")
    assert resp.status_code == 200
    alerts = resp.json()
    assert isinstance(alerts, list)
    if alerts:
        alert_id = alerts[0]["id"]
        ack = client.post(f"/api/risk-management/alerts/{alert_id}/acknowledge")
        assert ack.status_code == 200
        assert ack.json()["acknowledged"] is True


def test_limits_roundtrip_and_validation():
    # get defaults
    resp = client.get("/api/risk-management/limits")
    assert resp.status_code == 200
    limits = resp.json()
    # update within range
    upd = client.post("/api/risk-management/limits", json={"maxPositionSize": 20})
    assert upd.status_code == 200, upd.text
    assert upd.json()["maxPositionSize"] == 20
    # invalid update
    bad = client.post("/api/risk-management/limits", json={"maxLeverage": 100})
    assert bad.status_code == 400
