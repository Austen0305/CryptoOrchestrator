import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
import uuid
import os
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set test database URL before importing anything
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

# Now import app and database utilities
from server_fastapi.main import app

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database(event_loop):
    """Initialize test database with all tables"""
    # Import database.py directly, not the database package
    from server_fastapi.database import init_database, close_database
    await init_database()
    yield
    await close_database()

@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    """Get authentication headers for a logged-in user with unique email per test"""
    # Use unique email to avoid duplicate registration across tests
    unique_email = f"testuser-{uuid.uuid4().hex[:8]}@example.com"
    
    # Register a test user
    register_data = {
        "email": unique_email,
        "password": "TestPassword123!",
        "name": "Test User"
    }
    reg_response = client.post("/api/auth/register", json=register_data)
    assert reg_response.status_code == 200, f"Registration failed: {reg_response.json()}"

    # Login to get token
    login_data = {
        "email": unique_email,
        "password": "TestPassword123!"
    }
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200, f"Login failed: {response.json()}"
    token = response.json()["data"]["token"]

    return {"Authorization": f"Bearer {token}"}

class TestBotsIntegration:
    """Integration tests for bot management endpoints"""

    def test_get_bots_empty_list(self, client, auth_headers):
        """Test getting bots when no bots exist"""
        response = client.get("/api/bots/", headers=auth_headers)

        assert response.status_code == 200
        bots = response.json()
        assert isinstance(bots, list)

    def test_create_bot_success(self, client, auth_headers):
        """Test successful bot creation"""
        bot_data = {
            "name": "Test Trading Bot",
            "symbol": "BTC/USDT",
            "strategy": "simple_ma",
            "config": {
                "max_position_size": 0.1,
                "stop_loss": 0.02,
                "take_profit": 0.05,
                "risk_per_trade": 0.01
            }
        }

        response = client.post("/api/bots/", json=bot_data, headers=auth_headers)

        if response.status_code != 200:
            print(f"Bot creation failed: {response.status_code} - {response.json()}")
        assert response.status_code == 200
        bot = response.json()
        assert bot["name"] == "Test Trading Bot"
        assert bot["symbol"] == "BTC/USDT"
        assert bot["strategy"] == "simple_ma"
        assert "id" in bot

    def test_create_bot_invalid_strategy(self, client, auth_headers):
        """Test bot creation with invalid strategy"""
        bot_data = {
            "name": "Invalid Strategy Bot",
            "symbol": "BTC/USDT",
            "strategy": "invalid_strategy",
            "config": {}
        }

        response = client.post("/api/bots/", json=bot_data, headers=auth_headers)

        assert response.status_code == 400

    def test_get_bot_by_id(self, client, auth_headers):
        """Test getting a specific bot by ID"""
        # First create a bot
        bot_data = {
            "name": "Retrieve Test Bot",
            "symbol": "ETH/USDT",
            "strategy": "simple_ma",
            "config": {"test": "config"}
        }

        create_response = client.post("/api/bots/", json=bot_data, headers=auth_headers)
        assert create_response.status_code == 200
        created_bot = create_response.json()

        # Now retrieve it
        response = client.get(f"/api/bots/{created_bot['id']}", headers=auth_headers)

        assert response.status_code == 200
        bot = response.json()
        assert bot["id"] == created_bot["id"]
        assert bot["name"] == "Retrieve Test Bot"

    def test_get_bot_not_found(self, client, auth_headers):
        """Test getting a non-existent bot"""
        response = client.get("/api/bots/nonexistent-bot-id", headers=auth_headers)

        assert response.status_code == 404

    def test_update_bot(self, client, auth_headers):
        """Test updating bot configuration"""
        # Create a bot first
        bot_data = {
            "name": "Update Test Bot",
            "symbol": "BTC/USDT",
            "strategy": "simple_ma",
            "config": {"initial": "config"}
        }

        create_response = client.post("/api/bots/", json=bot_data, headers=auth_headers)
        created_bot = create_response.json()

        # Update the bot
        update_data = {
            "name": "Updated Bot Name",
            "config": {"updated": "config", "new_param": 123}
        }

        response = client.patch(f"/api/bots/{created_bot['id']}", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        updated_bot = response.json()
        assert updated_bot["name"] == "Updated Bot Name"
        assert "updated" in updated_bot["config"]
        assert "new_param" in updated_bot["config"]

    def test_update_bot_not_found(self, client, auth_headers):
        """Test updating a non-existent bot"""
        update_data = {"name": "New Name"}

        response = client.patch("/api/bots/nonexistent-bot-id", json=update_data, headers=auth_headers)

        assert response.status_code == 404

    def test_delete_bot(self, client, auth_headers):
        """Test deleting a bot"""
        # Create a bot first
        bot_data = {
            "name": "Delete Test Bot",
            "symbol": "BTC/USDT",
            "strategy": "simple_ma",
            "config": {}
        }

        create_response = client.post("/api/bots/", json=bot_data, headers=auth_headers)
        created_bot = create_response.json()

        # Delete the bot
        response = client.delete(f"/api/bots/{created_bot['id']}", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["message"] == "Bot deleted successfully"

        # Verify bot is deleted
        get_response = client.get(f"/api/bots/{created_bot['id']}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_bot_not_found(self, client, auth_headers):
        """Test deleting a non-existent bot"""
        response = client.delete("/api/bots/nonexistent-bot-id", headers=auth_headers)

        assert response.status_code == 404

    def test_start_bot(self, client, auth_headers):
        """Test starting a bot"""
        # Create a bot first
        bot_data = {
            "name": "Start Test Bot",
            "symbol": "BTC/USDT",
            "strategy": "simple_ma",
            "config": {
                "max_position_size": 0.1,
                "stop_loss": 0.02,
                "take_profit": 0.05
            }
        }

        create_response = client.post("/api/bots/", json=bot_data, headers=auth_headers)
        created_bot = create_response.json()

        # Start the bot
        response = client.post(f"/api/bots/{created_bot['id']}/start", headers=auth_headers)

        assert response.status_code == 200
        assert "started successfully" in response.json()["message"]

    def test_start_bot_already_active(self, client, auth_headers):
        """Test starting a bot that's already active"""
        # Create and start a bot first
        bot_data = {
            "name": "Already Active Bot",
            "symbol": "BTC/USDT",
            "strategy": "simple_ma",
            "config": {}
        }

        create_response = client.post("/api/bots/", json=bot_data, headers=auth_headers)
        created_bot = create_response.json()

        # Start the bot first time
        client.post(f"/api/bots/{created_bot['id']}/start", headers=auth_headers)

        # Try to start it again
        response = client.post(f"/api/bots/{created_bot['id']}/start", headers=auth_headers)

        assert response.status_code == 400  # Should fail because bot is already active

    def test_stop_bot(self, client, auth_headers):
        """Test stopping a bot"""
        # Create and start a bot first
        bot_data = {
            "name": "Stop Test Bot",
            "symbol": "BTC/USDT",
            "strategy": "simple_ma",
            "config": {}
        }

        create_response = client.post("/api/bots/", json=bot_data, headers=auth_headers)
        created_bot = create_response.json()

        # Start the bot
        client.post(f"/api/bots/{created_bot['id']}/start", headers=auth_headers)

        # Stop the bot
        response = client.post(f"/api/bots/{created_bot['id']}/stop", headers=auth_headers)

        assert response.status_code == 200
        assert "stopped successfully" in response.json()["message"]

    def test_stop_bot_not_active(self, client, auth_headers):
        """Test stopping a bot that's not active"""
        # Create a bot but don't start it
        bot_data = {
            "name": "Not Active Bot",
            "symbol": "BTC/USDT",
            "strategy": "simple_ma",
            "config": {}
        }

        create_response = client.post("/api/bots/", json=bot_data, headers=auth_headers)
        created_bot = create_response.json()

        # Try to stop the inactive bot
        response = client.post(f"/api/bots/{created_bot['id']}/stop", headers=auth_headers)

        assert response.status_code == 400  # Should fail because bot is not active

    def test_get_bot_performance(self, client, auth_headers):
        """Test getting bot performance metrics"""
        # Create a bot first
        bot_data = {
            "name": "Performance Test Bot",
            "symbol": "BTC/USDT",
            "strategy": "simple_ma",
            "config": {}
        }

        create_response = client.post("/api/bots/", json=bot_data, headers=auth_headers)
        created_bot = create_response.json()

        # Get performance
        response = client.get(f"/api/bots/{created_bot['id']}/performance", headers=auth_headers)

        assert response.status_code == 200
        performance = response.json()
        assert "total_trades" in performance
        assert "win_rate" in performance
        assert "total_pnl" in performance
        assert "sharpe_ratio" in performance

    def test_get_bot_model_status(self, client, auth_headers):
        """Test getting bot model status"""
        # Create a bot with ML strategy
        bot_data = {
            "name": "ML Model Test Bot",
            "symbol": "BTC/USDT",
            "strategy": "ml_enhanced",
            "config": {
                "ml_config": {
                    "confidence_threshold": 0.7
                }
            }
        }

        create_response = client.post("/api/bots/", json=bot_data, headers=auth_headers)
        created_bot = create_response.json()

        # Get model status
        response = client.get(f"/api/bots/{created_bot['id']}/model", headers=auth_headers)

        assert response.status_code == 200
        model_status = response.json()
        assert model_status["strategy"] == "ml_enhanced"
        assert "model_trained" in model_status

    def test_get_safety_status(self, client, auth_headers):
        """Test getting system safety status"""
        response = client.get("/api/bots/safety/status", headers=auth_headers)

        assert response.status_code == 200
        status_data = response.json()
        assert isinstance(status_data, dict)

    def test_emergency_stop_unauthorized(self, client, auth_headers):
        """Test emergency stop without admin privileges"""
        response = client.post("/api/bots/safety/emergency-stop", headers=auth_headers)

        assert response.status_code == 403  # Forbidden - not admin

    def test_bots_unauthenticated(self, client):
        """Test accessing bot endpoints without authentication"""
        response = client.get("/api/bots/")

        assert response.status_code == 403  # Forbidden

        # Test create bot
        bot_data = {
            "name": "Test Bot",
            "symbol": "BTC/USDT",
            "strategy": "simple_ma",
            "config": {}
        }

        response = client.post("/api/bots/", json=bot_data)
        assert response.status_code == 403  # Forbidden
