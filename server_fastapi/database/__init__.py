"""Unified database package interface.

This package now provides the same API surface as the previous `database.py`
module (init_database, close_database, get_db_session, Base, async_session) so
that imports using either `server_fastapi.database` forms resolve consistently.
It ensures shared in-memory SQLite across duplicated imports during pytest.
"""

import logging
import os
import sys
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

# Resolve and normalize database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/app.db")

# Ensure SQLite URLs use aiosqlite driver (not pysqlite)
if DATABASE_URL.startswith("sqlite://") and not DATABASE_URL.startswith(
    "sqlite+aiosqlite://"
):
    # Convert sqlite:// to sqlite+aiosqlite:// for async support
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)
    logger.warning(f"Converted database URL to use aiosqlite driver: {DATABASE_URL}")

# Auto-convert PostgreSQL URLs to asyncpg for async SQLAlchemy (e.g., Neon connection strings)
if DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith(
    "postgresql+asyncpg://"
):
    import re

    # Convert postgresql:// to postgresql+asyncpg:// for async support
    original_url = DATABASE_URL
    DATABASE_URL = re.sub(r"^postgresql://", "postgresql+asyncpg://", DATABASE_URL)

    # Remove channel_binding parameter as it may cause issues with async drivers
    if "channel_binding" in DATABASE_URL:
        DATABASE_URL = re.sub(r"[&?]channel_binding=[^&]*", "", DATABASE_URL)
        DATABASE_URL = DATABASE_URL.rstrip("&")
        # Clean up double ? or trailing &
        DATABASE_URL = re.sub(r"\?&", "?", DATABASE_URL)

    logger.info("Auto-converted PostgreSQL URL to async format for async SQLAlchemy")
    logger.debug("Original: %s@...", original_url.split("@")[0])
    logger.debug("Converted: %s@...", DATABASE_URL.split("@")[0])

if DATABASE_URL.endswith(":memory:"):
    # Use shared memory URI to allow multiple engine instances to see same DB
    driver_prefix = DATABASE_URL.split(":///")[0]
    DATABASE_URL = f"{driver_prefix}:///file:pytest_shared?mode=memory&cache=shared"

# Lazy engine creation - only create when actually needed
# This prevents blocking router loading if database driver is misconfigured
_engine = None
_async_session_factory = None


def _get_engine():  # type: ignore
    """Lazy engine creation - only creates engine when first needed"""
    global _engine
    if _engine is None:
        try:
            # Verify aiosqlite is available for SQLite databases
            if DATABASE_URL.startswith("sqlite+"):
                if "aiosqlite" not in DATABASE_URL:
                    raise ValueError(
                        "SQLite database requires aiosqlite driver. "
                        "Install with: pip install aiosqlite"
                    )
                # Try to import aiosqlite to verify it's installed
                try:
                    import aiosqlite  # noqa: F401
                except ImportError:
                    raise ImportError(
                        "aiosqlite is required for async SQLite support. "
                        "Install with: pip install aiosqlite"
                    )

                _engine = create_async_engine(
                    DATABASE_URL,
                    echo=False,
                    poolclass=StaticPool,
                    connect_args={"check_same_thread": False},
                    future=True,
                )
            else:
                # Use settings for pool configuration
                try:
                    from ..config.settings import Settings

                    settings = Settings()
                    _engine = create_async_engine(
                        DATABASE_URL,
                        echo=False,
                        pool_size=settings.db_pool_size,
                        max_overflow=settings.db_max_overflow,
                        pool_timeout=settings.db_pool_timeout,
                        pool_recycle=settings.db_pool_recycle,
                        pool_pre_ping=True,  # Verify connections before using
                        future=True,
                    )
                except ImportError:
                    # Fallback if settings not available
                    _engine = create_async_engine(
                        DATABASE_URL,
                        echo=False,
                        pool_size=20,
                        max_overflow=10,
                        pool_timeout=30,
                        pool_recycle=3600,
                        pool_pre_ping=True,
                        future=True,
                    )
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise
    return _engine


def _get_async_session():  # type: ignore
    """Lazy session factory creation"""
    global _async_session_factory
    if _async_session_factory is None:
        engine = _get_engine()
        _async_session_factory = async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )
    return _async_session_factory


# Create engine and session lazily - wrap in try/except to allow module to load even if database fails
try:
    # Try to create engine immediately for backward compatibility
    # But catch errors so module can still be imported
    if DATABASE_URL.startswith("sqlite+"):
        # Verify aiosqlite is available
        if "aiosqlite" not in DATABASE_URL:
            raise ValueError(
                "SQLite database requires aiosqlite driver. "
                "Install with: pip install aiosqlite"
            )
        try:
            import aiosqlite  # noqa: F401
        except ImportError:
            raise ImportError(
                "aiosqlite is required for async SQLite support. "
                "Install with: pip install aiosqlite"
            )

        engine = create_async_engine(
            DATABASE_URL,
            echo=False,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            future=True,
        )
    else:
        # Use settings for pool configuration
        try:
            from ..config.settings import Settings

            settings = Settings()
            engine = create_async_engine(
                DATABASE_URL,
                echo=False,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_timeout=settings.db_pool_timeout,
                pool_recycle=settings.db_pool_recycle,
                pool_pre_ping=True,  # Verify connections before using
                future=True,
            )
        except ImportError:
            # Fallback if settings not available
            engine = create_async_engine(
                DATABASE_URL,
                echo=False,
                pool_size=20,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping=True,
                future=True,
            )
    async_session = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
except Exception as e:
    # If engine creation fails, set to None and use lazy creation
    logger.warning(
        f"Database engine creation failed at module load: {e}. Will use lazy initialization."
    )
    engine = None
    async_session = None

try:
    # Prefer the application's canonical Base if available so models and engine
    # share the same metadata. This avoids duplicate table definitions and
    # mismatched schemas between `models` and `database`.
    from server_fastapi.models.base import Base as ModelsBase

    Base = ModelsBase
except Exception:
    # Fallback to local declarative base if models package isn't importable
    Base = declarative_base()

# Canonical module aliasing (so test dynamic import and package import share objects)
if __name__ != "server_fastapi.database":
    sys.modules["server_fastapi.database"] = sys.modules[__name__]


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an AsyncSession with proper cleanup."""
    session_factory = _get_async_session() if async_session is None else async_session
    session = session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


@asynccontextmanager
async def get_db_context():
    """
    Context manager for getting database session outside of FastAPI dependency injection.
    Use this when you need to manually manage database sessions in services.

    Usage:
        async with get_db_context() as session:
            # use session
    """
    session_factory = _get_async_session() if async_session is None else async_session
    session = session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_database():  # type: ignore
    """Populate metadata and create all tables (idempotent)."""
    # Import models via absolute path to ensure availability regardless of import style
    try:
        from server_fastapi import models  # noqa: F401
    except Exception as e:
        logger.warning(f"Model import failed during init_database (package): {e}")
    db_engine = _get_engine() if engine is None else engine
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_database():  # type: ignore
    """Dispose engine connections."""
    db_engine = _get_engine() if engine is None else engine
    await db_engine.dispose()


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

# Optional connection pool object used by advanced health checks. Set to None by
# default so imports like `from server_fastapi.database import db_pool` succeed
# during tests and when a dedicated pool manager isn't configured.
db_pool = None

__all__.append("db_pool")
