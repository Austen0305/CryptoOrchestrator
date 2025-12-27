"""
Tests for cold storage endpoints
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from server_fastapi.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_cold_storage_eligibility_requires_auth(client):
    """Test that cold storage eligibility endpoint requires authentication"""
    response = client.get("/api/cold-storage/eligibility")
    assert response.status_code == 401  # Unauthorized


def test_transfer_to_cold_storage_requires_auth(client):
    """Test that transfer to cold storage endpoint requires authentication"""
    response = client.post(
        "/api/cold-storage/transfer-to-cold", json={"currency": "BTC", "amount": 1.0}
    )
    assert response.status_code == 401  # Unauthorized


def test_get_cold_storage_balance_requires_auth(client):
    """Test that get cold storage balance endpoint requires authentication"""
    response = client.get("/api/cold-storage/balance")
    assert response.status_code == 401  # Unauthorized


def test_withdraw_from_cold_storage_requires_auth(client):
    """Test that withdraw from cold storage endpoint requires authentication"""
    response = client.post(
        "/api/cold-storage/withdraw-from-cold",
        json={"currency": "BTC", "amount": 0.5, "destination": "hot_wallet"},
    )
    assert response.status_code == 401  # Unauthorized
