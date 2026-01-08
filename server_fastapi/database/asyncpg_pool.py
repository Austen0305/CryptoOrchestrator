"""AsyncPG connection pool for high-performance database queries

This module provides a direct asyncpg connection pool for hot path queries
that need maximum performance. SQLAlchemy is still used for complex queries,
migrations, and ORM features, but asyncpg provides 30-50% faster performance
for simple, high-frequency queries.
"""

import logging
from urllib.parse import parse_qs, urlparse

import asyncpg

logger = logging.getLogger(__name__)


class AsyncPGPool:
    """Manages asyncpg connection pool for high-performance queries"""

    _pool: asyncpg.Pool | None = None
    _is_initialized: bool = False

    @classmethod
    async def create_pool(
        cls,
        database_url: str,
        min_size: int = 5,
        max_size: int = 20,
        command_timeout: int = 30,
    ) -> asyncpg.Pool:
        """Create asyncpg connection pool from SQLAlchemy-style database URL"""
        if cls._is_initialized:
            logger.warning("AsyncPG pool already initialized")
            return cls._pool

        # Convert SQLAlchemy URL to asyncpg format
        # Handle both postgresql:// and postgresql+asyncpg:// formats
        if "+asyncpg" in database_url:
            pg_url = database_url.replace("+asyncpg", "")
        elif database_url.startswith("postgresql://"):
            pg_url = database_url
        elif database_url.startswith("postgresql+psycopg2://"):
            pg_url = database_url.replace("+psycopg2", "")
        else:
            # Try to parse and convert
            parsed = urlparse(database_url)
            if parsed.scheme.startswith("postgresql"):
                pg_url = (
                    database_url.split("+")[0] if "+" in database_url else database_url
                )
            else:
                raise ValueError(f"Unsupported database URL format: {database_url}")

        # Parse connection parameters
        parsed = urlparse(pg_url)
        query_params = parse_qs(parsed.query)

        # Build connection parameters for asyncpg
        connection_params = {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "user": parsed.username,
            "password": parsed.password,
            "database": parsed.path.lstrip("/") if parsed.path else None,
            "min_size": min_size,
            "max_size": max_size,
            "command_timeout": command_timeout,
        }

        # Add SSL mode if specified
        if "sslmode" in query_params:
            connection_params["ssl"] = query_params["sslmode"][0]

        # Remove None values
        connection_params = {
            k: v for k, v in connection_params.items() if v is not None
        }

        try:
            cls._pool = await asyncpg.create_pool(**connection_params)
            cls._is_initialized = True
            logger.info(
                f"AsyncPG pool created: min={min_size}, max={max_size}, "
                f"database={connection_params.get('database', 'unknown')}"
            )
            return cls._pool
        except Exception as e:
            logger.error(f"Failed to create AsyncPG pool: {e}")
            raise

    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        """Get the asyncpg connection pool"""
        if cls._pool is None or not cls._is_initialized:
            raise RuntimeError(
                "AsyncPG pool not initialized. Call create_pool() first."
            )
        return cls._pool

    @classmethod
    async def close(cls):
        """Close the asyncpg connection pool"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            cls._is_initialized = False
            logger.info("AsyncPG pool closed")

    @classmethod
    async def health_check(cls) -> bool:
        """Check if the pool is healthy"""
        try:
            pool = await cls.get_pool()
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"AsyncPG health check failed: {e}")
            return False
