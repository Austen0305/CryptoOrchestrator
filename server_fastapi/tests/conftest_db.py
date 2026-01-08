"""
Database test isolation fixtures for pytest.
Provides isolated test databases using PostgreSQL or SQLite.
"""

import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, StaticPool

from server_fastapi.database import Base

# Database configuration
TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///file:pytest_test_db?mode=memory&cache=shared",
)

# Track if we're using PostgreSQL
USE_POSTGRES = TEST_DB_URL.startswith("postgresql")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_engine():
    """Create isolated test database engine."""
    if USE_POSTGRES:
        # PostgreSQL: Create a temporary database
        from sqlalchemy import create_engine, text

        # Extract base connection URL (without database name)
        base_url = TEST_DB_URL.rsplit("/", 1)[0] + "/postgres"
        admin_engine = create_engine(base_url.replace("+asyncpg", ""))

        # Create temporary database
        test_db_name = f"test_cryptoorchestrator_{os.getpid()}"

        with admin_engine.connect() as conn:
            conn.execute(text("COMMIT"))
            conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
            conn.execute(text(f"CREATE DATABASE {test_db_name}"))
            conn.commit()

        admin_engine.dispose()

        # Create async engine for test database
        test_url = f"{TEST_DB_URL.rsplit('/', 1)[0]}/{test_db_name}"
        engine = create_async_engine(
            test_url,
            poolclass=NullPool,
            echo=False,  # No pooling for tests
        )
    else:
        # SQLite: Use in-memory database
        engine = create_async_engine(
            TEST_DB_URL,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=False,
        )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()

    if USE_POSTGRES:
        # Drop temporary database
        base_url = TEST_DB_URL.rsplit("/", 1)[0] + "/postgres"
        admin_engine = create_engine(base_url.replace("+asyncpg", ""))
        with admin_engine.connect() as conn:
            conn.execute(text("COMMIT"))
            conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
            conn.commit()
        admin_engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create isolated database session for each test."""
    async_session = async_sessionmaker(
        bind=test_db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Begin transaction
        await session.begin()

        yield session

        # Rollback transaction to clean up
        await session.rollback()
        await session.close()


@pytest.fixture(scope="function")
async def db_session(test_db_session):
    """Alias for test_db_session to match FastAPI dependency name."""
    return test_db_session


@pytest.fixture(scope="function")
async def clean_db(test_db_session):
    """Ensure database is clean before test."""
    # Drop all tables
    async with test_db_session.bind.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield test_db_session


def pytest_configure(config):
    """Configure pytest with database markers."""
    config.addinivalue_line("markers", "db: mark test as requiring database")
    config.addinivalue_line("markers", "integration: mark test as integration test")


@pytest.fixture(autouse=True)
async def auto_clean_tables(test_db_session):
    """Automatically clean tables after each test."""
    yield
    # Cleanup happens in test_db_session fixture
    pass
