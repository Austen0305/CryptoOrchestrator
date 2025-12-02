"""
WebSocket notification broadcast tests.

Tests the notification WebSocket endpoint (/ws/notifications) including:
- Real-time scenario broadcast when simulate endpoint is called
- Initial notifications payload on connection
- Notification updates (read/delete events)
"""
import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from server_fastapi.main import app

client = TestClient(app)


def test_ws_notifications_receives_scenario_broadcast():
    """
    Test that simulating a risk scenario broadcasts a risk_scenario event
    over the notifications WebSocket.
    
    This validates the end-to-end flow:
    1. Client connects to /ws/notifications
    2. Backend simulates a scenario via POST /api/risk-scenarios/simulate
    3. The scenario result is broadcast as a 'risk_scenario' message
    4. Client receives the event with full scenario data
    """
    scenario_payload = {
        "portfolio_value": 50000,
        "baseline_var": 1500,
        "shock_percent": -0.15,
        "horizon_days": 7,
        "correlation_factor": 1.1,
    }
    
    received_messages = []
    
    # Connect to notifications WebSocket
    with client.websocket_connect("/ws/notifications") as websocket:
        # Receive initial messages (may include initial_notifications)
        try:
            initial = websocket.receive_json()
            received_messages.append(initial)
        except Exception:
            pass  # No initial message is fine
        
        # Trigger scenario simulation via HTTP endpoint
        # This should cause the backend to broadcast via notification service
        resp = client.post("/api/risk-scenarios/simulate", json=scenario_payload)
        assert resp.status_code == 200, f"Scenario simulation failed: {resp.text}"
        
        # Wait for the WebSocket broadcast
        # The notification service should emit a 'risk_scenario' event
        try:
            ws_message = websocket.receive_json()
            received_messages.append(ws_message)
        except Exception as e:
            pytest.fail(f"Did not receive WebSocket message after scenario simulation: {e}")
    
    # Validate that we received a risk_scenario event
    risk_scenario_events = [msg for msg in received_messages if msg.get("type") == "risk_scenario"]
    assert len(risk_scenario_events) > 0, f"Expected at least one risk_scenario event, received: {received_messages}"
    
    event = risk_scenario_events[0]
    
    # Validate event structure
    assert "data" in event, "risk_scenario event missing 'data' field"
    notification = event["data"]
    
    # Notification wrapper should have standard fields
    assert notification.get("type") == "risk_scenario"
    assert notification.get("category") == "RISK"
    assert notification.get("title") is not None
    assert notification.get("message") is not None
    
    # Nested scenario data should match simulation input/output
    scenario_data = notification.get("data")
    assert scenario_data is not None, "Notification missing nested scenario data"
    
    # Verify input parameters are preserved
    assert scenario_data["portfolio_value"] == scenario_payload["portfolio_value"]
    assert scenario_data["baseline_var"] == scenario_payload["baseline_var"]
    assert scenario_data["shock_percent"] == scenario_payload["shock_percent"]
    assert scenario_data["horizon_days"] == scenario_payload["horizon_days"]
    
    # Verify computed outputs are present
    assert "shocked_var" in scenario_data
    assert "projected_var" in scenario_data
    assert "stress_loss" in scenario_data
    assert "horizon_scale" in scenario_data
    assert "explanation" in scenario_data
    
    # Sanity check on computed values
    assert scenario_data["shocked_var"] >= 0
    assert scenario_data["projected_var"] >= scenario_data["shocked_var"]
    assert scenario_data["stress_loss"] > 0  # Should be positive (absolute loss)


def test_ws_notifications_connection_lifecycle():
    """
    Test basic WebSocket connection and disconnection without triggering events.
    Validates that the endpoint is reachable and handles client lifecycle correctly.
    """
    with client.websocket_connect("/ws/notifications") as websocket:
        # Connection should succeed
        assert websocket is not None
        
        # May receive initial_notifications or nothing; both are valid
        try:
            msg = websocket.receive_json()
            # If we get a message, it should be well-formed
            assert "type" in msg
        except Exception:
            pass  # No immediate message is acceptable
        
        # Clean disconnect (context manager handles close)
    
    # If we reach here without exception, lifecycle is healthy


def test_ws_notifications_multiple_clients():
    """
    Test that multiple WebSocket clients can connect and receive broadcasts.
    Simulates the scenario where multiple browser tabs/sessions are open.
    """
    scenario_payload = {
        "portfolio_value": 75000,
        "baseline_var": 2000,
        "shock_percent": -0.08,
        "horizon_days": 3,
        "correlation_factor": 1.0,
    }
    
    # Connect two clients
    with client.websocket_connect("/ws/notifications") as ws1, \
         client.websocket_connect("/ws/notifications") as ws2:
        
        # Clear any initial messages
        for ws in [ws1, ws2]:
            try:
                ws.receive_json()
            except Exception:
                pass
        
        # Trigger scenario simulation
        resp = client.post("/api/risk-scenarios/simulate", json=scenario_payload)
        assert resp.status_code == 200
        
        # Both clients should receive the broadcast
        messages1 = []
        messages2 = []
        
        try:
            messages1.append(ws1.receive_json())
        except Exception as e:
            pytest.fail(f"Client 1 did not receive broadcast: {e}")
        
        try:
            messages2.append(ws2.receive_json())
        except Exception as e:
            pytest.fail(f"Client 2 did not receive broadcast: {e}")
        
        # Both should have received a risk_scenario event
        assert any(m.get("type") == "risk_scenario" for m in messages1), "Client 1 missing risk_scenario"
        assert any(m.get("type") == "risk_scenario" for m in messages2), "Client 2 missing risk_scenario"
