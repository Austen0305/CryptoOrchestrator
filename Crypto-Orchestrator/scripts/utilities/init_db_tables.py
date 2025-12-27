#!/usr/bin/env python3
"""Initialize database tables from models"""
import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# CRITICAL: Set DATABASE_URL to SQLite BEFORE any database imports
# This must happen before importing server_fastapi.database
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/app.db"

# Ensure data directory exists
data_dir = project_root / "data"
data_dir.mkdir(exist_ok=True)

# Now import database module (it will use our SQLite URL)
from server_fastapi.database import engine, Base
from server_fastapi import models  # Import all models to populate Base.metadata

async def init_tables():
    """Create all tables from models"""
    if engine is None:
        print("[ERROR] Database engine not initialized")
        return
    
    print("[INFO] Creating database tables from models...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[SUCCESS] All tables created successfully")
    
    # Verify tables were created
    from sqlalchemy import text
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        )
        tables = [row[0] for row in result.fetchall()]
        print(f"[INFO] Created {len(tables)} tables: {', '.join(tables[:10])}")
        if len(tables) > 10:
            print(f"   ... and {len(tables) - 10} more")

if __name__ == "__main__":
    asyncio.run(init_tables())
