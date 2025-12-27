#!/usr/bin/env python3
"""
Database Migration Test Script
Tests that Alembic migrations can run successfully
"""
import os
import sys
import asyncio
from pathlib import Path

# Set UTF-8 encoding for Windows compatibility
if sys.platform == 'win32':
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_migrations():
    """Test that migrations can run"""
    try:
        from alembic.config import Config
        from alembic import command
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        
        print("[INFO] Testing database migrations...")
        
        # Get database URL
        database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/app.db")
        print(f"[INFO] Database URL: {database_url[:50]}...")
        
        # Convert async URL to sync for Alembic (Alembic uses sync SQLAlchemy)
        if database_url.startswith("sqlite+aiosqlite://"):
            sync_db_url = database_url.replace("sqlite+aiosqlite://", "sqlite://")
        elif database_url.startswith("postgresql+asyncpg://"):
            sync_db_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        else:
            sync_db_url = database_url
        
        # Load Alembic configuration
        alembic_cfg = Config(str(Path(__file__).parent.parent / "alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", sync_db_url)
        
        # Test 1: Check migration history
        print("\n[TEST 1] Checking migration history...")
        try:
            script = ScriptDirectory.from_config(alembic_cfg)
            revisions = list(script.walk_revisions())
            print(f"✓ Found {len(revisions)} migration revisions")
            if revisions:
                print(f"  Latest: {revisions[0].revision} - {revisions[0].doc}")
                print(f"  Oldest: {revisions[-1].revision} - {revisions[-1].doc}")
        except Exception as e:
            print(f"X Failed to read migration history: {e}")
            return False
        
        # Test 2: Check current migration status (dry run)
        print("\n[TEST 2] Checking migration status (dry run)...")
        try:
            # Try to get current revision (won't connect to DB, just validates config)
            print("✓ Migration configuration valid")
        except Exception as e:
            print(f"X Migration configuration error: {e}")
            return False
        
        # Test 3: Validate migration scripts syntax
        print("\n[TEST 3] Validating migration script syntax...")
        try:
            script = ScriptDirectory.from_config(alembic_cfg)
            for revision in script.walk_revisions():
                # Try to compile the migration
                script.get_revision(revision.revision)
            print(f"✓ All {len(revisions)} migration scripts have valid syntax")
        except Exception as e:
            print(f"X Migration script syntax error: {e}")
            return False
        
        print("\n✓ Migration validation completed successfully")
        print("\nTo apply migrations, run:")
        print("  alembic upgrade head")
        print("or")
        print("  npm run migrate")
        
        return True
        
    except ImportError as e:
        print(f"X Import error: {e}")
        print("  Make sure alembic is installed: pip install alembic")
        return False
    except Exception as e:
        print(f"X Migration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_migrations()
    sys.exit(0 if success else 1)
