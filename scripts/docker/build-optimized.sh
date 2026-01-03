#!/bin/bash
# ==========================================
# Optimized Docker Build Script
# ==========================================
# Usage:
#   ./scripts/docker/build-optimized.sh [--no-ml] [--push] [--tag TAG]
# ==========================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
INSTALL_ML_DEPS=true
PUSH=false
TAG="cryptoorchestrator:latest"
DOCKERFILE="Dockerfile.optimized"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --no-ml)
      INSTALL_ML_DEPS=false
      shift
      ;;
    --push)
      PUSH=true
      shift
      ;;
    --tag)
      TAG="$2"
      shift 2
      ;;
    --dockerfile)
      DOCKERFILE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--no-ml] [--push] [--tag TAG] [--dockerfile FILE]"
      exit 1
      ;;
  esac
done

# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

echo -e "${GREEN}🚀 Building optimized Docker image...${NC}"
echo -e "  Dockerfile: ${DOCKERFILE}"
echo -e "  ML Dependencies: ${INSTALL_ML_DEPS}"
echo -e "  Tag: ${TAG}"
echo ""

# Build the image
START_TIME=$(date +%s)

docker build \
  -f "${DOCKERFILE}" \
  --build-arg INSTALL_ML_DEPS="${INSTALL_ML_DEPS}" \
  --progress=plain \
  -t "${TAG}" \
  .

END_TIME=$(date +%s)
BUILD_TIME=$((END_TIME - START_TIME))

echo ""
echo -e "${GREEN}✅ Build completed in ${BUILD_TIME} seconds${NC}"

# Show image size
IMAGE_SIZE=$(docker images "${TAG}" --format "{{.Size}}")
echo -e "  Image size: ${IMAGE_SIZE}"

# Push if requested
if [ "$PUSH" = true ]; then
  echo -e "${YELLOW}📤 Pushing image to registry...${NC}"
  docker push "${TAG}"
  echo -e "${GREEN}✅ Image pushed successfully${NC}"
fi

echo ""
echo -e "${GREEN}✨ Done!${NC}"
