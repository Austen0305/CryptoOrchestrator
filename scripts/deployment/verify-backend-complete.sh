#!/bin/bash
# ==========================================
# Complete Backend Verification Script
# ==========================================
# Tests all critical endpoints and services
# ==========================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔍 Verifying Backend is Fully Working...${NC}"
echo ""

# Test 1: Health Endpoints
echo -e "${YELLOW}1. Testing Health Endpoints...${NC}"
HEALTH_RESPONSE=$(sudo docker exec crypto-orchestrator-backend python -c "
import urllib.request
import json
try:
    response = urllib.request.urlopen('http://localhost:8000/health', timeout=5)
    data = json.loads(response.read().decode())
    print(json.dumps(data))
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)

if echo "$HEALTH_RESPONSE" | grep -q "status.*healthy"; then
    echo -e "${GREEN}✅ Health endpoint: Working${NC}"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    echo -e "${RED}❌ Health endpoint: Failed${NC}"
    echo "$HEALTH_RESPONSE"
fi

HEALTHZ_RESPONSE=$(sudo docker exec crypto-orchestrator-backend python -c "
import urllib.request
try:
    response = urllib.request.urlopen('http://localhost:8000/healthz', timeout=5)
    print(response.read().decode())
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)

if echo "$HEALTHZ_RESPONSE" | grep -q "status.*ok"; then
    echo -e "${GREEN}✅ Healthz endpoint: Working${NC}"
else
    echo -e "${RED}❌ Healthz endpoint: Failed${NC}"
    echo "$HEALTHZ_RESPONSE"
fi

echo ""

# Test 2: Database Connection
echo -e "${YELLOW}2. Testing Database Connection...${NC}"
DB_TEST=$(sudo docker exec crypto-orchestrator-backend python -c "
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv('DATABASE_URL')
async_url = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1)
engine = create_async_engine(async_url)

async def test():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text('SELECT 1'))
            row = result.fetchone()
            print('SUCCESS')
    except Exception as e:
        print(f'ERROR: {e}')
    finally:
        await engine.dispose()

asyncio.run(test())
" 2>&1)

if echo "$DB_TEST" | grep -q "SUCCESS"; then
    echo -e "${GREEN}✅ Database: Connected${NC}"
else
    echo -e "${RED}❌ Database: Failed${NC}"
    echo "$DB_TEST"
fi

echo ""

# Test 3: Redis Connection
echo -e "${YELLOW}3. Testing Redis Connection...${NC}"
REDIS_TEST=$(sudo docker exec crypto-orchestrator-redis redis-cli ping 2>&1)
if [ "$REDIS_TEST" = "PONG" ]; then
    echo -e "${GREEN}✅ Redis: Connected${NC}"
else
    echo -e "${RED}❌ Redis: Failed${NC}"
    echo "$REDIS_TEST"
fi

echo ""

# Test 4: API Endpoints
echo -e "${YELLOW}4. Testing API Endpoints...${NC}"
API_TEST=$(sudo docker exec crypto-orchestrator-backend python -c "
import urllib.request
import json
try:
    response = urllib.request.urlopen('http://localhost:8000/api/', timeout=5)
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)

if echo "$API_TEST" | grep -q "SUCCESS"; then
    echo -e "${GREEN}✅ API Root: Accessible${NC}"
else
    echo -e "${YELLOW}⚠️  API Root: ${API_TEST}${NC}"
fi

echo ""

# Test 5: Service Status
echo -e "${YELLOW}5. Checking Service Status...${NC}"
sudo docker-compose ps

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}✨ Verification Complete! ✨${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
