"""Database connection pool management with health checks and retry logic"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, QueuePool, StaticPool
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator
import os

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
        if database_url.startswith("sqlite://") and not database_url.startswith("sqlite+aiosqlite://"):
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
            logger.warning(f"Converted database URL to use aiosqlite driver: {database_url}")
        
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
        
        # Determine pool settings based on environment
        is_production = os.getenv("NODE_ENV") == "production"
        
        pool_config = {
            "pool_size": 20 if is_production else 5,
            "max_overflow": 10 if is_production else 2,
            "pool_timeout": 30,
            "pool_recycle": 3600,  # Recycle connections after 1 hour
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
            **({} if poolclass == StaticPool else (pool_config if poolclass == QueuePool else {}))
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
        """Get a database session with automatic cleanup"""
        if not self._is_initialized:
            raise RuntimeError("Database connection pool not initialized")
        
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()
    
    async def health_check(self) -> bool:
        """Check database connection health"""
        try:
            async with self.get_session() as session:
                await session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
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
