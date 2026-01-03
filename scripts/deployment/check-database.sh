#!/bin/bash
# Check database connection and status
# Run this on your VM to diagnose database issues

echo "🔍 Checking Database Connection Status"
echo ""

# Check if PostgreSQL is running
echo "1. Checking PostgreSQL service..."
if systemctl is-active --quiet postgresql || systemctl is-active --quiet postgresql@*; then
    echo "   ✅ PostgreSQL service is running"
else
    echo "   ❌ PostgreSQL service is NOT running"
    echo "   Try: sudo systemctl start postgresql"
fi

# Check DATABASE_URL
echo ""
echo "2. Checking DATABASE_URL environment variable..."
if [ -f .env ]; then
    echo "   Found .env file"
    grep DATABASE_URL .env | sed 's/DATABASE_URL=.*/DATABASE_URL=***HIDDEN***/'
else
    echo "   ⚠️  No .env file found"
fi

# Check if we can connect to database
echo ""
echo "3. Testing database connection..."
if command -v psql &> /dev/null; then
    # Try to extract connection info from DATABASE_URL if set
    if [ -n "$DATABASE_URL" ]; then
        echo "   DATABASE_URL is set"
        # Try to parse and test connection
        python3 << EOF
import os
import sys
from urllib.parse import urlparse

db_url = os.getenv('DATABASE_URL', '')
if db_url:
    try:
        parsed = urlparse(db_url)
        print(f"   Database type: {parsed.scheme}")
        print(f"   Host: {parsed.hostname or 'localhost'}")
        print(f"   Port: {parsed.port or '5432'}")
        print(f"   Database: {parsed.path.lstrip('/')}")
    except Exception as e:
        print(f"   Error parsing DATABASE_URL: {e}")
else:
    print("   DATABASE_URL not set in environment")
EOF
    else
        echo "   DATABASE_URL not set"
    fi
else
    echo "   ⚠️  psql not installed (optional)"
fi

# Check backend logs for database errors
echo ""
echo "4. Checking recent backend logs for database errors..."
if systemctl is-active --quiet crypto-orchestrator-backend 2>/dev/null || systemctl is-active --quiet uvicorn 2>/dev/null; then
    echo "   Backend service found, checking logs..."
    sudo journalctl -u crypto-orchestrator-backend -n 50 --no-pager | grep -i "database\|error\|connection" | tail -10 || \
    sudo journalctl -u uvicorn -n 50 --no-pager | grep -i "database\|error\|connection" | tail -10 || \
    echo "   No recent database errors in logs"
else
    echo "   ⚠️  Backend service not found as systemd unit"
    echo "   Check if backend is running: ps aux | grep uvicorn"
fi

# Check if migrations are needed
echo ""
echo "5. Checking database migrations..."
if [ -d "alembic" ]; then
    echo "   Alembic directory found"
    if command -v alembic &> /dev/null; then
        echo "   Checking migration status..."
        alembic current 2>&1 | head -5
    else
        echo "   ⚠️  Alembic not installed or not in PATH"
    fi
else
    echo "   ⚠️  No alembic directory found"
fi

echo ""
echo "✅ Database check complete!"
echo ""
echo "Next steps:"
echo "1. If PostgreSQL not running: sudo systemctl start postgresql"
echo "2. If DATABASE_URL not set: Check your .env file or environment"
echo "3. If migrations needed: alembic upgrade head"
echo "4. Test connection: python3 -c \"from server_fastapi.database import engine; import asyncio; asyncio.run(engine.connect())\""
