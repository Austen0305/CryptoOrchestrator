"""
Integration Testing Utilities
Provides utilities for writing and running integration tests
"""

import pytest
import asyncio
import httpx
from typing import Dict, Any, Optional, AsyncGenerator, List
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
import os
import json

logger = pytest.getLogger(__name__)


class IntegrationTestClient:
    """
    Integration test client with helper methods
    
    Features:
    - Authenticated requests
    - Test data setup/teardown
    - Assertion helpers
    - Response validation
    - Error handling
    """

    def __init__(self, client: httpx.AsyncClient, base_url: str = "http://test"):
        self.client = client
        self.base_url = base_url
        self.auth_token: Optional[str] = None
        self.user_id: Optional[str] = None

    async def authenticate(self, email: str = "test@example.com", password: str = "testpassword123"):
        """Authenticate and store token"""
        response = await self.client.post(
            f"{self.base_url}/api/auth/login",
            json={"email": email, "password": password},
        )
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token")
            self.user_id = data.get("user_id")
            return True
        return False

    async def register_user(
        self,
        email: str = "test@example.com",
        username: str = "testuser",
        password: str = "testpassword123",
    ) -> Dict[str, Any]:
        """Register a new user"""
        response = await self.client.post(
            f"{self.base_url}/api/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password,
            },
        )
        response.raise_for_status()
        return response.json()

    def get_headers(self) -> Dict[str, str]:
        """Get request headers with auth"""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    async def get(self, path: str, **kwargs) -> httpx.Response:
        """GET request"""
        headers = kwargs.pop("headers", {})
        headers.update(self.get_headers())
        return await self.client.get(f"{self.base_url}{path}", headers=headers, **kwargs)

    async def post(self, path: str, json: Dict[str, Any] = None, **kwargs) -> httpx.Response:
        """POST request"""
        headers = kwargs.pop("headers", {})
        headers.update(self.get_headers())
        return await self.client.post(
            f"{self.base_url}{path}", json=json, headers=headers, **kwargs
        )

    async def put(self, path: str, json: Dict[str, Any] = None, **kwargs) -> httpx.Response:
        """PUT request"""
        headers = kwargs.pop("headers", {})
        headers.update(self.get_headers())
        return await self.client.put(
            f"{self.base_url}{path}", json=json, headers=headers, **kwargs
        )

    async def delete(self, path: str, **kwargs) -> httpx.Response:
        """DELETE request"""
        headers = kwargs.pop("headers", {})
        headers.update(self.get_headers())
        return await self.client.delete(f"{self.base_url}{path}", headers=headers, **kwargs)

    def assert_success(self, response: httpx.Response, expected_status: int = 200):
        """Assert response is successful"""
        assert response.status_code == expected_status, (
            f"Expected status {expected_status}, got {response.status_code}. "
            f"Response: {response.text}"
        )

    def assert_error(self, response: httpx.Response, expected_status: int = 400):
        """Assert response is an error"""
        assert response.status_code == expected_status, (
            f"Expected error status {expected_status}, got {response.status_code}. "
            f"Response: {response.text}"
        )

    def assert_json_keys(self, response: httpx.Response, expected_keys: List[str]):
        """Assert response has expected JSON keys"""
        data = response.json()
        for key in expected_keys:
            assert key in data, f"Missing key: {key} in response: {data}"


@pytest.fixture
async def integration_client(app) -> AsyncGenerator[IntegrationTestClient, None]:
    """Create integration test client"""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield IntegrationTestClient(client)


@pytest.fixture
async def authenticated_client(integration_client: IntegrationTestClient) -> IntegrationTestClient:
    """Create authenticated integration test client"""
    # Register and authenticate
    await integration_client.register_user()
    await integration_client.authenticate()
    return integration_client


class TestDataManager:
    """Manages test data setup and teardown"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.created_objects: List[Any] = []

    async def create_user(self, **kwargs) -> Any:
        """Create test user"""
        from ..models.user import User
        from ..utils.security import hash_password

        user = User(
            email=kwargs.get("email", "test@example.com"),
            username=kwargs.get("username", "testuser"),
            password_hash=hash_password(kwargs.get("password", "testpassword123")),
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        self.created_objects.append(("user", user.id))
        return user

    async def create_bot(self, user_id: str, **kwargs) -> Any:
        """Create test bot"""
        from ..models.bot import Bot

        bot = Bot(
            user_id=user_id,
            name=kwargs.get("name", "Test Bot"),
            strategy=kwargs.get("strategy", "momentum"),
            initial_balance=kwargs.get("initial_balance", 1000.0),
        )
        self.session.add(bot)
        await self.session.commit()
        await self.session.refresh(bot)
        self.created_objects.append(("bot", bot.id))
        return bot

    async def cleanup(self):
        """Cleanup created test data"""
        # Cleanup in reverse order
        for obj_type, obj_id in reversed(self.created_objects):
            try:
                if obj_type == "user":
                    from ..models.user import User
                    await self.session.delete(await self.session.get(User, obj_id))
                elif obj_type == "bot":
                    from ..models.bot import Bot
                    await self.session.delete(await self.session.get(Bot, obj_id))
            except Exception as e:
                logger.warning(f"Error cleaning up {obj_type} {obj_id}: {e}")

        await self.session.commit()
        self.created_objects.clear()


@pytest.fixture
async def test_data_manager(test_session: AsyncSession) -> TestDataManager:
    """Create test data manager"""
    manager = TestDataManager(test_session)
    yield manager
    await manager.cleanup()

