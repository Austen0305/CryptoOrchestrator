#!/bin/bash
# ==========================================
# Diagnose Backend Startup Issues
# ==========================================

echo "🔍 Diagnosing backend startup issues..."
echo ""

# Check all containers
echo "=== All Containers ==="
sudo docker ps -a

echo ""
echo "=== Docker Compose Services ==="
sudo docker-compose ps

echo ""
echo "=== Backend Logs ==="
sudo docker-compose logs backend 2>&1 | tail -100

echo ""
echo "=== Postgres Status ==="
sudo docker-compose ps postgres

echo ""
echo "=== Redis Status ==="
sudo docker-compose ps redis

echo ""
echo "=== Network Status ==="
sudo docker network ls | grep crypto

echo ""
echo "=== Try to start backend manually ==="
sudo docker-compose up -d backend 2>&1
