import pytest
from fastapi.testclient import TestClient

from server_fastapi.main import app


client = TestClient(app)


def test_integrations_status_ok():
    # Inspect registered routes to aid debugging if missing
    paths = {route.path for route in client.app.routes}
    assert "/api/integrations/status" in paths, f"/api/integrations/status not registered. Available: {sorted(paths)}"
    headers = {"Authorization": "Bearer test-token"}
    resp = client.get("/api/integrations/status", headers=headers)
    assert resp.status_code == 200, f"Unexpected status {resp.status_code}; body={resp.text}"
    data = resp.json()
    for key in ["integrations", "adapters", "started"]:
        assert key in data, f"Missing key {key} in response {data}"
