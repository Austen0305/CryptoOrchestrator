#!/usr/bin/env python3
"""
Migration Runner Script
Runs Alembic migrations in the correct order
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_migrations():
    """Run all pending migrations"""
    project_root = Path(__file__).parent.parent
    
    # Change to project root
    os.chdir(project_root)
    
    # Check if alembic is available
    try:
        import alembic
    except ImportError:
        logger.error("Alembic not installed. Install with: pip install alembic")
        sys.exit(1)
    
    # Run migrations
    logger.info("Running database migrations...")
    
    try:
        from alembic.config import Config
        from alembic import command
        
        alembic_cfg = Config(str(project_root / "alembic.ini"))
        
        # Get current revision
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import create_engine
        
        # Get database URL from environment
        db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./crypto_orchestrator.db")
        
        # Convert async URL to sync URL for Alembic
        sync_db_url = db_url.replace("sqlite+aiosqlite:///", "sqlite:///")
        sync_db_url = sync_db_url.replace("postgresql+asyncpg://", "postgresql://")
        
        # Update alembic.ini temporarily
        alembic_ini_path = project_root / "alembic.ini"
        original_content = alembic_ini_path.read_text(encoding="utf-8")
        
        # Update sqlalchemy.url
        import re
        updated_content = re.sub(
            r"sqlalchemy\.url\s*=\s*.+",
            f"sqlalchemy.url = {sync_db_url}",
            original_content
        )
        
        try:
            alembic_ini_path.write_text(updated_content, encoding="utf-8")
            
            # Run migrations
            logger.info("Upgrading database to head...")
            command.upgrade(alembic_cfg, "head")
            
            logger.info("✅ Migrations completed successfully")
            
            # Show current revision
            try:
                engine = create_engine(sync_db_url)
                with engine.connect() as conn:
                    context = MigrationContext.configure(conn)
                    current_rev = context.get_current_revision()
                    logger.info(f"✅ Current database revision: {current_rev or 'base'}")
            except Exception as e:
                logger.warning(f"Could not get current revision: {e}")
            
            return True
            
        finally:
            # Restore original alembic.ini
            try:
                alembic_ini_path.write_text(original_content, encoding="utf-8")
            except Exception:
                pass
        
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
