"""
Test Database Setup Script
Creates and migrates test database for E2E tests
Updated: December 6, 2025
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

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def setup_test_database():
    """Set up test database with migrations"""
    try:
        # Set test database URL
        test_db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test_e2e.db")
        os.environ["DATABASE_URL"] = test_db_url
        
        print(f"[INFO] Setting up test database: {test_db_url}")
        
        # Convert aiosqlite URL to sync SQLite URL for Alembic
        if test_db_url.startswith("sqlite+aiosqlite:///"):
            sync_db_url = test_db_url.replace("sqlite+aiosqlite:///", "sqlite:///")
        else:
            sync_db_url = test_db_url
        
        print(f"[INFO] Using sync database URL for migrations: {sync_db_url}")
        
        # Update alembic.ini with test database URL temporarily
        # alembic.ini is in project root, not scripts directory
        alembic_ini_path = Path(__file__).parent.parent.parent / "alembic.ini"
        original_content = alembic_ini_path.read_text()
        
        # Update sqlalchemy.url for migrations
        updated_content = original_content.replace(
            "sqlalchemy.url = sqlite:///./crypto_orchestrator.db",
            f"sqlalchemy.url = {sync_db_url}"
        )
        alembic_ini_path.write_text(updated_content)
        
        try:
            # Run migrations using Alembic
            from alembic.config import Config
            from alembic import command
            
            alembic_cfg = Config(str(alembic_ini_path))
            
            # Try to run migrations
            try:
                command.upgrade(alembic_cfg, "head")
                print(f"[SUCCESS] Database migrations completed for test database")
            except Exception as migration_error:
                print(f"[WARN] Alembic migration failed: {migration_error}")
                print("[INFO] Attempting to create tables directly using init_database...")
                # Fallback: Create tables directly
                from server_fastapi.database import init_database
                await init_database()
                print("[SUCCESS] Database tables created directly using init_database()")
            
        except Exception as e:
            print(f"[WARN] Migration failed, attempting to create tables directly: {e}")
            # Fallback: Create tables directly using init_database
            try:
                from server_fastapi.database import init_database
                await init_database()
                print("[SUCCESS] Database tables created directly")
            except Exception as e2:
                print(f"[ERROR] Database initialization failed: {e2}")
                import traceback
                traceback.print_exc()
                raise
        finally:
            # Restore original alembic.ini
            try:
                alembic_ini_path.write_text(original_content)
            except Exception:
                pass  # Ignore if we can't restore
            
    except Exception as e:
        print(f"[ERROR] Test database setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(setup_test_database())

