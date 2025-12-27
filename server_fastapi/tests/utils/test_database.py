"""
Test Database Utilities
Provides isolated test database creation with automatic Alembic migrations
"""

import os
import uuid
import asyncio
import logging
from pathlib import Path
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.pool import StaticPool, NullPool
from alembic.config import Config
from alembic import command
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

logger = logging.getLogger(__name__)

# Get project root directory
ROOT_DIR = Path(__file__).resolve().parents[3]


async def create_test_database(
    base_url: Optional[str] = None, use_postgres: bool = False
) -> tuple[str, AsyncEngine]:
    """
    Create isolated test database with automatic Alembic migrations.

    Args:
        base_url: Base database URL (optional, uses env var if not provided)
        use_postgres: Whether to use PostgreSQL (default: False, uses SQLite)

    Returns:
        Tuple of (database_url, engine)
    """
    if base_url is None:
        base_url = os.getenv(
            "TEST_DATABASE_URL",
            "sqlite+aiosqlite:///file:pytest_shared?mode=memory&cache=shared",
        )

    if use_postgres or base_url.startswith("postgresql"):
        # PostgreSQL: Create isolated test database
        # Generate unique database name
        db_name = f"test_{uuid.uuid4().hex[:8]}"

        # Extract connection URL without database name
        if "+asyncpg" in base_url:
            base_conn_url = base_url.rsplit("/", 1)[0]  # Remove database name
        else:
            base_conn_url = base_url.rsplit("/", 1)[0]

        # Create database URL
        if "+asyncpg" in base_url:
            test_db_url = f"{base_conn_url}/{db_name}"
        else:
            test_db_url = f"{base_conn_url}/{db_name}"

        # Create engine for database creation
        admin_engine = create_async_engine(
            base_conn_url.replace("+asyncpg", "")
            + "/postgres",  # Connect to postgres DB
            poolclass=NullPool,
            echo=False,
        )

        # Create test database
        async with admin_engine.begin() as conn:
            await conn.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
            # Note: CREATE DATABASE cannot be executed in a transaction
            # This would need to be done outside of begin()

        # For now, use the provided URL if PostgreSQL
        test_db_url = base_url
        engine = create_async_engine(
            test_db_url,
            echo=False,
            poolclass=NullPool,
        )
    else:
        # SQLite: Use unique in-memory database for isolation
        unique_id = uuid.uuid4().hex[:8]
        test_db_url = (
            f"sqlite+aiosqlite:///file:pytest_{unique_id}?mode=memory&cache=shared"
        )

        engine = create_async_engine(
            test_db_url,
            echo=False,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )

    # Run Alembic migrations
    await run_alembic_migrations(test_db_url, engine)

    return test_db_url, engine


async def run_alembic_migrations(database_url: str, engine: AsyncEngine) -> None:
    """
    Run Alembic migrations on the test database.

    Args:
        database_url: Database URL
        engine: SQLAlchemy async engine
    """
    try:
        # Convert async URL to sync URL for Alembic
        sync_url = database_url
        if "aiosqlite" in sync_url:
            # Convert async SQLite URL to sync
            sync_url = sync_url.replace("sqlite+aiosqlite:///file:", "sqlite:///")
            # Remove query parameters for sync URL
            if "?" in sync_url:
                sync_url = sync_url.split("?")[0]
        elif "+asyncpg" in sync_url:
            sync_url = sync_url.replace("+asyncpg", "")

        # Create Alembic config
        alembic_cfg = Config()
        alembic_cfg.set_main_option("script_location", str(ROOT_DIR / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", sync_url)

        # For SQLite in-memory, we need to use the sync engine directly
        # For PostgreSQL, we can use the sync engine from async engine
        if "sqlite" in sync_url.lower():
            # For SQLite, create a sync engine from the URL
            from sqlalchemy import create_engine

            sync_engine = create_engine(
                sync_url,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
            )
        else:
            # For PostgreSQL, use sync engine from async engine
            sync_engine = engine.sync_engine

        # Run migrations
        with sync_engine.connect() as connection:
            # Configure migration context
            context = MigrationContext.configure(connection)
            script = ScriptDirectory.from_config(alembic_cfg)

            # Get current and head revisions
            current_rev = context.get_current_revision()
            head_rev = script.get_current_head()

            if current_rev != head_rev:
                logger.info(f"Running Alembic migrations: {current_rev} -> {head_rev}")
                # Run migrations using Alembic command
                command.upgrade(alembic_cfg, "head")
            else:
                logger.debug("Database already at latest migration")

        # Close sync engine if we created it
        if "sqlite" in sync_url.lower():
            sync_engine.dispose()

    except Exception as e:
        logger.warning(
            f"Alembic migration failed, falling back to create_all: {e}", exc_info=True
        )
        # Fallback: use create_all if Alembic fails
        try:
            from server_fastapi.database import Base

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        except Exception as fallback_error:
            logger.error(
                f"Fallback create_all also failed: {fallback_error}", exc_info=True
            )
            raise


async def drop_test_database(engine: AsyncEngine) -> None:
    """
    Drop all tables from test database and dispose engine.

    Args:
        engine: SQLAlchemy async engine
    """
    try:
        from server_fastapi.database import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    except Exception as e:
        logger.warning(f"Error dropping test database: {e}")
    finally:
        await engine.dispose()


def get_test_database_url() -> str:
    """
    Get test database URL from environment or generate default.

    Returns:
        Test database URL
    """
    return os.getenv(
        "TEST_DATABASE_URL",
        "sqlite+aiosqlite:///file:pytest_shared?mode=memory&cache=shared",
    )
