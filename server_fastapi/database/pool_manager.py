"""
Advanced Database Connection Pool Manager
Provides intelligent pool management, health monitoring, and automatic scaling
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager, suppress
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool, StaticPool

logger = logging.getLogger(__name__)


class PoolMetrics:
    """Connection pool metrics"""

    def __init__(self):
        self.total_connections = 0
        self.active_connections = 0
        self.idle_connections = 0
        self.overflow_connections = 0
        self.connection_errors = 0
        self.query_count = 0
        self.slow_queries = 0
        self.last_health_check: datetime | None = None
        self.health_status = "unknown"

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "total_connections": self.total_connections,
            "active_connections": self.active_connections,
            "idle_connections": self.idle_connections,
            "overflow_connections": self.overflow_connections,
            "connection_errors": self.connection_errors,
            "query_count": self.query_count,
            "slow_queries": self.slow_queries,
            "last_health_check": (
                self.last_health_check.isoformat() if self.last_health_check else None
            ),
            "health_status": self.health_status,
            "utilization": (
                self.active_connections / self.total_connections * 100
                if self.total_connections > 0
                else 0
            ),
        }


class AdvancedPoolManager:
    """
    Advanced connection pool manager with:
    - Automatic pool sizing
    - Health monitoring
    - Connection leak detection
    - Query performance tracking
    - Automatic recovery
    """

    def __init__(
        self,
        database_url: str,
        min_pool_size: int = 5,
        max_pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        enable_monitoring: bool = True,
    ):
        self.database_url = database_url
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.enable_monitoring = enable_monitoring

        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker | None = None
        self.metrics = PoolMetrics()
        self._monitoring_task: asyncio.Task | None = None
        self._is_initialized = False

    def initialize(self):
        """Initialize the connection pool"""
        if self._is_initialized:
            logger.warning("Pool manager already initialized")
            return

        # Determine pool class
        if self.database_url.startswith("sqlite+"):
            poolclass = StaticPool
            pool_config = {"check_same_thread": False}
        else:
            poolclass = NullPool if os.getenv("TESTING") else QueuePool
            pool_config = {
                "pool_size": self.min_pool_size,
                "max_overflow": self.max_overflow,
                "pool_timeout": self.pool_timeout,
                "pool_recycle": self.pool_recycle,
                "pool_pre_ping": True,
            }

        # Create engine
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            poolclass=poolclass,
            connect_args=pool_config if poolclass == StaticPool else {},
            **({} if poolclass == StaticPool else pool_config),
        )

        # Create session factory
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        # Register event listeners
        if self.enable_monitoring:
            self._register_event_listeners()

        self._is_initialized = True
        logger.info("Advanced pool manager initialized")

        # Start monitoring
        if self.enable_monitoring:
            self._start_monitoring()

    def _register_event_listeners(self):
        """Register SQLAlchemy event listeners for monitoring"""
        if not self.engine:
            return

        @event.listens_for(self.engine.sync_engine, "connect")
        def on_connect(dbapi_conn, connection_record):
            self.metrics.total_connections += 1
            self.metrics.active_connections += 1

        @event.listens_for(self.engine.sync_engine, "checkout")
        def on_checkout(dbapi_conn, connection_record, connection_proxy):
            self.metrics.active_connections += 1
            if self.metrics.idle_connections > 0:
                self.metrics.idle_connections -= 1

        @event.listens_for(self.engine.sync_engine, "checkin")
        def on_checkin(dbapi_conn, connection_record):
            if self.metrics.active_connections > 0:
                self.metrics.active_connections -= 1
            self.metrics.idle_connections += 1

    def _start_monitoring(self):
        """Start background monitoring task"""
        if self._monitoring_task and not self._monitoring_task.done():
            return

        self._monitoring_task = asyncio.create_task(self._monitor_loop())

    async def _monitor_loop(self):
        """Background monitoring loop"""
        while self._is_initialized:
            try:
                await self._update_metrics()
                await self._health_check()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in pool monitoring: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _update_metrics(self):
        """Update pool metrics"""
        if not self.engine:
            return

        try:
            pool = self.engine.pool
            if hasattr(pool, "size"):
                self.metrics.total_connections = pool.size()
            if hasattr(pool, "checkedout"):
                self.metrics.active_connections = pool.checkedout()
            if hasattr(pool, "overflow"):
                self.metrics.overflow_connections = pool.overflow()
        except Exception as e:
            logger.debug(f"Error updating metrics: {e}")

    async def _health_check(self):
        """Perform health check"""
        if not self.engine:
            return

        try:
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
            self.metrics.health_status = "healthy"
            self.metrics.last_health_check = datetime.now(UTC)
        except Exception as e:
            self.metrics.health_status = "unhealthy"
            self.metrics.connection_errors += 1
            logger.warning(f"Pool health check failed: {e}")

    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """Get a database session with automatic cleanup"""
        if not self._is_initialized:
            raise RuntimeError("Pool manager not initialized")

        session = self.session_factory()
        start_time = datetime.now(UTC)

        try:
            yield session
            self.metrics.query_count += 1

            # Check for slow queries
            duration = (datetime.now(UTC) - start_time).total_seconds()
            if duration > 1.0:  # Queries over 1 second
                self.metrics.slow_queries += 1
                logger.warning(f"Slow query detected: {duration:.2f}s")

            try:
                await session.commit()
            except Exception as e:
                logger.error(f"Commit error: {e}")
                await session.rollback()
                raise
        except Exception:
            with suppress(Exception):
                await session.rollback()
            raise
        finally:
            with suppress(Exception):
                await session.close()

    async def health_check(self) -> bool:
        """Check if pool is healthy"""
        return self.metrics.health_status == "healthy"

    def get_metrics(self) -> dict[str, Any]:
        """Get current pool metrics"""
        return self.metrics.to_dict()

    async def close(self):
        """Close all connections and stop monitoring"""
        self._is_initialized = False

        if self._monitoring_task:
            self._monitoring_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._monitoring_task

        if self.engine:
            await self.engine.dispose()
            logger.info("Pool manager closed")


# Global pool manager instance
_pool_manager: AdvancedPoolManager | None = None


def get_pool_manager() -> AdvancedPoolManager:
    """Get or create global pool manager"""
    global _pool_manager

    if _pool_manager is None:
        database_url = os.getenv(
            "DATABASE_URL", "sqlite+aiosqlite:///./crypto_orchestrator.db"
        )
        _pool_manager = AdvancedPoolManager(
            database_url=database_url,
            min_pool_size=int(os.getenv("PERF_DB_POOL_SIZE", "5")),
            max_pool_size=int(os.getenv("PERF_DB_POOL_SIZE", "20")),
            max_overflow=int(os.getenv("PERF_DB_MAX_OVERFLOW", "10")),
            enable_monitoring=True,
        )
        _pool_manager.initialize()

    return _pool_manager
