#!/bin/bash
# Comprehensive Backend Test Script
# Tests all critical components of the CryptoOrchestrator backend

set -e  # Exit on error

echo "🚀 CryptoOrchestrator Backend Comprehensive Test"
echo "================================================"
echo ""

BASE_URL="http://localhost:8000"
PASSED=0
FAILED=0

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

test_passed() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASSED++))
}

test_failed() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAILED++))
}

test_warning() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
}

test_info() {
    echo -e "${BLUE}ℹ️  INFO${NC}: $1"
}

echo "1. Testing Container Status"
echo "---------------------------"
if sudo docker-compose ps backend | grep -q "Up (healthy)"; then
    test_passed "Backend container is running and healthy"
else
    test_failed "Backend container is not running or unhealthy"
fi
echo ""

echo "2. Testing Basic Health Endpoint"
echo "---------------------------------"
HEALTHZ_RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}/healthz" 2>/dev/null || echo -e "\n000")
HEALTHZ_BODY=$(echo "$HEALTHZ_RESPONSE" | head -n -1)
HEALTHZ_CODE=$(echo "$HEALTHZ_RESPONSE" | tail -n 1)

if [ "$HEALTHZ_CODE" = "200" ]; then
    test_passed "Healthz endpoint returned 200 OK"
    echo "   Response: $HEALTHZ_BODY"
else
    test_failed "Healthz endpoint returned $HEALTHZ_CODE (expected 200)"
fi
echo ""

echo "3. Testing Full Health Check"
echo "----------------------------"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}/api/health/" 2>/dev/null || echo -e "\n000")
HEALTH_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)

if [ "$HEALTH_CODE" = "200" ]; then
    test_passed "Full health check endpoint returned 200 OK"
    
    # Check overall status
    STATUS=$(echo "$HEALTH_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
    if [ "$STATUS" = "healthy" ] || [ "$STATUS" = "unhealthy" ]; then
        test_info "Overall status: $STATUS (unhealthy may be expected due to blockchain RPC)"
    fi
    
    # Check database
    DB_STATUS=$(echo "$HEALTH_BODY" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('components', {}).get('database', {}).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
    if [ "$DB_STATUS" = "healthy" ]; then
        test_passed "Database status: healthy"
    else
        test_failed "Database status: $DB_STATUS (expected healthy)"
    fi
    
    # Check Redis
    REDIS_STATUS=$(echo "$HEALTH_BODY" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('components', {}).get('redis', {}).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
    if [ "$REDIS_STATUS" = "healthy" ]; then
        test_passed "Redis status: healthy"
    else
        test_failed "Redis status: $REDIS_STATUS (expected healthy)"
    fi
    
    # Check DEX aggregators
    DEX_STATUS=$(echo "$HEALTH_BODY" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('components', {}).get('dex_aggregators', {}).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
    if [ "$DEX_STATUS" = "healthy" ]; then
        test_passed "DEX aggregators status: healthy"
    else
        test_warning "DEX aggregators status: $DEX_STATUS (may require API keys)"
    fi
else
    test_failed "Full health check endpoint returned $HEALTH_CODE (expected 200)"
fi
echo ""

echo "4. Testing Status Endpoint"
echo "--------------------------"
STATUS_RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}/api/status" 2>/dev/null || echo -e "\n000")
STATUS_CODE=$(echo "$STATUS_RESPONSE" | tail -n 1)

if [ "$STATUS_CODE" = "200" ]; then
    test_passed "Status endpoint returned 200 OK"
else
    test_warning "Status endpoint returned $STATUS_CODE (may require authentication)"
fi
echo ""

echo "5. Testing Database Connection"
echo "------------------------------"
# Test database connection via health check
if [ "$DB_STATUS" = "healthy" ]; then
    test_passed "Database connection is working"
else
    test_failed "Database connection is not working"
fi
echo ""

echo "6. Testing Redis Connection"
echo "---------------------------"
# Test Redis connection via health check
if [ "$REDIS_STATUS" = "healthy" ]; then
    test_passed "Redis connection is working"
else
    test_failed "Redis connection is not working"
fi
echo ""

echo "7. Testing Cache Warmer Service"
echo "-------------------------------"
CACHE_LOGS=$(sudo docker-compose logs backend 2>&1 | grep -i "cache_warmer\|warmup" | tail -5)
if echo "$CACHE_LOGS" | grep -q "Cache warmup cycle completed.*successful"; then
    test_passed "Cache warmer service is running successfully"
    echo "$CACHE_LOGS" | head -3 | sed 's/^/   /'
else
    test_warning "Cache warmer may not have run yet or has errors"
fi
echo ""

echo "8. Testing Error Logs"
echo "---------------------"
ERROR_COUNT=$(sudo docker-compose logs backend 2>&1 | tail -500 | grep -iE "error|exception" | grep -v "Circuit breaker is OPEN" | grep -v "Client error '401\|404'" | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    test_passed "No critical errors found in recent logs"
else
    test_warning "Found $ERROR_COUNT potential errors (excluding expected circuit breaker and API auth errors)"
    sudo docker-compose logs backend 2>&1 | tail -500 | grep -iE "error|exception" | grep -v "Circuit breaker is OPEN" | grep -v "Client error '401\|404'" | tail -5 | sed 's/^/   /'
fi
echo ""

echo "9. Testing System Resources"
echo "---------------------------"
CONTAINER_STATS=$(sudo docker stats --no-stream crypto-orchestrator-backend 2>/dev/null || echo "")
if [ -n "$CONTAINER_STATS" ]; then
    MEM_USAGE=$(echo "$CONTAINER_STATS" | tail -1 | awk '{print $4}')
    CPU_USAGE=$(echo "$CONTAINER_STATS" | tail -1 | awk '{print $3}')
    test_info "Container memory usage: $MEM_USAGE"
    test_info "Container CPU usage: $CPU_USAGE"
    test_passed "Container resource monitoring is working"
else
    test_warning "Could not retrieve container stats"
fi
echo ""

echo "10. Testing Response Times"
echo "--------------------------"
HEALTHZ_TIME=$(curl -s -o /dev/null -w "%{time_total}" "${BASE_URL}/healthz" 2>/dev/null || echo "0")
HEALTH_TIME=$(curl -s -o /dev/null -w "%{time_total}" "${BASE_URL}/api/health/" 2>/dev/null || echo "0")

if [ "$(echo "$HEALTHZ_TIME < 1.0" | bc 2>/dev/null || echo 0)" = "1" ]; then
    test_passed "Healthz endpoint response time: ${HEALTHZ_TIME}s (acceptable)"
else
    test_warning "Healthz endpoint response time: ${HEALTHZ_TIME}s (may be slow)"
fi

if [ "$(echo "$HEALTH_TIME < 20.0" | bc 2>/dev/null || echo 0)" = "1" ]; then
    test_passed "Full health check response time: ${HEALTH_TIME}s (acceptable)"
else
    test_warning "Full health check response time: ${HEALTH_TIME}s (may be slow, includes aggregator checks)"
fi
echo ""

echo "================================================"
echo "Test Summary"
echo "================================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All critical tests passed! Backend is operational.${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed. Review the output above.${NC}"
    exit 1
fi
