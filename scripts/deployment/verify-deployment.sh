#!/bin/bash
# Verify deployment setup
# Run this after setting up HTTPS to verify everything is working

set -e

echo "🔍 Verifying CryptoOrchestrator Deployment"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get backend URL
read -p "Enter your backend URL (e.g., https://api.example.com or http://34.16.15.56): " BACKEND_URL
if [ -z "$BACKEND_URL" ]; then
    echo -e "${RED}❌ Backend URL is required${NC}"
    exit 1
fi

# Remove trailing slash
BACKEND_URL=${BACKEND_URL%/}

echo ""
echo "Testing backend at: $BACKEND_URL"
echo ""

# Test 1: Backend Health
echo -n "1. Testing backend health endpoint... "
if curl -s -f "${BACKEND_URL}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS${NC}"
    HEALTH_RESPONSE=$(curl -s "${BACKEND_URL}/health")
    echo "   Response: $HEALTH_RESPONSE"
else
    echo -e "${RED}❌ FAIL${NC}"
    echo "   Backend health endpoint not accessible"
    FAILED=true
fi

# Test 2: API Documentation
echo -n "2. Testing API documentation... "
if curl -s -f "${BACKEND_URL}/docs" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS${NC}"
    echo "   Visit: ${BACKEND_URL}/docs"
else
    echo -e "${YELLOW}⚠️  WARNING${NC}"
    echo "   API docs not accessible (may be normal if /docs is disabled)"
fi

# Test 3: CORS Headers
echo -n "3. Testing CORS headers... "
CORS_HEADER=$(curl -s -I -X OPTIONS "${BACKEND_URL}/health" | grep -i "access-control-allow-origin" || echo "")
if [ -n "$CORS_HEADER" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    echo "   $CORS_HEADER"
else
    echo -e "${YELLOW}⚠️  WARNING${NC}"
    echo "   CORS headers not found (may cause issues with frontend)"
fi

# Test 4: SSL Certificate (if HTTPS)
if [[ "$BACKEND_URL" == https://* ]]; then
    echo -n "4. Testing SSL certificate... "
    SSL_INFO=$(echo | openssl s_client -connect "${BACKEND_URL#https://}" -servername "${BACKEND_URL#https://}" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "")
    if [ -n "$SSL_INFO" ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        echo "$SSL_INFO" | head -2
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "   SSL certificate not valid"
        FAILED=true
    fi
else
    echo -e "${YELLOW}⚠️  4. Skipping SSL test (using HTTP)${NC}"
fi

# Test 5: Nginx Status
echo -n "5. Testing nginx service... "
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ PASS${NC}"
    echo "   Nginx is running"
else
    echo -e "${RED}❌ FAIL${NC}"
    echo "   Nginx is not running"
    FAILED=true
fi

# Test 6: Backend Process
echo -n "6. Testing backend process... "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS${NC}"
    echo "   Backend is running on localhost:8000"
else
    echo -e "${RED}❌ FAIL${NC}"
    echo "   Backend not responding on localhost:8000"
    FAILED=true
fi

# Summary
echo ""
echo "=========================================="
if [ "$FAILED" = true ]; then
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Check backend logs: sudo journalctl -u your-backend-service -f"
    echo "2. Check nginx logs: sudo tail -f /var/log/nginx/error.log"
    echo "3. Verify backend is running: curl http://localhost:8000/health"
    echo "4. Check nginx config: sudo nginx -t"
    exit 1
else
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Your backend is ready!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Set Vercel environment variable:"
    echo "   VITE_API_URL=${BACKEND_URL}/api"
    echo ""
    echo "2. Redeploy your Vercel frontend"
    echo ""
    echo "3. Test the frontend connection"
    exit 0
fi
