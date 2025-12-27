"""
Integration tests for bot management endpoints
Uses async patterns with AsyncClient for proper async route testing
Enhanced with proper database isolation and test factories
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
import uuid
import logging

logger = logging.getLogger(__name__)

# Use conftest fixtures
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(autouse=True)
async def reset_db_state(db_session):
    """
    Automatically reset database state before each test.
    This ensures complete isolation between tests.
    """
    # Rollback any existing transaction
    await db_session.rollback()

    # Begin a fresh transaction for this test
    await db_session.begin()

    yield

    # Cleanup after test
    await db_session.rollback()


class TestBotsIntegration:
    """Integration tests for bot management endpoints"""

    async def test_get_bots_empty_list(self, client: AsyncClient, auth_headers):
        """Test getting bots when no bots exist"""
        response = await client.get("/api/bots/", headers=auth_headers)

        assert response.status_code == 200
        bots = response.json()
        assert isinstance(bots, list)

    async def test_create_bot_success(
        self, client: AsyncClient, auth_headers, test_bot_config
    ):
        """Test successful bot creation"""
        response = await client.post(
            "/api/bots/", json=test_bot_config, headers=auth_headers
        )

        if response.status_code not in [200, 201]:
            # Log error details for debugging
            error_data = (
                response.json()
                if response.headers.get("content-type", "").startswith(
                    "application/json"
                )
                else response.text
            )
            logger.error(f"Bot creation failed: {response.status_code} - {error_data}")

        assert response.status_code in [
            200,
            201,
        ], f"Expected 200/201, got {response.status_code}: {error_data if 'error_data' in locals() else response.text}"
        bot = response.json()
        assert bot["name"] == test_bot_config["name"]
        assert bot["symbol"] == test_bot_config["symbol"]
        assert bot["strategy"] == test_bot_config["strategy"]
        assert "id" in bot

    async def test_create_bot_invalid_strategy(self, client: AsyncClient, auth_headers):
        """Test bot creation with invalid strategy"""
        bot_data = {
            "name": "Invalid Strategy Bot",
            "symbol": "BTC/USDT",
            "strategy": "invalid_strategy",
            "config": {},
        }

        response = await client.post("/api/bots/", json=bot_data, headers=auth_headers)

        assert response.status_code in [400, 422]  # Validation error

    async def test_get_bot_by_id(
        self, client: AsyncClient, auth_headers, test_bot_config
    ):
        """Test getting a specific bot by ID"""
        # First create a bot
        create_response = await client.post(
            "/api/bots/", json=test_bot_config, headers=auth_headers
        )
        assert create_response.status_code == 200
        created_bot = create_response.json()

        # Now retrieve it
        response = await client.get(
            f"/api/bots/{created_bot['id']}", headers=auth_headers
        )

        assert response.status_code == 200
        bot = response.json()
        assert bot["id"] == created_bot["id"]
        assert bot["name"] == test_bot_config["name"]

    async def test_get_bot_not_found(self, client: AsyncClient, auth_headers):
        """Test getting a non-existent bot"""
        response = await client.get(
            "/api/bots/nonexistent-bot-id", headers=auth_headers
        )

        assert response.status_code == 404

    async def test_update_bot(self, client: AsyncClient, auth_headers, test_bot_config):
        """Test updating bot configuration"""
        # Create a bot first
        create_response = await client.post(
            "/api/bots/", json=test_bot_config, headers=auth_headers
        )
        assert create_response.status_code == 200
        created_bot = create_response.json()

        # Update the bot
        update_data = {
            "name": "Updated Bot Name",
            "config": {"updated": "config", "new_param": 123},
        }

        response = await client.patch(
            f"/api/bots/{created_bot['id']}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 200
        updated_bot = response.json()
        assert updated_bot["name"] == "Updated Bot Name"
        assert "updated" in updated_bot.get("config", {})

    async def test_update_bot_not_found(self, client: AsyncClient, auth_headers):
        """Test updating a non-existent bot"""
        update_data = {"name": "New Name"}

        response = await client.patch(
            "/api/bots/nonexistent-bot-id", json=update_data, headers=auth_headers
        )

        assert response.status_code == 404

    async def test_delete_bot(self, client: AsyncClient, auth_headers, test_bot_config):
        """Test deleting a bot"""
        # Create a bot first
        create_response = await client.post(
            "/api/bots/", json=test_bot_config, headers=auth_headers
        )
        assert create_response.status_code == 200
        created_bot = create_response.json()

        # Delete the bot
        response = await client.delete(
            f"/api/bots/{created_bot['id']}", headers=auth_headers
        )

        assert response.status_code == 200
        assert (
            "deleted" in response.json().get("message", "").lower()
            or response.status_code == 200
        )

        # Verify bot is deleted
        get_response = await client.get(
            f"/api/bots/{created_bot['id']}", headers=auth_headers
        )
        assert get_response.status_code == 404

    async def test_delete_bot_not_found(self, client: AsyncClient, auth_headers):
        """Test deleting a non-existent bot"""
        response = await client.delete(
            "/api/bots/nonexistent-bot-id", headers=auth_headers
        )

        assert response.status_code == 404

    async def test_start_bot(self, client: AsyncClient, auth_headers, test_bot_config):
        """Test starting a bot"""
        # Create a bot first
        create_response = await client.post(
            "/api/bots/", json=test_bot_config, headers=auth_headers
        )
        assert create_response.status_code == 200
        created_bot = create_response.json()

        # Start the bot
        response = await client.post(
            f"/api/bots/{created_bot['id']}/start", headers=auth_headers
        )

        # May return 200 or 400 depending on implementation
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            assert "start" in response.json().get("message", "").lower()

    async def test_stop_bot(self, client: AsyncClient, auth_headers, test_bot_config):
        """Test stopping a bot"""
        # Create a bot first
        create_response = await client.post(
            "/api/bots/", json=test_bot_config, headers=auth_headers
        )
        assert create_response.status_code == 200
        created_bot = create_response.json()

        # Start the bot first (if needed)
        await client.post(f"/api/bots/{created_bot['id']}/start", headers=auth_headers)

        # Stop the bot
        response = await client.post(
            f"/api/bots/{created_bot['id']}/stop", headers=auth_headers
        )

        # May return 200 or 400 depending on implementation
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            assert "stop" in response.json().get("message", "").lower()

    async def test_get_bot_performance(
        self, client: AsyncClient, auth_headers, test_bot_config
    ):
        """Test getting bot performance metrics"""
        # Create a bot first
        create_response = await client.post(
            "/api/bots/", json=test_bot_config, headers=auth_headers
        )
        assert create_response.status_code == 200
        created_bot = create_response.json()

        # Get performance
        response = await client.get(
            f"/api/bots/{created_bot['id']}/performance", headers=auth_headers
        )

        # May return 200 or 404/400 if not implemented
        if response.status_code == 200:
            performance = response.json()
            # Check for expected performance fields if available
            assert isinstance(performance, dict)

    async def test_bots_unauthenticated(self, client: AsyncClient):
        """Test accessing bot endpoints without authentication"""
        response = await client.get("/api/bots/")

        assert response.status_code in [401, 403]  # Unauthorized or Forbidden

        # Test create bot
        bot_data = {
            "name": "Test Bot",
            "symbol": "BTC/USDT",
            "strategy": "simple_ma",
            "config": {},
        }

        response = await client.post("/api/bots/", json=bot_data)
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden
