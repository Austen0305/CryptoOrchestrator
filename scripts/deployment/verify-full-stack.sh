#!/bin/bash
# Comprehensive verification script for CryptoOrchestrator full stack
# Run this on the Google Cloud VM to verify everything is working

set -e

PROJECT_DIR="/home/labarcodez/CryptoOrchestrator"
cd "$PROJECT_DIR"

echo "🔍 CryptoOrchestrator Full Stack Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track results
PASSED=0
FAILED=0

check_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASSED++))
}

check_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
}

echo -e "${BLUE}Step 1: Checking Backend Service Status${NC}"
echo "────────────────────────────────────────────────────────────────────────────"
if systemctl is-active --quiet cryptoorchestrator; then
    check_pass "Backend service is running"
    systemctl status cryptoorchestrator --no-pager -l | head -10
else
    check_fail "Backend service is not running"
    echo "  Attempting to start service..."
    sudo systemctl start cryptoorchestrator || check_fail "Failed to start service"
fi
echo ""

echo -e "${BLUE}Step 2: Checking Backend Health Endpoint${NC}"
echo "────────────────────────────────────────────────────────────────────────────"
if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
    echo "  Response: $HEALTH_RESPONSE"
    if echo "$HEALTH_RESPONSE" | grep -q "healthy\|ok"; then
        check_pass "Backend health endpoint is responding"
    else
        check_warn "Backend health endpoint responded but status unclear"
    fi
else
    check_fail "Backend health endpoint is not responding"
fi
echo ""

echo -e "${BLUE}Step 3: Checking Status Endpoint${NC}"
echo "────────────────────────────────────────────────────────────────────────────"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/status/ || echo "000")
if [ "$STATUS_CODE" = "200" ]; then
    STATUS_RESPONSE=$(curl -s http://localhost:8000/api/status/)
    echo "  Response: $STATUS_RESPONSE" | head -5
    check_pass "Status endpoint is working (HTTP $STATUS_CODE)"
elif [ "$STATUS_CODE" = "500" ]; then
    check_fail "Status endpoint returned HTTP 500 (check logs for compression middleware errors)"
else
    check_warn "Status endpoint returned HTTP $STATUS_CODE"
fi
echo ""

echo -e "${BLUE}Step 4: Checking Database Connection${NC}"
echo "────────────────────────────────────────────────────────────────────────────"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    DB_TEST=$(python3 -c "
import asyncio
import sys
import os
os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///./data/app.db')
try:
    from server_fastapi.database import get_db_context
    from sqlalchemy import text
    async def test():
        try:
            async with get_db_context() as db:
                await db.execute(text('SELECT 1'))
            print('OK')
        except Exception as e:
            print(f'ERROR: {e}')
            sys.exit(1)
    asyncio.run(test())
except Exception as e:
    print(f'IMPORT_ERROR: {e}')
    sys.exit(1)
" 2>&1)
    if echo "$DB_TEST" | grep -q "OK"; then
        check_pass "Database connection is working"
    else
        check_fail "Database connection failed: $DB_TEST"
    fi
else
    check_warn "Virtual environment not found, skipping database test"
fi
echo ""

echo -e "${BLUE}Step 5: Checking Redis Connection (Optional)${NC}"
echo "────────────────────────────────────────────────────────────────────────────"
REDIS_TEST=$(python3 -c "
import asyncio
import sys
import os
try:
    import redis.asyncio as aioredis
    async def test():
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            client = await aioredis.from_url(redis_url, encoding='utf-8', decode_responses=True, socket_connect_timeout=2)
            await asyncio.wait_for(client.ping(), timeout=2)
            print('OK')
            await client.close()
        except Exception as e:
            print(f'ERROR: {e}')
    asyncio.run(test())
except ImportError:
    print('NOT_INSTALLED')
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)
if echo "$REDIS_TEST" | grep -q "OK"; then
    check_pass "Redis connection is working"
elif echo "$REDIS_TEST" | grep -q "NOT_INSTALLED"; then
    check_warn "Redis client not installed (optional, using in-memory cache)"
elif echo "$REDIS_TEST" | grep -q "ERROR"; then
    check_warn "Redis connection failed (optional, using in-memory cache): $REDIS_TEST"
else
    check_warn "Redis status unclear"
fi
echo ""

echo -e "${BLUE}Step 6: Checking Recent Logs for Errors${NC}"
echo "────────────────────────────────────────────────────────────────────────────"
if [ -f "logs/app.log" ]; then
    ERROR_COUNT=$(tail -100 logs/app.log 2>/dev/null | grep -i "error\|exception\|traceback" | grep -v "DEBUG" | wc -l || echo "0")
    COMPRESSION_ERRORS=$(tail -100 logs/app.log 2>/dev/null | grep -i "compression middleware" | grep -i "error" | wc -l || echo "0")
    if [ "$COMPRESSION_ERRORS" -gt 0 ]; then
        check_fail "Found $COMPRESSION_ERRORS compression middleware errors in recent logs"
        echo "  Recent compression errors:"
        tail -100 logs/app.log 2>/dev/null | grep -i "compression middleware" | grep -i "error" | tail -3 | sed 's/^/    /'
    elif [ "$ERROR_COUNT" -gt 10 ]; then
        check_warn "Found $ERROR_COUNT errors in recent logs (may be normal)"
    else
        check_pass "No critical errors in recent logs"
    fi
else
    check_warn "Log file not found (logs/app.log)"
fi
echo ""

echo -e "${BLUE}Step 7: Checking Port 8000${NC}"
echo "────────────────────────────────────────────────────────────────────────────"
if ss -tlnp | grep -q ":8000 "; then
    LISTENER=$(ss -tlnp | grep ":8000 ")
    echo "  Port 8000 is listening: $LISTENER"
    check_pass "Port 8000 is open and listening"
else
    check_fail "Port 8000 is not listening"
fi
echo ""

echo -e "${BLUE}Step 8: Checking System Resources${NC}"
echo "────────────────────────────────────────────────────────────────────────────"
MEMORY=$(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')
CPU=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')
echo "  Memory usage: $MEMORY"
echo "  CPU usage: $CPU"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    PYTHON_PROCS=$(ps aux | grep -E "python.*uvicorn|python.*server_fastapi" | grep -v grep | wc -l)
    echo "  Python/uvicorn processes: $PYTHON_PROCS"
    if [ "$PYTHON_PROCS" -gt 0 ]; then
        check_pass "Backend processes are running"
    else
        check_fail "No backend processes found"
    fi
fi
echo ""

echo -e "${BLUE}Step 9: Checking Environment Variables${NC}"
echo "────────────────────────────────────────────────────────────────────────────"
if [ -f ".env" ]; then
    if grep -q "DATABASE_URL" .env; then
        check_pass "DATABASE_URL is set"
    else
        check_warn "DATABASE_URL not found in .env"
    fi
    if grep -q "SECRET_KEY" .env; then
        check_pass "SECRET_KEY is set"
    else
        check_warn "SECRET_KEY not found in .env"
    fi
else
    check_warn ".env file not found"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}Summary${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All critical checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Verify frontend can connect to backend"
    echo "  2. Test user authentication flow"
    echo "  3. Test critical API endpoints"
    echo "  4. Monitor logs for any issues"
    exit 0
else
    echo -e "${RED}⚠️  Some checks failed. Please review the errors above.${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs: tail -100 logs/app.log"
    echo "  2. Check service status: sudo systemctl status cryptoorchestrator"
    echo "  3. Check service logs: sudo journalctl -u cryptoorchestrator -n 100"
    echo "  4. Restart service: sudo systemctl restart cryptoorchestrator"
    exit 1
fi
