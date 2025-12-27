"""
Test Database Fixtures
Provides reusable database fixtures for E2E tests
Updated: December 6, 2025
"""

import os
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///./test_e2e.db")


async def create_test_database():
    """Create and initialize test database"""
    from server_fastapi.database import Base, init_database

    # Create engine for test database
    if TEST_DATABASE_URL.startswith("sqlite+"):
        engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
    else:
        engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
        )

    # Initialize database (creates tables)
    await init_database()

    return engine


async def cleanup_test_database(engine):
    """Clean up test database"""
    await engine.dispose()

    # Remove test database file if SQLite
    if TEST_DATABASE_URL.startswith("sqlite+"):
        db_path = TEST_DATABASE_URL.replace("sqlite+aiosqlite:///./", "")
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass  # Ignore cleanup errors
