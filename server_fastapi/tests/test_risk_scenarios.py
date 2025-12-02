from fastapi.testclient import TestClient
from server_fastapi.main import app

client = TestClient(app)


def test_risk_scenario_simulate_ok():
    payload = {
        "portfolio_value": 100000,
        "baseline_var": 2500,
        "shock_percent": -0.1,
        "horizon_days": 5,
        "correlation_factor": 1.25,
    }
    resp = client.post("/api/risk-scenarios/simulate", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    for key in [
        "portfolio_value","baseline_var","shock_percent","correlation_factor","horizon_days",
        "shocked_var","projected_var","stress_loss","horizon_scale","explanation"
    ]:
        assert key in data
    assert data["portfolio_value"] == payload["portfolio_value"]
    assert data["horizon_days"] == payload["horizon_days"]
    assert data["shock_percent"] == payload["shock_percent"]
    # shocked_var should reflect absolute loss proportion
    assert data["shocked_var"] >= 0
    assert data["projected_var"] >= data["shocked_var"]


def test_risk_scenario_invalid_shock():
    bad_payload = {
        "portfolio_value": 100000,
        "baseline_var": 2500,
        "shock_percent": -1.5,  # below allowed floor (-1)
        "horizon_days": 1,
        "correlation_factor": 1.0,
    }
    resp = client.post("/api/risk-scenarios/simulate", json=bad_payload)
    # Pydantic validation triggers 422 Unprocessable Entity
    assert resp.status_code == 422
