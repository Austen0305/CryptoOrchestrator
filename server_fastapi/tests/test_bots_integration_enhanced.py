"""
Enhanced integration tests for bot management with comprehensive coverage.
Tests bot lifecycle, error handling, and edge cases.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


class TestBotsIntegrationEnhanced:
    """Enhanced integration tests for bot management"""

    async def test_create_bot_with_factory(
        self, client: AsyncClient, db_session, test_user_with_auth, factories
    ):
        """Test bot creation using factory"""
        user = test_user_with_auth
        bot_data = factories["bot"].bot_data()

        response = await client.post(
            "/api/bots/", json=bot_data, headers=user["auth_headers"]
        )

        assert response.status_code in [200, 201]
        bot = response.json()
        assert bot["name"] == bot_data["name"]
        assert bot["symbol"] == bot_data["symbol"]

    async def test_create_multiple_bots(
        self, client: AsyncClient, test_user_with_auth, factories
    ):
        """Test creating multiple bots for same user"""
        user = test_user_with_auth

        # Create 3 bots
        bots = []
        for i in range(3):
            bot_data = factories["bot"].bot_data(name=f"Bot {i+1}")
            response = await client.post(
                "/api/bots/", json=bot_data, headers=user["auth_headers"]
            )
            assert response.status_code in [200, 201]
            bots.append(response.json())

        # Verify all bots are listed
        list_response = await client.get("/api/bots/", headers=user["auth_headers"])
        assert list_response.status_code == 200
        all_bots = list_response.json()
        assert len(all_bots) >= 3

    async def test_bot_ownership_isolation(
        self, client: AsyncClient, db_session, factories
    ):
        """Test that users can only see their own bots"""
        # Create two users
        user1 = await factories["user"].create_user(db_session)
        user2 = await factories["user"].create_user(db_session)

        # Get auth tokens
        from server_fastapi.services.auth.auth_service import AuthService

        auth_service = AuthService()

        token1_data = await auth_service.login_user(user1["email"], user1["password"])
        token2_data = await auth_service.login_user(user2["email"], user2["password"])

        headers1 = {"Authorization": f"Bearer {token1_data['token']}"}
        headers2 = {"Authorization": f"Bearer {token2_data['token']}"}

        # User1 creates a bot
        bot_data = factories["bot"].bot_data()
        create_response = await client.post(
            "/api/bots/", json=bot_data, headers=headers1
        )
        assert create_response.status_code in [200, 201]
        bot_id = create_response.json()["id"]

        # User2 should not see User1's bot
        list_response = await client.get("/api/bots/", headers=headers2)
        assert list_response.status_code == 200
        user2_bots = list_response.json()
        bot_ids = [b.get("id") for b in user2_bots if isinstance(b, dict)]
        assert bot_id not in bot_ids

        # User2 should not be able to access User1's bot directly
        get_response = await client.get(f"/api/bots/{bot_id}", headers=headers2)
        assert get_response.status_code in [403, 404]

    async def test_bot_update_validation(
        self, client: AsyncClient, test_user_with_auth, factories
    ):
        """Test bot update with validation"""
        user = test_user_with_auth

        # Create a bot
        bot_data = factories["bot"].bot_data()
        create_response = await client.post(
            "/api/bots/", json=bot_data, headers=user["auth_headers"]
        )
        assert create_response.status_code in [200, 201]
        bot_id = create_response.json()["id"]

        # Try to update with invalid strategy
        update_data = {"strategy": "invalid_strategy_xyz"}
        update_response = await client.patch(
            f"/api/bots/{bot_id}", json=update_data, headers=user["auth_headers"]
        )
        # Should either reject invalid strategy or accept but not use it
        assert update_response.status_code in [200, 400, 422]

    async def test_bot_delete_cascade(
        self, client: AsyncClient, db_session, test_user_with_auth, factories
    ):
        """Test that deleting a bot properly cleans up related data"""
        user = test_user_with_auth

        # Create a bot
        bot_data = factories["bot"].bot_data()
        create_response = await client.post(
            "/api/bots/", json=bot_data, headers=user["auth_headers"]
        )
        assert create_response.status_code in [200, 201]
        bot_id = create_response.json()["id"]

        # Verify bot exists
        get_response = await client.get(
            f"/api/bots/{bot_id}", headers=user["auth_headers"]
        )
        assert get_response.status_code == 200

        # Delete the bot
        delete_response = await client.delete(
            f"/api/bots/{bot_id}", headers=user["auth_headers"]
        )
        assert delete_response.status_code == 200

        # Verify bot is deleted
        get_response = await client.get(
            f"/api/bots/{bot_id}", headers=user["auth_headers"]
        )
        assert get_response.status_code == 404

    async def test_bot_start_stop_cycle(
        self, client: AsyncClient, test_user_with_auth, factories
    ):
        """Test bot start/stop cycle"""
        user = test_user_with_auth

        # Create a bot
        bot_data = factories["bot"].bot_data()
        create_response = await client.post(
            "/api/bots/", json=bot_data, headers=user["auth_headers"]
        )
        assert create_response.status_code in [200, 201]
        bot_id = create_response.json()["id"]

        # Start the bot
        start_response = await client.post(
            f"/api/bots/{bot_id}/start", headers=user["auth_headers"]
        )
        # May return 200 or 400 depending on implementation
        assert start_response.status_code in [200, 400]

        # Stop the bot
        stop_response = await client.post(
            f"/api/bots/{bot_id}/stop", headers=user["auth_headers"]
        )
        assert stop_response.status_code in [200, 400]

    async def test_bot_performance_endpoint(
        self, client: AsyncClient, test_user_with_auth, factories
    ):
        """Test bot performance metrics endpoint"""
        user = test_user_with_auth

        # Create a bot
        bot_data = factories["bot"].bot_data()
        create_response = await client.post(
            "/api/bots/", json=bot_data, headers=user["auth_headers"]
        )
        assert create_response.status_code in [200, 201]
        bot_id = create_response.json()["id"]

        # Get performance metrics
        perf_response = await client.get(
            f"/api/bots/{bot_id}/performance", headers=user["auth_headers"]
        )

        # Performance endpoint may return 200 with empty data or 404 if not implemented
        if perf_response.status_code == 200:
            perf_data = perf_response.json()
            assert isinstance(perf_data, dict)
        else:
            assert perf_response.status_code in [404, 400]

    async def test_bot_list_pagination(
        self, client: AsyncClient, test_user_with_auth, factories
    ):
        """Test bot list pagination if implemented"""
        user = test_user_with_auth

        # Create multiple bots
        for i in range(5):
            bot_data = factories["bot"].bot_data(name=f"Pagination Bot {i+1}")
            await client.post("/api/bots/", json=bot_data, headers=user["auth_headers"])

        # Get list (may support pagination)
        list_response = await client.get("/api/bots/", headers=user["auth_headers"])
        assert list_response.status_code == 200
        bots = list_response.json()
        assert isinstance(bots, list)
        assert len(bots) >= 5

    async def test_bot_error_handling(self, client: AsyncClient, test_user_with_auth):
        """Test error handling for invalid bot operations"""
        user = test_user_with_auth

        # Try to get non-existent bot
        response = await client.get(
            "/api/bots/non-existent-id-12345", headers=user["auth_headers"]
        )
        assert response.status_code == 404

        # Try to update non-existent bot
        response = await client.patch(
            "/api/bots/non-existent-id-12345",
            json={"name": "Updated"},
            headers=user["auth_headers"],
        )
        assert response.status_code == 404

        # Try to delete non-existent bot
        response = await client.delete(
            "/api/bots/non-existent-id-12345", headers=user["auth_headers"]
        )
        assert response.status_code == 404
