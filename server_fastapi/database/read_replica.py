"""
Read Replica Support
Enables read/write splitting for improved database performance.
"""

import logging
from typing import Optional, AsyncGenerator, Dict, Any
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.pool import QueuePool, StaticPool
from contextlib import asynccontextmanager
import os

logger = logging.getLogger(__name__)


class ReadReplicaManager:
    """
    Manages read replica connections for read/write splitting
    """

    def __init__(self):
        self.write_engine: Optional[AsyncEngine] = None
        self.read_engines: list[AsyncEngine] = []
        self.read_session_factories: list[async_sessionmaker] = []
        self.current_read_index = 0
        self._is_initialized = False

    def initialize(self, write_url: str, read_urls: Optional[list[str]] = None) -> None:
        """
        Initialize read replica manager

        Args:
            write_url: Primary database URL for writes
            read_urls: List of read replica URLs (optional, defaults to write_url)
        """
        if self._is_initialized:
            logger.warning("Read replica manager already initialized")
            return

        from ..config.settings import settings

        # Initialize write engine (primary)
        self.write_engine = self._create_engine(write_url, settings, is_write=True)
        logger.info("Write engine (primary) initialized")

        # Initialize read replicas
        if read_urls:
            for i, read_url in enumerate(read_urls):
                read_engine = self._create_engine(read_url, settings, is_write=False)
                self.read_engines.append(read_engine)

                read_session_factory = async_sessionmaker(
                    read_engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autocommit=False,
                    autoflush=False,
                )
                self.read_session_factories.append(read_session_factory)

                logger.info(
                    f"Read replica {i+1} initialized: {read_url.split('@')[1] if '@' in read_url else read_url}"
                )
        else:
            # No read replicas configured, use write engine for reads too
            logger.info("No read replicas configured, using primary for reads")

        self._is_initialized = True

    def _create_engine(
        self, database_url: str, settings: Any, is_write: bool = False
    ) -> AsyncEngine:
        """Create async engine with appropriate configuration"""
        # Ensure async drivers
        if database_url.startswith("sqlite://") and not database_url.startswith(
            "sqlite+aiosqlite://"
        ):
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

        if database_url.startswith("postgresql://") and not database_url.startswith(
            "postgresql+asyncpg://"
        ):
            import re

            database_url = re.sub(
                r"^postgresql://", "postgresql+asyncpg://", database_url
            )

        is_production = os.getenv("NODE_ENV") == "production"

        # Pool configuration
        if database_url.startswith("sqlite+"):
            poolclass = StaticPool
            pool_config = {"check_same_thread": False}
        else:
            poolclass = QueuePool
            pool_config = {
                "pool_size": settings.db_pool_size,
                "max_overflow": settings.db_max_overflow,
                "pool_timeout": settings.db_pool_timeout,
                "pool_recycle": settings.db_pool_recycle,
                "pool_pre_ping": True,
            }

        engine = create_async_engine(
            database_url,
            echo=not is_production,
            poolclass=poolclass,
            connect_args=pool_config if poolclass == StaticPool else {},
            **(
                {}
                if poolclass == StaticPool
                else pool_config if poolclass == QueuePool else {}
            ),
        )

        return engine

    @asynccontextmanager
    async def get_read_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a read session from a read replica (round-robin)

        Yields:
            AsyncSession from a read replica
        """
        if not self._is_initialized:
            raise RuntimeError("Read replica manager not initialized")

        # Use read replica if available, otherwise use write engine
        if self.read_session_factories:
            # Round-robin selection
            session_factory = self.read_session_factories[self.current_read_index]
            self.current_read_index = (self.current_read_index + 1) % len(
                self.read_session_factories
            )
        else:
            # Fallback to write engine if no replicas
            from ..database.connection_pool import db_pool

            if not db_pool._is_initialized:
                raise RuntimeError("Database connection pool not initialized")
            session_factory = db_pool.session_factory

        session = session_factory()
        try:
            yield session
            # Read sessions don't need commit, but ensure proper cleanup
        except Exception as e:
            try:
                await session.rollback()
            except Exception as rollback_error:
                logger.error(f"Read session rollback error: {rollback_error}")
            logger.error(f"Read session error: {e}", exc_info=True)
            raise
        finally:
            try:
                await session.close()
            except Exception as close_error:
                logger.error(f"Read session close error: {close_error}")

    @asynccontextmanager
    async def get_write_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a write session from the primary database

        Yields:
            AsyncSession from the primary database
        """
        if not self._is_initialized:
            raise RuntimeError("Read replica manager not initialized")

        # Use write engine
        from ..database.connection_pool import db_pool

        if not db_pool._is_initialized:
            raise RuntimeError("Database connection pool not initialized")

        session = db_pool.session_factory()
        try:
            yield session
            try:
                await session.commit()
            except Exception as commit_error:
                logger.error(f"Write session commit error: {commit_error}")
                await session.rollback()
                raise
        except Exception as e:
            try:
                await session.rollback()
            except Exception as rollback_error:
                logger.error(f"Write session rollback error: {rollback_error}")
            logger.error(f"Write session error: {e}", exc_info=True)
            raise
        finally:
            try:
                await session.close()
            except Exception as close_error:
                logger.error(f"Write session close error: {close_error}")

    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of all database connections

        Returns:
            Dictionary with health status for write and read replicas
        """
        health_status = {"write": False, "read_replicas": []}

        # Check write engine
        if self.write_engine:
            try:
                async with self.get_write_session() as session:
                    await session.execute("SELECT 1")
                health_status["write"] = True
            except Exception as e:
                logger.error(f"Write engine health check failed: {e}")

        # Check read replicas
        for i, engine in enumerate(self.read_engines):
            try:
                async with self.get_read_session() as session:
                    await session.execute("SELECT 1")
                health_status["read_replicas"].append(True)
            except Exception as e:
                logger.error(f"Read replica {i} health check failed: {e}")
                health_status["read_replicas"].append(False)

        return health_status

    async def close(self) -> None:
        """Close all database connections"""
        if self.write_engine:
            await self.write_engine.dispose()

        for engine in self.read_engines:
            await engine.dispose()

        self._is_initialized = False
        logger.info("Read replica connections closed")


# Global read replica manager instance
read_replica_manager = ReadReplicaManager()
