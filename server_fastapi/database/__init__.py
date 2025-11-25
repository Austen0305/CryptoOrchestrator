"""Unified database package interface.

This package now provides the same API surface as the previous `database.py`
module (init_database, close_database, get_db_session, Base, async_session) so
that imports using either `server_fastapi.database` forms resolve consistently.
It ensures shared in-memory SQLite across duplicated imports during pytest.
"""

from typing import AsyncIterator, Any, AsyncGenerator
from contextlib import asynccontextmanager
import os
import sys
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool
import logging

logger = logging.getLogger(__name__)

# Resolve and normalize database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/app.db")
if DATABASE_URL.endswith(":memory:"):
    # Use shared memory URI to allow multiple engine instances to see same DB
    driver_prefix = DATABASE_URL.split(":///")[0]
    DATABASE_URL = f"{driver_prefix}:///file:pytest_shared?mode=memory&cache=shared"

# Engine creation (support SQLite + Postgres conventions similar to database.py)
if DATABASE_URL.startswith("sqlite+"):
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        future=True,
    )
else:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600,
        future=True,
    )

async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Canonical module aliasing (so test dynamic import and package import share objects)
if __name__ != "server_fastapi.database":
    sys.modules["server_fastapi.database"] = sys.modules[__name__]

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an AsyncSession with proper cleanup."""
    async with async_session() as session:
        yield session

@asynccontextmanager
async def get_db_context():
    """
    Context manager for getting database session outside of FastAPI dependency injection.
    Use this when you need to manually manage database sessions in services.
    
    Usage:
        async with get_db_context() as session:
            # use session
    """
    async with async_session() as session:
        yield session

async def init_database():
    """Populate metadata and create all tables (idempotent)."""
    # Import models via absolute path to ensure availability regardless of import style
    try:
        from server_fastapi import models  # noqa: F401
    except Exception as e:
        logger.warning(f"Model import failed during init_database (package): {e}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_database():
    """Dispose engine connections."""
    await engine.dispose()

__all__ = [
    "DATABASE_URL",
    "engine",
    "async_session",
    "Base",
    "get_db_session",
    "get_db_context",
    "init_database",
    "close_database",
]

