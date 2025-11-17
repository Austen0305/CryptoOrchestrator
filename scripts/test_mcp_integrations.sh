#!/bin/bash
# Test MCP Integrations Script
# Tests all MCP integrations to ensure they're working correctly

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧪 Testing MCP Integrations...${NC}\n"

FAILED=0
PASSED=0

test_command() {
    local name=$1
    local command=$2
    
    echo -n "Testing $name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
        return 1
    fi
}

# Test Python environment
echo -e "${BLUE}📦 Testing Python Environment...${NC}"
test_command "Python" "python --version"
test_command "pip" "pip --version"
test_command "pytest" "pytest --version"

# Test Node.js environment
echo -e "\n${BLUE}📦 Testing Node.js Environment...${NC}"
test_command "Node.js" "node --version"
test_command "npm" "npm --version"

# Test Docker
echo -e "\n${BLUE}🐳 Testing Docker...${NC}"
test_command "Docker" "docker --version"
test_command "Docker Compose" "docker-compose --version"

# Test Redis
echo -e "\n${BLUE}🔴 Testing Redis...${NC}"
if test_command "Redis" "redis-cli ping"; then
    echo "✓ Redis is running"
else
    echo -e "${YELLOW}⚠ Redis not running (optional)${NC}"
fi

# Test PostgreSQL
echo -e "\n${BLUE}🐘 Testing PostgreSQL...${NC}"
if test_command "PostgreSQL" "psql --version"; then
    echo "✓ PostgreSQL is available"
else
    echo -e "${YELLOW}⚠ PostgreSQL not available (optional)${NC}"
fi

# Test MCP Scripts
echo -e "\n${BLUE}🔧 Testing MCP Scripts...${NC}"
test_command "GitHub Release Script" "python scripts/github_release.py --help"
test_command "Secrets Manager" "python scripts/secrets_manager.py --help"
test_command "Redis Setup" "python scripts/redis_setup.py --help"
test_command "Code Quality Scanner" "python scripts/code_quality_scan.py --help"

# Test Secrets Management
echo -e "\n${BLUE}🔐 Testing Secrets Management...${NC}"
if python scripts/secrets_manager.py validate 2>/dev/null; then
    echo -e "${GREEN}✓ Secrets validation passed${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ Secrets validation failed (may be expected)${NC}"
fi

# Test Redis Connection
echo -e "\n${BLUE}🔴 Testing Redis Connection...${NC}"
if python scripts/redis_setup.py test 2>/dev/null | grep -q "ok"; then
    echo -e "${GREEN}✓ Redis connection successful${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ Redis connection failed (may be expected)${NC}"
fi

# Test Docker Build
echo -e "\n${BLUE}🐳 Testing Docker Build...${NC}"
if docker build -t test-mcp:latest -f Dockerfile . > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker build successful${NC}"
    ((PASSED++))
    docker rmi test-mcp:latest > /dev/null 2>&1
else
    echo -e "${YELLOW}⚠ Docker build failed (check Dockerfile)${NC}"
fi

# Summary
echo -e "\n${BLUE}📊 Test Summary${NC}"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✅ All critical tests passed!${NC}"
    exit 0
else
    echo -e "\n${YELLOW}⚠ Some tests failed (check output above)${NC}"
    exit 1
fi

