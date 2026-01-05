#!/bin/bash
# Simple Backend Test Script (without set -e)
# Tests critical components of the CryptoOrchestrator backend

echo "🚀 CryptoOrchestrator Backend Test"
echo "===================================="
echo ""

BASE_URL="http://localhost:8000"

echo "1. Container Status:"
echo "-------------------"
if sudo docker-compose ps backend | grep -q "Up (healthy)"; then
    echo "✅ Backend container is running and healthy"
else
    echo "❌ Backend container is not running or unhealthy"
fi
echo ""

echo "2. Healthz Endpoint:"
echo "-------------------"
HEALTHZ=$(curl -s "${BASE_URL}/healthz" 2>/dev/null)
if [ -n "$HEALTHZ" ]; then
    echo "✅ Healthz endpoint working: $HEALTHZ"
else
    echo "❌ Healthz endpoint not responding"
fi
echo ""

echo "3. Full Health Check:"
echo "--------------------"
HEALTH=$(curl -s "${BASE_URL}/api/health/" 2>/dev/null)
if [ -n "$HEALTH" ]; then
    echo "✅ Full health check endpoint working"
    echo "   Components status:"
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null | grep -A 1 '"database"\|"redis"\|"dex_aggregators"' | grep '"status"' | head -3 | sed 's/^/   /' || echo "   (Could not parse JSON)"
else
    echo "❌ Full health check endpoint not responding"
fi
echo ""

echo "4. Cache Warmer:"
echo "---------------"
CACHE_LOG=$(sudo docker-compose logs backend 2>&1 | grep -i "cache warmup cycle completed.*successful" | tail -1)
if [ -n "$CACHE_LOG" ]; then
    echo "✅ Cache warmer working:"
    echo "   $CACHE_LOG" | sed 's/^/   /'
else
    echo "⚠️  Cache warmer not run yet or no successful cycles found"
fi
echo ""

echo "5. Error Check:"
echo "--------------"
ERROR_COUNT=$(sudo docker-compose logs backend 2>&1 | tail -200 | grep -iE "error|exception" | grep -v "Circuit breaker is OPEN" | grep -v "Client error '401\|404'" | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo "✅ No critical errors found"
else
    echo "⚠️  Found $ERROR_COUNT potential errors (excluding expected circuit breaker and API auth errors)"
    sudo docker-compose logs backend 2>&1 | tail -200 | grep -iE "error|exception" | grep -v "Circuit breaker is OPEN" | grep -v "Client error '401\|404'" | tail -3 | sed 's/^/   /'
fi
echo ""

echo "===================================="
echo "Test Complete!"
echo "===================================="
