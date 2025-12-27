#!/usr/bin/env python3
"""Quick script to check database tables"""
import sqlite3
import sys
from pathlib import Path

db_path = Path(__file__).parent.parent.parent / "data" / "app.db"
if not db_path.exists():
    print(f"Database not found at {db_path}")
    sys.exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]
print(f"Total tables: {len(tables)}")
print("\nTables:")
for table in tables:
    print(f"  - {table}")

# Check alembic version
cursor.execute("SELECT version_num FROM alembic_version")
version = cursor.fetchone()
print(f"\nAlembic version: {version[0] if version else 'None'}")

conn.close()
