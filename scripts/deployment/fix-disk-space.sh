#!/bin/bash
# ==========================================
# Fix Disk Space Issues
# ==========================================
# Cleans up Docker to free disk space
# ==========================================

set -e

echo "🔍 Checking disk space..."
df -h

echo ""
echo "🧹 Cleaning up Docker..."

# Remove stopped containers
echo "Removing stopped containers..."
sudo docker container prune -f

# Remove unused images
echo "Removing unused images..."
sudo docker image prune -a -f

# Remove unused volumes
echo "Removing unused volumes..."
sudo docker volume prune -f

# Remove build cache
echo "Removing build cache..."
sudo docker builder prune -a -f

# Remove all unused resources
echo "Removing all unused resources..."
sudo docker system prune -a -f --volumes

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Disk space after cleanup:"
df -h
