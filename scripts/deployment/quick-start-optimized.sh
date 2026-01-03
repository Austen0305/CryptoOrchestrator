#!/bin/bash
# ==========================================
# Quick Start with Optimized Docker Build
# ==========================================

set -e

echo "🚀 Starting optimized deployment..."

# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull

# Start only essential services (no celery-worker)
echo "🐳 Starting services with optimized Dockerfile..."
sudo DOCKER_BUILDKIT=1 docker-compose up -d postgres redis backend

# Wait a bit for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check status
echo ""
echo "📊 Service Status:"
sudo docker-compose ps

echo ""
echo "🏥 Health Check:"
curl -s http://localhost:8000/health | python3 -m json.tool || echo "Backend not ready yet"

echo ""
echo "✅ Done! Check the status above."
