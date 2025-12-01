"""
Tests for comprehensive health check endpoints
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


def test_liveness_probe(client):
    """Test liveness probe endpoint"""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_readiness_probe(client):
    """Test readiness probe endpoint"""
    response = client.get("/health/ready")
    # May return 200 or 503 depending on database availability
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data


def test_startup_probe(client):
    """Test startup probe endpoint"""
    response = client.get("/health/startup")
    # May return 200 or 503 depending on startup time
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data


def test_detailed_health_check(client):
    """Test detailed health check endpoint"""
    response = client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "dependencies" in data
    assert isinstance(data["dependencies"], list)


def test_detailed_health_check_with_optional(client):
    """Test detailed health check with optional dependencies"""
    response = client.get("/health/detailed?include_optional=true")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "dependencies" in data


def test_specific_dependency_check_database(client):
    """Test checking specific dependency (database)"""
    response = client.get("/health/dependencies/database")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "status" in data
    assert data["name"] == "database"


def test_specific_dependency_check_redis(client):
    """Test checking specific dependency (redis)"""
    response = client.get("/health/dependencies/redis")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["name"] == "redis"


def test_specific_dependency_check_invalid(client):
    """Test checking invalid dependency"""
    response = client.get("/health/dependencies/invalid_dependency")
    assert response.status_code == 404

