"""
Tests for cache warmer endpoints
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient

from server_fastapi.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_cache_warmer_status_requires_auth(client):
    """Test that cache warmer status endpoint requires authentication"""
    response = client.get("/api/cache-warmer/status")
    assert response.status_code == 401  # Unauthorized


def test_trigger_warmup_requires_auth(client):
    """Test that trigger warmup endpoint requires authentication"""
    response = client.post("/api/cache-warmer/warmup")
    assert response.status_code == 401  # Unauthorized


def test_start_cache_warmer_requires_auth(client):
    """Test that start cache warmer endpoint requires authentication"""
    response = client.post("/api/cache-warmer/start")
    assert response.status_code == 401  # Unauthorized


def test_stop_cache_warmer_requires_auth(client):
    """Test that stop cache warmer endpoint requires authentication"""
    response = client.post("/api/cache-warmer/stop")
    assert response.status_code == 401  # Unauthorized
