#!/bin/bash
# ==========================================
# Stop Current Build and Fix Deployment
# ==========================================

set -e

echo "🛑 Stopping current build and containers..."

# Stop all containers
sudo docker-compose down 2>/dev/null || true

# Kill any running builds
sudo docker ps -a | grep -E "build|celery" | awk '{print $1}' | xargs -r sudo docker rm -f

# Clean up aggressively
echo "🧹 Cleaning up disk space..."
sudo docker system prune -a -f --volumes
sudo docker builder prune -a -f

# Check disk space
echo ""
echo "📊 Current disk space:"
df -h

echo ""
echo "✅ Cleanup complete. Ready for optimized build."
