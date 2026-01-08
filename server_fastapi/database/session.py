"""
Unified Database Session Management
Provides a single, consistent interface for database session access
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Try to use connection pool if available, otherwise fall back to direct session
try:
    from .connection_pool import db_pool

    USE_CONNECTION_POOL = True
except ImportError:
    USE_CONNECTION_POOL = False
    db_pool = None

# Fallback to direct session factory
try:
    from ..database import async_session
    from ..database import get_db_session as _legacy_get_db_session

    DIRECT_SESSION_AVAILABLE = True
except ImportError:
    DIRECT_SESSION_AVAILABLE = False
    async_session = None
    _legacy_get_db_session = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Unified FastAPI dependency for database sessions.

    This is the canonical way to get a database session in FastAPI routes.
    It automatically handles:
    - Connection pooling (if available)
    - Transaction management (commit/rollback)
    - Session cleanup

    Usage in routes:
        @router.get("/items")
        async def get_items(
            db: Annotated[AsyncSession, Depends(get_db_session)]
        ):
            # Use db session
            pass
    """
    if USE_CONNECTION_POOL and db_pool and db_pool._is_initialized:
        # Use connection pool (preferred for production)
        async with db_pool.get_session() as session:
            yield session
    elif DIRECT_SESSION_AVAILABLE and async_session:
        # Use direct session factory (fallback)
        session = async_session()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    elif DIRECT_SESSION_AVAILABLE and _legacy_get_db_session:
        # Use legacy get_db_session (last resort)
        async for session in _legacy_get_db_session():
            yield session
    else:
        raise RuntimeError(
            "No database session factory available. "
            "Please ensure database is properly initialized."
        )


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions outside of FastAPI dependency injection.

    Use this in services, background tasks, or other non-route code.

    Usage:
        async with get_db_context() as session:
            # Use session
            result = await session.execute(query)
    """
    if USE_CONNECTION_POOL and db_pool and db_pool._is_initialized:
        async with db_pool.get_session() as session:
            yield session
    elif DIRECT_SESSION_AVAILABLE and async_session:
        session = async_session()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    else:
        raise RuntimeError(
            "No database session factory available. "
            "Please ensure database is properly initialized."
        )


# Alias for backward compatibility
get_db = get_db_session
