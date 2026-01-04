#!/bin/bash
# ==========================================
# Wait for Backend to be Ready
# ==========================================

echo "⏳ Waiting for backend to be ready..."

MAX_WAIT=120  # 2 minutes max
WAIT_TIME=0
INTERVAL=5

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    # Check if backend is healthy
    STATUS=$(sudo docker inspect crypto-orchestrator-backend --format='{{.State.Health.Status}}' 2>/dev/null)
    
    if [ "$STATUS" = "healthy" ]; then
        echo "✅ Backend is healthy!"
        break
    fi
    
    echo "   Backend status: $STATUS (waiting ${WAIT_TIME}s/${MAX_WAIT}s)..."
    sleep $INTERVAL
    WAIT_TIME=$((WAIT_TIME + INTERVAL))
done

# Final check
if [ "$STATUS" != "healthy" ]; then
    echo "⚠️  Backend not healthy after ${MAX_WAIT}s. Checking logs..."
    sudo docker-compose logs backend --tail 50
    exit 1
fi

# Test health endpoint
echo ""
echo "🏥 Testing health endpoint..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "Health endpoint not responding yet"

echo ""
echo "✅ Backend is ready!"
