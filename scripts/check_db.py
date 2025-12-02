#!/usr/bin/env python3
"""Quick script to check database schema"""
import sqlite3
import sys

try:
    conn = sqlite3.connect('crypto_orchestrator.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"✓ Found {len(tables)} tables: {', '.join(tables)}")
    
    # Check exchange_api_keys table
    if 'exchange_api_keys' in tables:
        cursor.execute("PRAGMA table_info(exchange_api_keys)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"✓ exchange_api_keys table has {len(columns)} columns: {', '.join(columns)}")
        
        # Count records
        cursor.execute("SELECT COUNT(*) FROM exchange_api_keys")
        count = cursor.fetchone()[0]
        print(f"✓ exchange_api_keys table has {count} records")
    else:
        print("✗ exchange_api_keys table not found!")
        sys.exit(1)
    
    conn.close()
    print("✓ Database check completed successfully")
except Exception as e:
    print(f"✗ Database check failed: {e}")
    sys.exit(1)

