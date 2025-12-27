#!/usr/bin/env python3
"""
Promote PostgreSQL Replica to Primary
Script for database failover operations
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def promote_replica(db_url: str, force: bool = False) -> bool:
    """
    Promote a PostgreSQL replica to primary
    
    Args:
        db_url: Database URL for the replica
        force: Force promotion even if conditions aren't ideal
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create database connection
        engine = create_async_engine(db_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            # Check if this is a replica
            result = await session.execute(text("SELECT pg_is_in_recovery()"))
            is_replica = result.scalar()

            if not is_replica:
                logger.warning("Database is not in recovery mode (not a replica)")
                if not force:
                    logger.error("Cannot promote: not a replica. Use --force to override.")
                    return False

            # Check replication lag
            if not force:
                try:
                    result = await session.execute(text("""
                        SELECT 
                            pg_wal_lsn_diff(
                                pg_last_wal_receive_lsn(),
                                pg_last_wal_replay_lsn()
                            ) as lag_bytes
                    """))
                    lag_bytes = result.scalar() or 0
                    lag_mb = lag_bytes / (1024 * 1024)

                    if lag_mb > 100:  # More than 100MB lag
                        logger.warning(f"Replication lag is {lag_mb:.2f} MB")
                        logger.warning("Consider waiting for replica to catch up or use --force")
                        if not force:
                            return False
                except Exception as e:
                    logger.warning(f"Could not check replication lag: {e}")

            # Promote replica to primary
            logger.info("Promoting replica to primary...")
            await session.execute(text("SELECT pg_promote()"))
            await session.commit()

            # Verify promotion
            result = await session.execute(text("SELECT pg_is_in_recovery()"))
            is_still_replica = result.scalar()

            if is_still_replica:
                logger.error("Promotion failed: database is still in recovery mode")
                return False

            logger.info("✅ Replica successfully promoted to primary")
            return True

    except Exception as e:
        logger.error(f"Error promoting replica: {e}", exc_info=True)
        return False
    finally:
        await engine.dispose()


async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Promote PostgreSQL replica to primary")
    parser.add_argument(
        "--db-url",
        required=True,
        help="Database URL for the replica (e.g., postgresql+asyncpg://user:pass@host:port/db)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force promotion even if conditions aren't ideal",
    )

    args = parser.parse_args()

    logger.info("Starting replica promotion...")
    success = await promote_replica(args.db_url, force=args.force)

    if success:
        logger.info("✅ Promotion completed successfully")
        logger.info("⚠️  Remember to:")
        logger.info("   1. Update application connection strings")
        logger.info("   2. Restart application services")
        logger.info("   3. Verify application connectivity")
        sys.exit(0)
    else:
        logger.error("❌ Promotion failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
