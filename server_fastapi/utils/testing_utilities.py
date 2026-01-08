"""
Testing Utilities and Fixtures
Provides utilities for writing and running tests
"""

import asyncio
import os
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///file:pytest_shared?mode=memory&cache=shared",
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Create tables
    from ..models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_user() -> dict[str, Any]:
    """Create test user data"""
    return {
        "id": "test_user_123",
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
    }


@pytest.fixture
async def authenticated_client(test_client, test_user) -> AsyncClient:
    """Create authenticated test client"""
    # Login to get token
    response = await test_client.post(
        "/api/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"],
        },
    )

    if response.status_code == 200:
        token = response.json().get("access_token")
        test_client.headers.update({"Authorization": f"Bearer {token}"})

    return test_client


class TestHelpers:
    """Helper functions for tests"""

    @staticmethod
    async def create_user(
        session: AsyncSession,
        email: str = "test@example.com",
        username: str = "testuser",
        password: str = "testpassword123",
    ) -> dict[str, Any]:
        """Create a test user"""
        from ..models.user import User
        from ..utils.security import hash_password

        user = User(
            email=email,
            username=username,
            password_hash=hash_password(password),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
        }

    @staticmethod
    async def create_bot(
        session: AsyncSession,
        user_id: str,
        name: str = "Test Bot",
        strategy: str = "momentum",
    ) -> dict[str, Any]:
        """Create a test bot"""
        from ..models.bot import Bot

        bot = Bot(
            user_id=user_id,
            name=name,
            strategy=strategy,
            initial_balance=1000.0,
        )
        session.add(bot)
        await session.commit()
        await session.refresh(bot)

        return {
            "id": str(bot.id),
            "name": bot.name,
            "strategy": bot.strategy,
            "user_id": str(bot.user_id),
        }

    @staticmethod
    def assert_response_success(response, expected_status: int = 200):
        """Assert response is successful"""
        assert response.status_code == expected_status, (
            f"Expected status {expected_status}, got {response.status_code}. "
            f"Response: {response.text}"
        )

    @staticmethod
    def assert_response_error(response, expected_status: int = 400):
        """Assert response is an error"""
        assert response.status_code == expected_status, (
            f"Expected error status {expected_status}, got {response.status_code}. "
            f"Response: {response.text}"
        )

    @staticmethod
    def assert_json_response(response, expected_keys: list):
        """Assert response has expected JSON keys"""
        data = response.json()
        for key in expected_keys:
            assert key in data, f"Missing key: {key} in response: {data}"


# Pytest markers
pytest_plugins = ["pytest_asyncio"]


# Async test decorator
def async_test(func):
    """Decorator for async tests"""
    return pytest.mark.asyncio(func)


# Database transaction rollback fixture
@pytest.fixture(autouse=True)
async def rollback_transaction(test_session):
    """Automatically rollback transactions after each test"""
    yield
    await test_session.rollback()
