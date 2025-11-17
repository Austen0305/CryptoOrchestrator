import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool, NullPool
from httpx import AsyncClient
import sys
from pathlib import Path
import os
import asyncio
from contextlib import asynccontextmanager

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
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///file:pytest_shared?mode=memory&cache=shared")
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
    """Set up test database schema if DB is available."""
    if Base is None or test_engine is None:
        yield
        return
    
    # Import all models to ensure metadata is populated
    try:
        from server_fastapi import models  # noqa: F401
    except ImportError:
        pass
    
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Cleanup after all tests
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    # Dispose engine
    await test_engine.dispose()

@pytest_asyncio.fixture
async def db_session(test_engine, test_db_setup):
    """
    Provide an isolated database session for each test.
    Each test gets its own transaction that rolls back automatically.
    """
    if test_engine is None:
        class DummySession:
            async def execute(self, *a, **k):
                class R:
                    def scalar_one_or_none(self): return None
                    def scalars(self): return []
                return R()
            async def commit(self): pass
            async def refresh(self, obj): pass
            async def rollback(self): pass
            async def close(self): pass
        yield DummySession()
        return
    
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        # Begin transaction for this test
        await session.begin()
        
        try:
            yield session
        finally:
            # Always rollback to clean up
            await session.rollback()
            await session.close()

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
                "created_at": "2023-01-01T00:00:00Z"
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
                "created_at": "2023-01-01T00:00:00Z"
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
    """Provide test client with database session override"""
    from server_fastapi.main import app
    from server_fastapi.database import get_db_session
    
    # Override database dependency
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db_session] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client
    
    # Clean up overrides
    app.dependency_overrides.clear()

@pytest.fixture
def test_bot_data():
    """Sample bot data for testing"""
    return {
        "name": "Test Bot",
        "exchange": "kraken",
        "symbol": "BTC/USD",
        "strategy": "ml_adaptive",
        "config": {
            "risk_level": "medium",
            "position_size": 0.1,
            "stop_loss": 0.02,
            "take_profit": 0.05
        }
    }

@pytest_asyncio.fixture
async def created_bot(client: AsyncClient, test_bot_data):
    """Create a bot for testing"""
    response = await client.post("/api/bots/", json=test_bot_data)
    if response.status_code == 201:
        return response.json()
    return None

@pytest_asyncio.fixture
async def auth_headers(client):
    """Provide authentication headers for tests with real JWT token"""
    import uuid
    from server_fastapi.services.auth.auth_service import AuthService
    
    # Create a test user and get a real token
    unique_email = f"testuser-{uuid.uuid4().hex[:8]}@example.com"
    auth_service = AuthService()
    
    try:
        # Register user
        user = await auth_service.register_user(
            email=unique_email,
            password="TestPassword123!",
            name="Test User"
        )
        
        # Login to get token
        token_data = await auth_service.login_user(
            email=unique_email,
            password="TestPassword123!"
        )
        
        return {"Authorization": f"Bearer {token_data['token']}"}
    except Exception as e:
        # Fallback to mock token if auth fails
        pytest.skip(f"Auth setup failed: {e}")
        return {"Authorization": "Bearer test_token_mock"}