#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Initialization Script
Initializes database, creates tables, runs migrations, and verifies setup
"""

import os
import sys
import asyncio
import io
from pathlib import Path

# Fix Windows encoding issues
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def setup_paths() -> Path:
    """Add project root to Python path"""
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Load .env file explicitly
    try:
        from dotenv import load_dotenv  # type: ignore[import-untyped]
        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=True)
    except ImportError:
        pass  # dotenv not available, rely on environment
    
    return project_root


def create_database_if_needed(db_url: str) -> bool:
    """Create PostgreSQL database if it doesn't exist"""
    if not db_url.startswith("postgresql"):
        # SQLite databases are created automatically
        return True
    
    try:
        # Parse PostgreSQL URL
        # Format: postgresql+asyncpg://user:password@host:port/dbname
        from urllib.parse import urlparse
        
        parsed = urlparse(db_url.replace("postgresql+asyncpg://", "postgresql://"))
        
        if not parsed.hostname or not parsed.username:
            print("⚠️  Could not parse PostgreSQL URL for database creation")
            return False
        
        # Import psycopg2 for sync connection
        try:
            import psycopg2  # type: ignore[import-untyped]
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT  # type: ignore[import-untyped]
        except ImportError:
            print("⚠️  psycopg2 not installed, skipping database creation check")
            return True
        
        # Connect to postgres database to create target database
        db_name = parsed.path[1:] if parsed.path else "cryptoorchestrator"
        admin_conn_str = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port or 5432}/postgres"
        
        try:
            conn = psycopg2.connect(admin_conn_str)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (db_name,)
            )
            exists = cursor.fetchone()
            
            if not exists:
                print(f"📦 Creating PostgreSQL database: {db_name}")
                cursor.execute(f'CREATE DATABASE "{db_name}"')
                print(f"✅ Database '{db_name}' created successfully")
            else:
                print(f"✅ Database '{db_name}' already exists")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"⚠️  Could not create database (may already exist): {e}")
            return True
            
    except Exception as e:
        print(f"⚠️  Database creation check failed: {e}")
        return True  # Continue anyway


async def run_migrations() -> bool:
    """Run Alembic migrations"""
    project_root = setup_paths()
    alembic_ini_path = project_root / "alembic.ini"
    
    if not alembic_ini_path.exists():
        print(f"❌ alembic.ini not found at {alembic_ini_path}")
        return False
    
    try:
        from alembic.config import Config  # type: ignore[import-untyped]
        from alembic import command  # type: ignore[attr-defined]
        
        # Get database URL from environment
        db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/app.db")
        
        # Convert async URL to sync URL for Alembic
        sync_db_url = db_url.replace("sqlite+aiosqlite:///", "sqlite:///")
        sync_db_url = sync_db_url.replace("postgresql+asyncpg://", "postgresql://")
        
        # Update alembic.ini temporarily
        original_content = alembic_ini_path.read_text(encoding="utf-8")
        
        # Update sqlalchemy.url
        updated_content = original_content
        if "sqlalchemy.url = " in original_content:
            # Replace existing URL
            import re
            updated_content = re.sub(
                r"sqlalchemy\.url\s*=\s*.+",
                f"sqlalchemy.url = {sync_db_url}",
                original_content
            )
        else:
            # Add URL if not present
            updated_content = original_content + f"\nsqlalchemy.url = {sync_db_url}\n"
        
        alembic_ini_path.write_text(updated_content, encoding="utf-8")
        
        try:
            print("🔄 Running database migrations...")
            alembic_cfg = Config(str(alembic_ini_path))
            
            # Run migrations
            command.upgrade(alembic_cfg, "head")
            print("✅ Database migrations completed successfully")
            
            # Verify migration status
            try:
                from alembic.runtime.migration import MigrationContext  # type: ignore[import-untyped]
                from sqlalchemy import create_engine  # type: ignore[import-untyped]
                
                engine = create_engine(sync_db_url)
                with engine.connect() as conn:
                    context = MigrationContext.configure(conn)
                    current_rev = context.get_current_revision()
                    print(f"✅ Current database revision: {current_rev or 'base'}")
            except Exception:
                pass  # Skip revision check if it fails
            
            return True
            
        finally:
            # Restore original alembic.ini
            try:
                alembic_ini_path.write_text(original_content, encoding="utf-8")
            except Exception:
                pass
        
    except Exception as e:
        print(f"⚠️  Migration failed: {e}")
        print("📋 Attempting fallback: Creating tables directly...")
        return await init_tables_directly()


async def init_tables_directly() -> bool:
    """Initialize tables directly using SQLAlchemy (fallback method)"""
    try:
        setup_paths()
        from server_fastapi.database import init_database
        
        print("🔄 Creating tables directly...")
        await init_database()
        print("✅ Database tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create tables directly: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_database() -> bool:
    """Verify database connection and table existence"""
    try:
        setup_paths()
        from server_fastapi.database import get_db_context
        from sqlalchemy import text  # type: ignore[import-untyped]

        print("🔍 Verifying database connection...")

        async with get_db_context() as session:
            # Test connection
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            print("✅ Database connection successful")
            
            # Check for key tables
            tables_to_check = [
                "users", "bots", "trades", "portfolios", "wallets",
                "orders", "dextrades", "wallet_transactions"
            ]
            
            existing_tables = []
            for table in tables_to_check:
                try:
                    result = await session.execute(
                        text(f"SELECT 1 FROM {table} LIMIT 1")
                    )
                    existing_tables.append(table)
                except Exception:
                    pass  # Table doesn't exist or error checking
            
            if existing_tables:
                print(f"✅ Verified {len(existing_tables)} key tables exist: {', '.join(existing_tables[:5])}")
                if len(existing_tables) > 5:
                    print(f"   ... and {len(existing_tables) - 5} more")
            
            await session.commit()
        
        return True
        
    except Exception as e:
        print(f"⚠️  Database verification warning: {e}")
        return False  # Non-fatal


def create_data_directory() -> bool:
    """Create data directory for SQLite databases"""
    try:
        data_dir = Path("data")
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created data directory: {data_dir.absolute()}")
        return True
    except Exception as e:
        print(f"⚠️  Could not create data directory: {e}")
        return False


async def init_database(  # noqa: C901
    create_db: bool = True,
    run_migrations_flag: bool = True,
    verify: bool = True,
    seed_data: bool = False
) -> bool:
    """Initialize database"""
    print("🚀 Initializing database...")
    print("=" * 60)
    
    # Ensure paths are set up and .env is loaded
    project_root = setup_paths()
    
    # Load .env explicitly to ensure fresh values
    try:
        from dotenv import load_dotenv  # type: ignore[import-untyped]
        load_dotenv(project_root / ".env", override=True)
    except ImportError:
        pass
    
    # Get database URL (should be from .env now)
    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/app.db")
    
    # Display database URL (hide credentials for PostgreSQL)
    if "@" in db_url:
        display_url = db_url.split("@")[-1]
    elif ":///" in db_url:
        display_url = db_url.split(":///")[-1]
    else:
        display_url = db_url
    print(f"📊 Database URL: {display_url}")
    
    # Create data directory for SQLite
    if "sqlite" in db_url:
        create_data_directory()
    
    # Create database if needed (PostgreSQL)
    if create_db and db_url.startswith("postgresql"):
        create_database_if_needed(db_url)
    
    # Run migrations
    if run_migrations_flag:
        success = await run_migrations()
        if not success:
            print("❌ Database initialization failed")
            return False
    
    # Verify database
    if verify:
        await verify_database()
    
    # Seed test data (optional, development only)
    if seed_data and os.getenv("NODE_ENV") == "development":
        print("🌱 Seeding test data (development only)...")
        # Seed data functionality can be added here if needed
        print("✅ Test data seeding skipped (not implemented)")
    
    print("=" * 60)
    print("✅ Database initialization complete!")
    return True


def main() -> None:
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize CryptoOrchestrator database")
    parser.add_argument(
        "--skip-create",
        action="store_true",
        help="Skip database creation (PostgreSQL)"
    )
    parser.add_argument(
        "--skip-migrations",
        action="store_true",
        help="Skip running migrations"
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip database verification"
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed test data (development only)"
    )
    
    args = parser.parse_args()
    
    success = asyncio.run(init_database(
        create_db=not args.skip_create,
        run_migrations_flag=not args.skip_migrations,
        verify=not args.skip_verify,
        seed_data=args.seed
    ))
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
