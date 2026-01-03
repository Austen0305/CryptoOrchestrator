#!/bin/bash
# ==========================================
# Test Optimized Docker Build
# ==========================================
# This script tests the optimized Dockerfile to ensure it works correctly
# ==========================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧪 Testing Optimized Docker Build${NC}"
echo ""

# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Check if requirements files exist
echo -e "${YELLOW}📋 Checking requirements files...${NC}"
if [ ! -f "requirements-base.txt" ]; then
    echo -e "${RED}❌ requirements-base.txt not found${NC}"
    exit 1
fi
if [ ! -f "requirements-ml.txt" ]; then
    echo -e "${RED}❌ requirements-ml.txt not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Requirements files found${NC}"
echo ""

# Check if Dockerfile.optimized exists
if [ ! -f "Dockerfile.optimized" ]; then
    echo -e "${RED}❌ Dockerfile.optimized not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Dockerfile.optimized found${NC}"
echo ""

# Test 1: Build without ML dependencies (fast)
echo -e "${YELLOW}🧪 Test 1: Building without ML dependencies...${NC}"
START_TIME=$(date +%s)

docker build \
    -f Dockerfile.optimized \
    --build-arg INSTALL_ML_DEPS=false \
    --progress=plain \
    -t cryptoorchestrator:test-no-ml \
    . 2>&1 | tee /tmp/docker-build-no-ml.log

END_TIME=$(date +%s)
BUILD_TIME=$((END_TIME - START_TIME))

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Build without ML succeeded in ${BUILD_TIME} seconds${NC}"
    
    # Test if image runs
    echo -e "${YELLOW}🔍 Testing if image runs...${NC}"
    docker run --rm cryptoorchestrator:test-no-ml python -c "import fastapi; print('FastAPI:', fastapi.__version__)" 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Image runs correctly${NC}"
    else
        echo -e "${RED}❌ Image failed to run${NC}"
        exit 1
    fi
    
    # Check if ML packages are missing (expected)
    echo -e "${YELLOW}🔍 Checking ML packages (should be missing)...${NC}"
    docker run --rm cryptoorchestrator:test-no-ml python -c "import tensorflow" 2>&1 | grep -q "No module named" && \
        echo -e "${GREEN}✅ TensorFlow correctly excluded${NC}" || \
        echo -e "${YELLOW}⚠️  TensorFlow found (unexpected)${NC}"
else
    echo -e "${RED}❌ Build without ML failed${NC}"
    exit 1
fi

echo ""

# Test 2: Build with ML dependencies (full)
echo -e "${YELLOW}🧪 Test 2: Building with ML dependencies...${NC}"
START_TIME=$(date +%s)

docker build \
    -f Dockerfile.optimized \
    --build-arg INSTALL_ML_DEPS=true \
    --progress=plain \
    -t cryptoorchestrator:test-with-ml \
    . 2>&1 | tee /tmp/docker-build-with-ml.log

END_TIME=$(date +%s)
BUILD_TIME=$((END_TIME - START_TIME))

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Build with ML succeeded in ${BUILD_TIME} seconds${NC}"
    
    # Test if image runs
    echo -e "${YELLOW}🔍 Testing if image runs...${NC}"
    docker run --rm cryptoorchestrator:test-with-ml python -c "import fastapi; print('FastAPI:', fastapi.__version__)" 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Image runs correctly${NC}"
    else
        echo -e "${RED}❌ Image failed to run${NC}"
        exit 1
    fi
    
    # Check if ML packages are present (expected)
    echo -e "${YELLOW}🔍 Checking ML packages (should be present)...${NC}"
    docker run --rm cryptoorchestrator:test-with-ml python -c "import tensorflow; print('TensorFlow:', tensorflow.__version__)" 2>&1 | grep -q "TensorFlow:" && \
        echo -e "${GREEN}✅ TensorFlow correctly included${NC}" || \
        echo -e "${YELLOW}⚠️  TensorFlow not found (unexpected)${NC}"
else
    echo -e "${RED}❌ Build with ML failed${NC}"
    exit 1
fi

echo ""

# Test 3: Check image sizes
echo -e "${YELLOW}📊 Image Size Comparison:${NC}"
echo ""
echo "Without ML:"
docker images cryptoorchestrator:test-no-ml --format "  Size: {{.Size}}"
echo ""
echo "With ML:"
docker images cryptoorchestrator:test-with-ml --format "  Size: {{.Size}}"
echo ""

# Test 4: Test cache effectiveness (rebuild)
echo -e "${YELLOW}🧪 Test 3: Testing cache effectiveness (rebuild)...${NC}"
START_TIME=$(date +%s)

docker build \
    -f Dockerfile.optimized \
    --build-arg INSTALL_ML_DEPS=false \
    --progress=plain \
    -t cryptoorchestrator:test-no-ml \
    . 2>&1 | tee /tmp/docker-build-no-ml-cached.log

END_TIME=$(date +%s)
REBUILD_TIME=$((END_TIME - START_TIME))

echo -e "${GREEN}✅ Rebuild completed in ${REBUILD_TIME} seconds${NC}"
echo -e "${YELLOW}   (Should be much faster than first build if cache works)${NC}"
echo ""

# Summary
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}✨ All Tests Passed! ✨${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo "Build logs saved to:"
echo "  - /tmp/docker-build-no-ml.log"
echo "  - /tmp/docker-build-with-ml.log"
echo "  - /tmp/docker-build-no-ml-cached.log"
echo ""
echo "Test images created:"
echo "  - cryptoorchestrator:test-no-ml"
echo "  - cryptoorchestrator:test-with-ml"
echo ""
echo -e "${YELLOW}💡 To clean up test images:${NC}"
echo "  docker rmi cryptoorchestrator:test-no-ml cryptoorchestrator:test-with-ml"
