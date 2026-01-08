import asyncio
import logging
import os
import sys
from datetime import UTC
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, StaticPool

# Set TESTING environment variable for test mode
os.environ["TESTING"] = "true"

logger = logging.getLogger(__name__)

# Ensure project root is on sys.path for "server_fastapi" package resolution
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from server_fastapi.database import Base  # type: ignore
except Exception:
    Base = None  # Database layer may be optional in some environments

# Test database URL - use shared memory SQLite for tests (allows multiple connections)
# This fixes the issue where tests would fail with "no such table" errors
# Can also use PostgreSQL for more realistic testing
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///file:pytest_shared?mode=memory&cache=shared",
)
USE_POSTGRES = TEST_DATABASE_URL.startswith("postgresql")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_engine():
    """
    Create a test database engine with isolated database for tests.
    Supports both SQLite (in-memory) and PostgreSQL.
    """
    if Base is None:
        return None

    if USE_POSTGRES:
        # PostgreSQL: Create isolated test database
        engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
            poolclass=NullPool,  # No pooling for tests
        )
    else:
        # SQLite: Use shared in-memory database
        engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
            poolclass=StaticPool,  # Use static pool for SQLite
            connect_args={"check_same_thread": False},  # Needed for SQLite
        )
    return engine


@pytest_asyncio.fixture(scope="session", autouse=True)
async def test_db_setup(test_engine):
    """
    Set up test database schema if DB is available.
    Supports both Alembic migrations and direct table creation.
    Uses automatic Alembic migrations when TEST_USE_ALEMBIC=true.
    Enhanced with proper isolation and automatic teardown.
    """
    if Base is None or test_engine is None:
        yield
        return

    # Import all models to ensure metadata is populated
    try:
        from server_fastapi import models  # noqa: F401
    except ImportError:
        pass

    # Try to use Alembic migrations if available, otherwise use create_all
    # Default to False in CI/local quick runs to avoid long-running Alembic operations
    use_alembic = (
        os.getenv("TEST_USE_ALEMBIC", "false").lower() == "true"
    )  # Set to 'true' explicitly to enable Alembic migrations when needed

    if use_alembic:
        # Use Alembic migrations for proper schema setup
        try:
            from .utils.test_database import run_alembic_migrations

            await run_alembic_migrations(TEST_DATABASE_URL, test_engine)
            logger.info("Test database setup using Alembic migrations")
        except Exception as e:
            # Fallback to create_all if Alembic fails
            logger.warning(f"Alembic migration failed, using create_all: {e}")
            # Try to create tables, handle "already exists" errors
            try:
                async with test_engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
            except Exception as e2:
                error_str = str(e2).lower()
                if (
                    "already exists" in error_str
                    or "table" in error_str
                    and "exists" in error_str
                ):
                    logger.debug(f"Tables already exist, dropping and recreating: {e2}")
                    try:
                        async with test_engine.begin() as conn:
                            await conn.run_sync(Base.metadata.drop_all)
                        async with test_engine.begin() as conn:
                            await conn.run_sync(Base.metadata.create_all)
                    except Exception as e3:
                        logger.warning(f"Could not recreate tables: {e3}")
                else:
                    raise
    else:
        # Default: use create_all (faster for tests but less realistic)
        # Try to create tables, catch and ignore "already exists" errors
        try:
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            error_str = str(e).lower()
            # If tables already exist, that's fine for SQLite (shared memory can persist)
            if (
                "already exists" in error_str
                or "table" in error_str
                and "exists" in error_str
            ):
                logger.debug(f"Tables already exist (expected with shared SQLite): {e}")
                # Try to drop and recreate for clean state
                try:
                    async with test_engine.begin() as conn:
                        await conn.run_sync(Base.metadata.drop_all)
                    async with test_engine.begin() as conn:
                        await conn.run_sync(Base.metadata.create_all)
                    logger.debug("Successfully recreated tables after drop")
                except Exception as e2:
                    logger.warning(
                        f"Could not recreate tables: {e2}, continuing anyway"
                    )
            else:
                # Re-raise if it's a different error
                raise

    yield

    # Cleanup after all tests - automatic teardown
    try:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Test database teardown completed")
    except Exception as e:
        logger.warning(f"Error during test database teardown: {e}")

    # Dispose engine
    try:
        await test_engine.dispose()
    except Exception as e:
        logger.warning(f"Error disposing test engine: {e}")


@pytest_asyncio.fixture
async def db_session(test_engine, test_db_setup):
    """
    Provide an isolated database session for each test.
    Each test gets its own transaction that rolls back automatically.
    Uses savepoint for nested transaction support.
    """
    if test_engine is None:

        class DummySession:
            async def execute(self, *a, **k):
                class R:
                    def scalar_one_or_none(self):
                        return None

                    def scalars(self):
                        return []

                return R()

            async def commit(self):
                pass

            async def refresh(self, obj):
                pass

            async def rollback(self):
                pass

            async def close(self):
                pass

            async def begin_nested(self):
                pass

        yield DummySession()
        return

    async_session = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Begin transaction for this test
        trans = await session.begin()

        # Use savepoint for nested transaction support (allows rollback within test)
        savepoint = await session.begin_nested()

        try:
            yield session
        except Exception:
            # Rollback on any exception
            try:
                await savepoint.rollback()
            except Exception:
                pass
            try:
                await session.rollback()
            except Exception:
                pass
            raise
        finally:
            # Always rollback to clean up test data
            try:
                await savepoint.rollback()
            except Exception:
                pass
            try:
                await trans.rollback()
            except Exception:
                pass
            try:
                await session.close()
            except Exception:
                pass


@pytest.fixture(scope="session")
def mock_user_repository():
    """Mock user repository for testing"""

    class MockUserRepository:
        def __init__(self):
            self.users = {}
            self.next_id = 1

        async def create_user(self, username: str, email: str, hashed_password: str):
            user_id = self.next_id
            self.next_id += 1
            user = {
                "id": user_id,
                "username": username,
                "email": email,
                "hashed_password": hashed_password,
                "is_active": True,
                "created_at": "2023-01-01T00:00:00Z",
            }
            self.users[user_id] = user
            return user

        async def get_user_by_username(self, username: str):
            for user in self.users.values():
                if user["username"] == username:
                    return user
            return None

        async def get_user_by_email(self, email: str):
            for user in self.users.values():
                if user["email"] == email:
                    return user
            return None

        async def get_user_by_id(self, user_id: int):
            return self.users.get(user_id)

    return MockUserRepository()


@pytest.fixture(scope="session")
def mock_bot_repository():
    """Mock bot repository for testing"""

    class MockBotRepository:
        def __init__(self):
            self.bots = {}
            self.next_id = 1

        async def create_bot(self, user_id: int, name: str, config: dict):
            bot_id = self.next_id
            self.next_id += 1
            bot = {
                "id": bot_id,
                "user_id": user_id,
                "name": name,
                "config": config,
                "status": "stopped",
                "created_at": "2023-01-01T00:00:00Z",
            }
            self.bots[bot_id] = bot
            return bot

        async def get_bot_by_id(self, bot_id: int):
            return self.bots.get(bot_id)

        async def get_bots_by_user_id(self, user_id: int):
            return [bot for bot in self.bots.values() if bot["user_id"] == user_id]

        async def update_bot_status(self, bot_id: int, status: str):
            if bot_id in self.bots:
                self.bots[bot_id]["status"] = status
                return self.bots[bot_id]
            return None

        async def delete_bot(self, bot_id: int):
            return self.bots.pop(bot_id, None)

    return MockBotRepository()


@pytest_asyncio.fixture
async def client(db_session):
    """Provide test client with database session override and proper dependency injection"""
    from server_fastapi.database import get_db_session
    from server_fastapi.dependencies.bots import (
        get_bot_service,
        get_bot_trading_service,
    )
    from server_fastapi.main import app
    from server_fastapi.services.trading.bot_service import BotService
    from server_fastapi.services.trading.bot_trading_service import BotTradingService

    # Override database dependency
    async def override_get_db():
        yield db_session

    # Override bot service dependencies to use test database session
    async def override_get_bot_service():
        return BotService(db_session=db_session)

    async def override_get_bot_trading_service():
        return BotTradingService(session=db_session)

    # Configure test-specific rate limiting (high limits for tests)
    # This allows rate limiting logic to be tested without blocking tests
    # Set test-specific high limits that won't block tests but still validate logic
    test_limits = {
        "authenticated": {"limit": 100000, "window": 3600},  # Very high for tests
        "anonymous": {"limit": 100000, "window": 3600},  # Very high for tests
    }

    # Update RateLimitMiddleware default limits for tests
    for middleware in app.user_middleware:
        if (
            hasattr(middleware, "cls")
            and middleware.cls.__name__ == "RateLimitMiddleware"
        ):
            # Get the middleware instance
            middleware_instance = None
            for mw in app.middleware_stack:
                if (
                    hasattr(mw, "__class__")
                    and mw.__class__.__name__ == "RateLimitMiddleware"
                ):
                    middleware_instance = mw
                    break

            if middleware_instance:
                # Override default limits for tests
                middleware_instance.default_limits = test_limits
                # Also update endpoint limits to be high for tests
                for endpoint in middleware_instance.endpoint_limits:
                    middleware_instance.endpoint_limits[endpoint] = {
                        "limit": 100000,
                        "window": 3600,
                    }
                logger.debug("Test-specific rate limits configured")

    # Also configure SlowAPI limiter if available
    if hasattr(app, "state") and hasattr(app.state, "limiter"):
        # SlowAPI limiter - set high test limits
        app.state.limiter.enabled = True  # Keep enabled for logic testing
        # Note: SlowAPI limits are set per-route, so we keep them enabled
        # but they should be high enough not to block tests

    # Apply all overrides
    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_bot_service] = override_get_bot_service
    app.dependency_overrides[get_bot_trading_service] = override_get_bot_trading_service

    # Use ASGITransport for newer httpx versions
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client

    # Clean up overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def test_bot_data():
    """Sample bot data for testing"""
    import json

    return {
        "name": "Test Bot",
        "symbol": "ETH/USDC",
        "strategy": "ml_adaptive",
        "parameters": json.dumps(
            {  # JSON string for Bot model
                "risk_level": "medium",
                "position_size": 0.1,
                "stop_loss": 0.02,
                "take_profit": 0.05,
            }
        ),
        "config": {  # Keep for API compatibility
            "risk_level": "medium",
            "position_size": 0.1,
            "stop_loss": 0.02,
            "take_profit": 0.05,
        },
    }


@pytest_asyncio.fixture
async def created_bot(client: AsyncClient, test_bot_data):
    """Create a bot for testing"""
    response = await client.post("/api/bots/", json=test_bot_data)
    if response.status_code == 201:
        return response.json()
    return None


@pytest_asyncio.fixture
async def auth_headers(client, db_session, test_engine, test_db_setup):
    """Provide authentication headers for tests with real JWT token using test database"""
    import uuid

    try:
        # Use the registration endpoint approach (like test_auth_integration.py)
        # This works with the normal registration route (shim removed January 3, 2026)
        unique_email = f"testuser-{uuid.uuid4().hex[:8]}@example.com"

        # Register a test user via API endpoint
        register_data = {
            "email": unique_email,
            "password": "TestPassword123!",
            "name": "Test User",
        }
        reg_response = await client.post("/api/auth/register", json=register_data)

        if reg_response.status_code != 200:
            # If registration fails, try login anyway (user might already exist)
            logger.warning(
                f"Registration returned {reg_response.status_code}: {reg_response.text}"
            )
        else:
            logger.debug(f"Successfully registered test user: {unique_email}")

        # Login to get token
        login_data = {"email": unique_email, "password": "TestPassword123!"}
        login_response = await client.post("/api/auth/login", json=login_data)

        if login_response.status_code != 200:
            error_text = (
                login_response.text
                if hasattr(login_response, "text")
                else str(login_response.json())
            )
            logger.warning(f"Login failed: {login_response.status_code} - {error_text}")
            # Fallback to mock token
            return {"Authorization": "Bearer test_token_mock"}

        response_data = login_response.json()
        # Support both old format (data.token) and new format (access_token)
        token = response_data.get("access_token") or response_data.get("data", {}).get(
            "token"
        )

        if not token:
            logger.warning(f"Token not found in response: {response_data}")
            return {"Authorization": "Bearer test_token_mock"}

        return {"Authorization": f"Bearer {token}"}
    except Exception as e:
        # Fallback to mock token if auth fails
        logger.warning(f"Auth setup failed, using mock token: {e}")
        return {"Authorization": "Bearer test_token_mock"}


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user in the database"""
    import uuid

    from server_fastapi.services.auth.auth_service import AuthService

    unique_email = f"testuser-{uuid.uuid4().hex[:8]}@example.com"
    auth_service = AuthService()

    try:
        user = await auth_service.register_user(
            email=unique_email, password="TestPassword123!", name="Test User"
        )
        return {
            "id": user.get("id") if isinstance(user, dict) else str(user),
            "email": unique_email,
            "name": "Test User",
        }
    except Exception as e:
        pytest.skip(f"User creation failed: {e}")
        return None


@pytest.fixture
def test_bot_config():
    """Standard test bot configuration"""
    return {
        "name": "Test Trading Bot",
        "symbol": "BTC/USDT",
        "strategy": "simple_ma",
        "config": {
            "max_position_size": 0.1,
            "stop_loss": 0.02,
            "take_profit": 0.05,
            "risk_per_trade": 0.01,
        },
    }


# Import test factories for easy access
@pytest.fixture
def factories():
    """Provide access to test data factories"""
    from .utils.test_factories import (
        BotFactory,
        PortfolioFactory,
        TradeFactory,
        UserFactory,
        WalletFactory,
    )

    return {
        "user": UserFactory,
        "bot": BotFactory,
        "wallet": WalletFactory,
        "trade": TradeFactory,
        "portfolio": PortfolioFactory,
    }


@pytest_asyncio.fixture
async def test_user_with_auth(db_session, factories):
    """Create a test user with authentication token"""
    user = await factories["user"].create_user(db_session)

    from server_fastapi.services.auth.auth_service import AuthService

    auth_service = AuthService(db_session=db_session)

    try:
        token_data = await auth_service.login_user(
            email=user["email"], password=user["password"]
        )
        user["token"] = token_data["token"]
        user["auth_headers"] = {"Authorization": f"Bearer {token_data['token']}"}
    except Exception as e:
        logger.warning(f"Failed to get auth token: {e}")
        user["token"] = None
        user["auth_headers"] = {}

    return user


@pytest_asyncio.fixture
async def admin_headers(client, db_session):
    """Provide authentication headers for admin user"""
    import uuid

    from server_fastapi.database import get_db_session
    from server_fastapi.main import app
    from server_fastapi.services.auth.auth_service import AuthService

    # Override database dependency for auth service
    async def override_get_db():
        yield db_session

    original_override = app.dependency_overrides.get(get_db_session)
    app.dependency_overrides[get_db_session] = override_get_db

    try:
        from datetime import datetime, timedelta

        import jwt

        from server_fastapi.config.settings import settings

        # Create an admin user using AuthService
        unique_email = f"admin-{uuid.uuid4().hex[:8]}@example.com"
        auth_service = AuthService()  # AuthService doesn't take db_session

        # Register admin user through the service
        result = auth_service.register(
            {
                "email": unique_email,
                "password": "AdminPassword123!",
                "name": "Admin User",
            }
        )

        user = result.get("user", {})

        # Restore original override
        if original_override:
            app.dependency_overrides[get_db_session] = original_override
        else:
            app.dependency_overrides.pop(get_db_session, None)

        # Create a JWT token with admin role manually
        # The require_permission checks for "roles" (plural) in the token payload
        user_id = user.get("id") or 1
        now = datetime.now(UTC)
        payload = {
            "id": user_id,
            "sub": str(user_id),  # Standard JWT claim
            "email": unique_email,
            "role": "admin",  # For backward compatibility
            "roles": ["admin"],  # Required for require_permission
            "permissions": ["admin:*"],  # Optional, but helpful
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "iat": int(now.timestamp()),
        }

        token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

        return {"Authorization": f"Bearer {token}"}
    except Exception as e:
        # Restore original override on error
        if original_override:
            app.dependency_overrides[get_db_session] = original_override
        else:
            app.dependency_overrides.pop(get_db_session, None)

        logger.warning(f"Admin auth setup failed: {e}")
        # Return a mock admin token for testing
        # Note: This won't work for routes that check the actual role from the token
        return {"Authorization": "Bearer admin_test_token_mock"}
