"""Database connection pool management with health checks and retry logic"""

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, QueuePool, StaticPool

logger = logging.getLogger(__name__)


class DatabaseConnectionPool:
    """Manages database connection pool with health checks and retry logic"""

    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._is_initialized = False

    def initialize(self, database_url: str):
        """Initialize database connection pool"""
        if self._is_initialized:
            logger.warning("Database connection pool already initialized")
            return

        # Ensure SQLite URLs use aiosqlite driver
        if database_url.startswith("sqlite://") and not database_url.startswith(
            "sqlite+aiosqlite://"
        ):
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
            logger.warning(
                f"Converted database URL to use aiosqlite driver: {database_url}"
            )

        # Verify aiosqlite is available for SQLite
        if database_url.startswith("sqlite+"):
            if "aiosqlite" not in database_url:
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

        # Use settings for pool configuration
        from ..config.settings import settings

        is_production = os.getenv("NODE_ENV") == "production"

        pool_config = {
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "pool_timeout": settings.db_pool_timeout,
            "pool_recycle": settings.db_pool_recycle,
            "pool_pre_ping": True,  # Verify connections before using
        }

        # Use NullPool for testing, StaticPool for SQLite, QueuePool for production PostgreSQL
        if database_url.startswith("sqlite+"):
            poolclass = StaticPool
            pool_config = {"check_same_thread": False}
        else:
            poolclass = NullPool if os.getenv("TESTING") else QueuePool

        self.engine = create_async_engine(
            database_url,
            echo=not is_production,
            poolclass=poolclass,
            connect_args=pool_config if poolclass == StaticPool else {},
            **(
                {}
                if poolclass == StaticPool
                else (pool_config if poolclass == QueuePool else {})
            ),
        )

        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        self._is_initialized = True
        logger.info("Database connection pool initialized successfully")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session with automatic cleanup and proper error handling"""
        if not self._is_initialized:
            raise RuntimeError("Database connection pool not initialized")

        session = self.session_factory()
        try:
            yield session
            try:
                await session.commit()
            except Exception as commit_error:
                logger.error(f"Database commit error: {commit_error}")
                await session.rollback()
                raise
        except Exception as e:
            try:
                await session.rollback()
            except Exception as rollback_error:
                logger.error(f"Database rollback error: {rollback_error}")
            logger.error(f"Database session error: {e}")
            raise
        finally:
            try:
                await session.close()
            except Exception as close_error:
                logger.error(f"Database session close error: {close_error}")

    async def health_check(self) -> bool:
        """Check database connection health"""
        if not self._is_initialized or not self.engine:
            logger.warning("Database pool not initialized, health check cannot proceed")
            return False
        try:
            from sqlalchemy import text

            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                result.scalar()  # Verify we got a result
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}", exc_info=True)
            return False

    async def get_pool_status(self) -> dict:
        """Get detailed pool status information"""
        if not self._is_initialized or not self.engine:
            return {
                "initialized": False,
                "pool_size": 0,
                "checked_in": 0,
                "checked_out": 0,
                "overflow": 0,
            }

        try:
            pool = self.engine.pool
            status = {
                "initialized": True,
            }

            # Get pool statistics if available (these are attributes, not methods)
            status["pool_size"] = getattr(pool, "size", None)
            status["checked_in"] = getattr(pool, "checkedin", None)
            status["checked_out"] = getattr(pool, "checkedout", None)
            status["overflow"] = getattr(pool, "overflow", None)
            status["invalid"] = getattr(pool, "invalid", None)

            # Add pool class name
            status["pool_class"] = pool.__class__.__name__

            return status
        except Exception as e:
            logger.warning(f"Error getting pool status: {e}")
            return {
                "initialized": True,
                "error": str(e),
            }

    async def close(self):
        """Close all database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")
            self._is_initialized = False


# Global connection pool instance
db_pool = DatabaseConnectionPool()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI routes"""
    async with db_pool.get_session() as session:
        yield session
