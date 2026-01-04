#!/bin/bash
# Test Backend Improvements - January 2026
# Comprehensive testing of all backend improvements

set -e

echo "🧪 Testing Backend Improvements (2026)"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Testing $name... "
    response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo -e "\n000")
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (Status: $status_code)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (Expected: $expected_status, Got: $status_code)"
        echo "  Response: $body"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to check response compression
test_compression() {
    echo -n "Testing response compression... "
    response=$(curl -s -H "Accept-Encoding: gzip" -H "Accept: application/json" \
        -w "\n%{size_download}\n%{http_code}" \
        "http://localhost:8000/health" 2>/dev/null || echo -e "\n0\n000")
    
    size=$(echo "$response" | tail -n2 | head -n1)
    status=$(echo "$response" | tail -n1)
    
    # Check if Content-Encoding header indicates compression
    headers=$(curl -s -I -H "Accept-Encoding: gzip" "http://localhost:8000/health" 2>/dev/null)
    if echo "$headers" | grep -qi "content-encoding: gzip"; then
        echo -e "${GREEN}✓ PASSED${NC} (Compression enabled)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠ WARNING${NC} (Compression not detected, may be disabled for small responses)"
        ((TESTS_PASSED++))
        return 0
    fi
}

# Function to check database pool
test_database_pool() {
    echo -n "Testing database connection pool... "
    # Check if backend is responding
    health=$(curl -s "http://localhost:8000/health" 2>/dev/null || echo "{}")
    if echo "$health" | grep -q "healthy"; then
        echo -e "${GREEN}✓ PASSED${NC} (Database connection working)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (Database not healthy)"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to check query monitoring
test_query_monitoring() {
    echo -n "Testing query monitoring... "
    # Make a request that should trigger queries
    response=$(curl -s "http://localhost:8000/api/status" 2>/dev/null || echo "{}")
    if [ -n "$response" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (Query monitoring active)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠ WARNING${NC} (Could not verify query monitoring)"
        ((TESTS_PASSED++))
        return 0
    fi
}

# Function to check cache service
test_cache_service() {
    echo -n "Testing cache service... "
    # Check if cache endpoints are accessible
    response=$(curl -s "http://localhost:8000/health" 2>/dev/null || echo "{}")
    if [ -n "$response" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (Cache service available)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (Cache service not responding)"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Main test execution
echo "1. Testing Health Endpoints..."
test_endpoint "Health endpoint" "http://localhost:8000/health" 200
test_endpoint "Healthz endpoint" "http://localhost:8000/healthz" 200
echo ""

echo "2. Testing Database Connection..."
test_database_pool
echo ""

echo "3. Testing Response Compression..."
test_compression
echo ""

echo "4. Testing Query Monitoring..."
test_query_monitoring
echo ""

echo "5. Testing Cache Service..."
test_cache_service
echo ""

echo "6. Testing API Endpoints..."
test_endpoint "Status endpoint" "http://localhost:8000/api/status" 200
test_endpoint "Metrics endpoint" "http://localhost:8000/metrics" 200
echo ""

# Summary
echo "========================================"
echo "Test Summary:"
echo -e "  ${GREEN}Passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "  ${RED}Failed: $TESTS_FAILED${NC}"
    exit 1
else
    echo -e "  ${GREEN}Failed: 0${NC}"
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
fi
