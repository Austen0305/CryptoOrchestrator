"""
Database configuration and connection management for PostgreSQL using async SQLAlchemy.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

# Database URL from environment variable
env_db_url = os.getenv("DATABASE_URL", "")
if not env_db_url or "user:pass@host:5432" in env_db_url:
    DATABASE_URL = "sqlite+aiosqlite:///./data/app.db"
else:
    DATABASE_URL = env_db_url

print(f"DEBUG: Resolved DATABASE_URL: {DATABASE_URL}")


# Test environment in-memory DB sharing fix:
# Pytest suite imports this module twice under different names (direct file spec import
# and package import). A plain `:memory:` SQLite DSN creates a separate, isolated
# database per engine, so tables created in one import aren't visible in the other,
# leading to "no such table" OperationalError during tests.
#
# To make the in-memory database shared across all engines within the same process,
# rewrite the URL to use a named shared memory database when we detect the
# `:memory:` pattern. The URI form `file:pytest_shared?mode=memory&cache=shared`
# enables multiple connections (and separate engine instances) to access the same
# transient DB.
if DATABASE_URL.endswith(":memory:"):
    # Preserve driver prefix, replace tail with shared memory URI form
    # Example input: sqlite+aiosqlite:///:memory:
    # Output:       sqlite+aiosqlite:///file:pytest_shared?mode=memory&cache=shared
    driver_prefix = DATABASE_URL.split(":///")[0]  # e.g. 'sqlite+aiosqlite'
    DATABASE_URL = f"{driver_prefix}:///file:pytest_shared?mode=memory&cache=shared"


# Create async engine with connection pooling
if DATABASE_URL.startswith("sqlite+"):
    # SQLite-specific configuration
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,  # Set to True for SQL query logging in development
        poolclass=StaticPool,  # Use static pool for SQLite
        connect_args={"check_same_thread": False},  # Needed for SQLite
    )
else:
    # PostgreSQL configuration with optimized pooling
    # Use environment variables for production tuning
    pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
    max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # 1 hour

    engine = create_async_engine(
        DATABASE_URL,
        echo=False,  # Set to True for SQL query logging in development
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=True,  # Verify connections before using (prevents stale connections)
        future=True,
    )

# Create async session factory
async_session = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for all database models
# Import from models.base to ensure consistency
try:
    from .models.base import Base
except ImportError:
    # Fallback if models.base doesn't exist yet
    Base = DeclarativeBase


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an AsyncSession and ensures proper cleanup.
    """
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
    """Initialize the database by creating all tables defined in the models.

    Ensures models are imported so that `Base.metadata` is populated, then creates
    any missing tables. Safe to call multiple times (idempotent for `create_all`).
    """
    # Import models to populate metadata (handles double-import test scenario)
    import logging

    log = logging.getLogger(__name__)
    # Attempt relative import (when running within package context)
    try:  # local import to avoid circulars at module import time
        from . import models  # type: ignore  # noqa: F401

        log.debug("Models imported via relative package path for metadata population")
    except Exception as e_rel:
        # Fallback to absolute import when invoked from a dynamically loaded module name
        try:
            from server_fastapi import models  # type: ignore  # noqa: F401

            log.debug(
                "Models imported via absolute package path for metadata population"
            )
        except Exception as e_abs:
            log.warning(
                f"Model import failed during init_database: relative={e_rel}; absolute={e_abs}"
            )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_database():
    """
    Close the database connection pool.
    Call this during application shutdown.
    """
    await engine.dispose()
