#!/bin/bash
# Docker Deployment Automation Script
# Handles building, tagging, and deploying Docker containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY=${DOCKER_REGISTRY:-"ghcr.io"}
IMAGE_NAME=${DOCKER_IMAGE_NAME:-"cryptoorchestrator"}
VERSION=${VERSION:-$(git describe --tags --always)}
ENVIRONMENT=${ENVIRONMENT:-"staging"}

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Build Docker image
build_image() {
    log "Building Docker image..."
    docker build \
        -t "${IMAGE_NAME}:${VERSION}" \
        -t "${IMAGE_NAME}:latest" \
        -t "${REGISTRY}/${IMAGE_NAME}:${VERSION}" \
        -t "${REGISTRY}/${IMAGE_NAME}:latest" \
        -f Dockerfile \
        .
    
    log "✓ Docker image built successfully"
}

# Run security scan
security_scan() {
    log "Running security scan..."
    if command -v trivy &> /dev/null; then
        trivy image --exit-code 0 --severity HIGH,CRITICAL "${IMAGE_NAME}:${VERSION}" || warn "Security scan found issues"
    else
        warn "Trivy not installed, skipping security scan"
    fi
}

# Push to registry
push_image() {
    if [ -z "$DOCKER_USERNAME" ] || [ -z "$DOCKER_PASSWORD" ]; then
        warn "DOCKER_USERNAME or DOCKER_PASSWORD not set, skipping push"
        return
    fi
    
    log "Logging into Docker registry..."
    echo "$DOCKER_PASSWORD" | docker login "${REGISTRY}" -u "$DOCKER_USERNAME" --password-stdin
    
    log "Pushing images to registry..."
    docker push "${REGISTRY}/${IMAGE_NAME}:${VERSION}"
    docker push "${REGISTRY}/${IMAGE_NAME}:latest"
    
    log "✓ Images pushed successfully"
}

# Deploy with docker-compose
deploy_compose() {
    log "Deploying with docker-compose..."
    
    # Update environment variables
    export IMAGE_TAG="${VERSION}"
    export ENV="${ENVIRONMENT}"
    
    # Use environment-specific compose file if exists
    COMPOSE_FILE="docker-compose.yml"
    if [ -f "docker-compose.${ENVIRONMENT}.yml" ]; then
        COMPOSE_FILE="docker-compose.yml:docker-compose.${ENVIRONMENT}.yml"
    fi
    
    docker-compose -f docker-compose.yml pull
    docker-compose -f docker-compose.yml up -d --force-recreate
    
    log "✓ Deployment completed"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    docker-compose exec -T backend python -m alembic upgrade head || error "Migrations failed"
    log "✓ Migrations completed"
}

# Health check
health_check() {
    log "Performing health check..."
    MAX_RETRIES=30
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log "✓ Health check passed"
            return 0
        fi
        
        RETRY_COUNT=$((RETRY_COUNT + 1))
        sleep 2
    done
    
    error "Health check failed after $MAX_RETRIES attempts"
    return 1
}

# Rollback
rollback() {
    warn "Rolling back to previous version..."
    PREVIOUS_VERSION=$(docker images "${IMAGE_NAME}" --format "{{.Tag}}" | grep -v latest | head -1)
    
    if [ -z "$PREVIOUS_VERSION" ]; then
        error "No previous version found"
        return 1
    fi
    
    export IMAGE_TAG="${PREVIOUS_VERSION}"
    docker-compose -f docker-compose.yml up -d --force-recreate
    
    log "✓ Rolled back to ${PREVIOUS_VERSION}"
}

# Main execution
main() {
    case "${1:-build}" in
        build)
            build_image
            ;;
        scan)
            build_image
            security_scan
            ;;
        push)
            build_image
            push_image
            ;;
        deploy)
            build_image
            security_scan
            push_image
            deploy_compose
            run_migrations
            health_check
            ;;
        migrate)
            run_migrations
            ;;
        health)
            health_check
            ;;
        rollback)
            rollback
            ;;
        *)
            echo "Usage: $0 {build|scan|push|deploy|migrate|health|rollback}"
            exit 1
            ;;
    esac
}

main "$@"

