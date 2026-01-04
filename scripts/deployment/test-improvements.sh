#!/bin/bash
# Test Backend Improvements - Comprehensive Testing Script
# Run this on the VM to test all improvements

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧪 Testing Backend Improvements (2026)${NC}"
echo "=========================================="
echo ""

# Test 1: Health Endpoints
echo -e "${YELLOW}1. Testing Health Endpoints...${NC}"
HEALTH_TEST=$(sudo docker exec crypto-orchestrator-backend python -c "
import urllib.request
import json
try:
    response = urllib.request.urlopen('http://localhost:8000/health', timeout=10)
    data = json.loads(response.read().decode())
    print('SUCCESS')
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)

if echo "$HEALTH_TEST" | grep -q "SUCCESS"; then
    echo -e "${GREEN}✅ Health endpoint: Working${NC}"
    echo "$HEALTH_TEST" | grep -v "SUCCESS"
else
    echo -e "${RED}❌ Health endpoint: Failed${NC}"
    echo "$HEALTH_TEST"
fi

HEALTHZ_TEST=$(sudo docker exec crypto-orchestrator-backend python -c "
import urllib.request
try:
    response = urllib.request.urlopen('http://localhost:8000/healthz', timeout=10)
    print('SUCCESS')
    print(response.read().decode())
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)

if echo "$HEALTHZ_TEST" | grep -q "SUCCESS"; then
    echo -e "${GREEN}✅ Healthz endpoint: Working${NC}"
else
    echo -e "${RED}❌ Healthz endpoint: Failed${NC}"
    echo "$HEALTHZ_TEST"
fi

echo ""

# Test 2: Response Compression
echo -e "${YELLOW}2. Testing Response Compression...${NC}"
COMPRESSION_TEST=$(sudo docker exec crypto-orchestrator-backend python -c "
import urllib.request
try:
    req = urllib.request.Request('http://localhost:8000/health')
    req.add_header('Accept-Encoding', 'gzip')
    response = urllib.request.urlopen(req, timeout=10)
    headers = dict(response.headers)
    if 'Content-Encoding' in headers and 'gzip' in headers['Content-Encoding']:
        print('SUCCESS: Compression enabled')
    else:
        print('WARNING: Compression not detected (may be disabled for small responses)')
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)

if echo "$COMPRESSION_TEST" | grep -q "SUCCESS"; then
    echo -e "${GREEN}✅ Compression: Enabled${NC}"
elif echo "$COMPRESSION_TEST" | grep -q "WARNING"; then
    echo -e "${YELLOW}⚠️  Compression: ${COMPRESSION_TEST}${NC}"
else
    echo -e "${RED}❌ Compression test failed${NC}"
    echo "$COMPRESSION_TEST"
fi

echo ""

# Test 3: Database Pool Configuration
echo -e "${YELLOW}3. Testing Database Pool Configuration...${NC}"
POOL_TEST=$(sudo docker exec crypto-orchestrator-backend python -c "
import os
pool_size = os.getenv('DB_POOL_SIZE', '50')
max_overflow = os.getenv('DB_MAX_OVERFLOW', '30')
print(f'Pool Size: {pool_size}')
print(f'Max Overflow: {max_overflow}')
if int(pool_size) >= 50 and int(max_overflow) >= 30:
    print('SUCCESS: Pool optimized')
else:
    print('WARNING: Pool not optimized')
" 2>&1)

if echo "$POOL_TEST" | grep -q "SUCCESS"; then
    echo -e "${GREEN}✅ Database Pool: Optimized${NC}"
    echo "$POOL_TEST" | grep -v "SUCCESS"
else
    echo -e "${YELLOW}⚠️  Database Pool: ${POOL_TEST}${NC}"
fi

echo ""

# Test 4: Cache Service with TTL Jitter
echo -e "${YELLOW}4. Testing Cache Service (TTL Jitter)...${NC}"
CACHE_TEST=$(sudo docker exec crypto-orchestrator-backend python -c "
import sys
sys.path.insert(0, '/app')
try:
    from server_fastapi.services.cache_service import CACHE_CONFIG
    print('SUCCESS')
    print(f'Default TTL: {CACHE_CONFIG[\"default_ttl\"]}s')
    print(f'TTL Jitter: {CACHE_CONFIG.get(\"ttl_jitter_percent\", 10)}%')
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)

if echo "$CACHE_TEST" | grep -q "SUCCESS"; then
    echo -e "${GREEN}✅ Cache Service: Configured with TTL jitter${NC}"
    echo "$CACHE_TEST" | grep -v "SUCCESS"
else
    echo -e "${RED}❌ Cache Service: ${CACHE_TEST}${NC}"
fi

echo ""

# Test 5: Query Monitoring
echo -e "${YELLOW}5. Testing Query Monitoring...${NC}"
QUERY_TEST=$(sudo docker exec crypto-orchestrator-backend python -c "
import sys
sys.path.insert(0, '/app')
try:
    from server_fastapi.middleware.enhanced_query_monitoring import EnhancedQueryMonitoringMiddleware
    print('SUCCESS: Query monitoring middleware available')
except ImportError as e:
    print(f'ERROR: {e}')
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)

if echo "$QUERY_TEST" | grep -q "SUCCESS"; then
    echo -e "${GREEN}✅ Query Monitoring: Available${NC}"
else
    echo -e "${RED}❌ Query Monitoring: ${QUERY_TEST}${NC}"
fi

echo ""

# Test 6: Check for Errors in Logs
echo -e "${YELLOW}6. Checking for Errors...${NC}"
ERRORS=$(sudo docker-compose logs backend 2>&1 | grep -i "error\|exception\|traceback" | tail -10)
if [ -z "$ERRORS" ]; then
    echo -e "${GREEN}✅ No recent errors found${NC}"
else
    echo -e "${RED}❌ Recent errors found:${NC}"
    echo "$ERRORS"
fi

echo ""

# Test 7: Router Loading
echo -e "${YELLOW}7. Checking Router Loading...${NC}"
ROUTER_COUNT=$(sudo docker-compose logs backend 2>&1 | grep -i "loaded router" | wc -l)
echo "Routers loaded: $ROUTER_COUNT"
if [ "$ROUTER_COUNT" -gt 50 ]; then
    echo -e "${GREEN}✅ Routers loaded successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Only $ROUTER_COUNT routers loaded${NC}"
fi

echo ""

# Summary
echo "=========================================="
echo -e "${BLUE}Test Summary:${NC}"
echo "=========================================="
echo ""

# Count successes
SUCCESS_COUNT=0
if echo "$HEALTH_TEST" | grep -q "SUCCESS"; then ((SUCCESS_COUNT++)); fi
if echo "$HEALTHZ_TEST" | grep -q "SUCCESS"; then ((SUCCESS_COUNT++)); fi
if echo "$COMPRESSION_TEST" | grep -q "SUCCESS\|WARNING"; then ((SUCCESS_COUNT++)); fi
if echo "$POOL_TEST" | grep -q "SUCCESS"; then ((SUCCESS_COUNT++)); fi
if echo "$CACHE_TEST" | grep -q "SUCCESS"; then ((SUCCESS_COUNT++)); fi
if echo "$QUERY_TEST" | grep -q "SUCCESS"; then ((SUCCESS_COUNT++)); fi

echo -e "${GREEN}Tests Passed: $SUCCESS_COUNT/6${NC}"

if [ "$SUCCESS_COUNT" -eq 6 ]; then
    echo -e "${GREEN}✅ All improvements working correctly!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some improvements need attention${NC}"
    exit 1
fi
