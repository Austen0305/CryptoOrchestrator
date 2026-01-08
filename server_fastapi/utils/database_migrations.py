"""
Database Migration Utilities
Provides utilities for managing database migrations and schema changes
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Database migration manager

    Features:
    - Schema version tracking
    - Migration execution
    - Rollback support
    - Migration history
    - Schema validation
    """

    def __init__(self):
        self.migrations: list[dict[str, Any]] = []
        self.current_version: str | None = None

    def register_migration(
        self,
        version: str,
        description: str,
        up_sql: str,
        down_sql: str | None = None,
    ):
        """Register a migration"""
        self.migrations.append(
            {
                "version": version,
                "description": description,
                "up_sql": up_sql,
                "down_sql": down_sql,
                "applied_at": None,
            }
        )

    async def get_current_version(self, session: AsyncSession) -> str | None:
        """Get current database schema version"""
        try:
            # Check if schema_version table exists
            result = await session.execute(
                text(
                    "SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1"
                )
            )
            row = result.fetchone()
            return row[0] if row else None
        except Exception:
            # Table doesn't exist, create it
            await self._create_schema_version_table(session)
            return None

    async def _create_schema_version_table(self, session: AsyncSession):
        """Create schema version tracking table"""
        await session.execute(
            text("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version VARCHAR(50) PRIMARY KEY,
                    description TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        await session.commit()

    async def apply_migrations(
        self, session: AsyncSession, target_version: str | None = None
    ):
        """Apply pending migrations"""
        current_version = await self.get_current_version(session)

        # Get pending migrations
        pending = [
            m
            for m in self.migrations
            if m["applied_at"] is None
            and (target_version is None or m["version"] <= target_version)
        ]

        if not pending:
            logger.info("No pending migrations")
            return

        # Sort by version
        pending.sort(key=lambda m: m["version"])

        for migration in pending:
            try:
                logger.info(
                    f"Applying migration {migration['version']}: {migration['description']}"
                )

                # Execute migration
                await session.execute(text(migration["up_sql"]))

                # Record migration
                await session.execute(
                    text("""
                        INSERT INTO schema_version (version, description, applied_at)
                        VALUES (:version, :description, :applied_at)
                    """),
                    {
                        "version": migration["version"],
                        "description": migration["description"],
                        "applied_at": datetime.utcnow(),
                    },
                )

                await session.commit()
                migration["applied_at"] = datetime.utcnow()
                logger.info(f"Migration {migration['version']} applied successfully")
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to apply migration {migration['version']}: {e}")
                raise

    async def rollback_migration(self, session: AsyncSession, version: str):
        """Rollback a migration"""
        migration = next((m for m in self.migrations if m["version"] == version), None)

        if not migration:
            raise ValueError(f"Migration {version} not found")

        if not migration["down_sql"]:
            raise ValueError(f"Migration {version} does not support rollback")

        try:
            logger.info(f"Rolling back migration {version}")

            # Execute rollback
            await session.execute(text(migration["down_sql"]))

            # Remove migration record
            await session.execute(
                text("DELETE FROM schema_version WHERE version = :version"),
                {"version": version},
            )

            await session.commit()
            migration["applied_at"] = None
            logger.info(f"Migration {version} rolled back successfully")
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to rollback migration {version}: {e}")
            raise

    async def get_migration_history(
        self, session: AsyncSession
    ) -> list[dict[str, Any]]:
        """Get migration history"""
        try:
            result = await session.execute(
                text(
                    "SELECT version, description, applied_at FROM schema_version ORDER BY applied_at DESC"
                )
            )
            return [
                {
                    "version": row[0],
                    "description": row[1],
                    "applied_at": row[2].isoformat() if row[2] else None,
                }
                for row in result.fetchall()
            ]
        except Exception:
            return []

    async def validate_schema(
        self, session: AsyncSession, expected_tables: list[str]
    ) -> dict[str, Any]:
        """Validate database schema"""
        try:
            # Get actual tables
            result = await session.execute(
                text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
            )
            actual_tables = {row[0] for row in result.fetchall()}
            expected_tables_set = set(expected_tables)

            missing = expected_tables_set - actual_tables
            extra = actual_tables - expected_tables_set

            return {
                "valid": len(missing) == 0,
                "missing_tables": list(missing),
                "extra_tables": list(extra),
            }
        except Exception as e:
            logger.error(f"Schema validation error: {e}")
            return {
                "valid": False,
                "error": str(e),
            }


# Global migration manager
migration_manager = MigrationManager()
