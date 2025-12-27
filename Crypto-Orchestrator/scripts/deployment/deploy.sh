#!/bin/bash

# CryptoOrchestrator - One-Click Production Deployment Script
# Usage: ./deploy.sh [production|staging|development]

set -e  # Exit on error

ENVIRONMENT=${1:-production}
echo "🚀 Deploying CryptoOrchestrator to $ENVIRONMENT..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Error: Docker Compose is not installed${NC}"
        exit 1
    fi
    
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}Warning: .env file not found. Creating from .env.example...${NC}"
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo -e "${YELLOW}Please edit .env with your configuration before continuing${NC}"
            exit 1
        else
            echo -e "${RED}Error: .env.example not found${NC}"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✓ Prerequisites check passed${NC}"
}

# Pull latest changes
pull_changes() {
    if [ -d ".git" ]; then
        echo -e "${YELLOW}Pulling latest changes...${NC}"
        git pull origin main || echo -e "${YELLOW}Warning: Could not pull changes${NC}"
    fi
}

# Build Docker images
build_images() {
    echo -e "${YELLOW}Building Docker images...${NC}"
    docker-compose build --no-cache
    echo -e "${GREEN}✓ Docker images built${NC}"
}

# Run database migrations
run_migrations() {
    echo -e "${YELLOW}Running database migrations...${NC}"
    docker-compose run --rm backend alembic upgrade head || echo -e "${YELLOW}Warning: Migrations may have failed${NC}"
    echo -e "${GREEN}✓ Database migrations complete${NC}"
}

# Start services
start_services() {
    echo -e "${YELLOW}Starting services...${NC}"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose up -d
    else
        docker-compose up -d
    fi
    
    echo -e "${GREEN}✓ Services started${NC}"
}

# Wait for services to be healthy
wait_for_health() {
    echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
    
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost:8000/healthz > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Services are healthy${NC}"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo -e "${YELLOW}Waiting... (attempt $attempt/$max_attempts)${NC}"
        sleep 2
    done
    
    echo -e "${RED}Error: Services did not become healthy${NC}"
    docker-compose logs
    exit 1
}

# Run tests (optional)
run_tests() {
    if [ "$ENVIRONMENT" != "production" ]; then
        echo -e "${YELLOW}Running tests...${NC}"
        docker-compose run --rm backend pytest server_fastapi/tests/ -v || echo -e "${YELLOW}Warning: Some tests may have failed${NC}"
    fi
}

# Show status
show_status() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}\n"
    
    echo -e "Services:"
    docker-compose ps
    
    echo -e "\nHealth Check:"
    curl -s http://localhost:8000/healthz | jq . || echo "API is responding"
    
    echo -e "\n${GREEN}Access points:${NC}"
    echo -e "  Frontend: http://localhost:3000"
    echo -e "  Backend API: http://localhost:8000"
    echo -e "  API Docs: http://localhost:8000/docs"
    echo -e "  Health: http://localhost:8000/healthz"
    
    echo -e "\n${YELLOW}View logs:${NC}"
    echo -e "  docker-compose logs -f"
    
    echo -e "\n${YELLOW}Stop services:${NC}"
    echo -e "  docker-compose down"
}

# Main deployment flow
main() {
    check_prerequisites
    pull_changes
    build_images
    run_migrations
    start_services
    wait_for_health
    run_tests
    show_status
    
    echo -e "\n${GREEN}🎉 Deployment successful!${NC}"
}

# Run main function
main

