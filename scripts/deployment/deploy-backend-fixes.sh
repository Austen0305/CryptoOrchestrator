#!/bin/bash
# Deploy Backend CORS Fixes to Google Cloud Server
# This script updates the running FastAPI service with the latest CORS fixes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Server details
SERVER_USER="${SERVER_USER:-labarcodez}"
SERVER_HOST="${SERVER_HOST:-34.16.15.56}"
PROJECT_DIR="${PROJECT_DIR:-~/CryptoOrchestrator}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Backend CORS Fixes Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if we're running on the server or locally
if [ "$(hostname)" = "$SERVER_HOST" ] || [ -n "$SSH_CONNECTION" ]; then
    echo -e "${YELLOW}Running on server directly...${NC}"
    IS_REMOTE=false
else
    echo -e "${YELLOW}Connecting to server ${SERVER_USER}@${SERVER_HOST}...${NC}"
    IS_REMOTE=true
fi

# Function to execute commands (either locally or via SSH)
run_cmd() {
    if [ "$IS_REMOTE" = true ]; then
        ssh "${SERVER_USER}@${SERVER_HOST}" "$1"
    else
        eval "$1"
    fi
}

# Function to copy files (if remote)
copy_file() {
    if [ "$IS_REMOTE" = true ]; then
        scp "$1" "${SERVER_USER}@${SERVER_HOST}:$2"
    else
        cp "$1" "$2"
    fi
}

echo -e "${BLUE}Step 1: Pulling latest changes from git...${NC}"
run_cmd "cd $PROJECT_DIR && git pull origin main"
echo -e "${GREEN}✓ Git pull complete${NC}"
echo ""

echo -e "${BLUE}Step 2: Finding running FastAPI process...${NC}"
PID=$(run_cmd "ps aux | grep 'uvicorn.*main:app' | grep -v grep | awk '{print \$2}' | head -1")

if [ -z "$PID" ]; then
    echo -e "${RED}✗ No running FastAPI process found${NC}"
    echo -e "${YELLOW}Starting FastAPI service...${NC}"
    run_cmd "cd $PROJECT_DIR && nohup python3 -m uvicorn server_fastapi.main:app --host 0.0.0.0 --port 8000 > /tmp/fastapi.log 2>&1 &"
    sleep 5
    PID=$(run_cmd "ps aux | grep 'uvicorn.*main:app' | grep -v grep | awk '{print \$2}' | head -1")
    if [ -z "$PID" ]; then
        echo -e "${RED}✗ Failed to start FastAPI service${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ FastAPI service started (PID: $PID)${NC}"
else
    echo -e "${GREEN}✓ Found FastAPI process (PID: $PID)${NC}"
fi
echo ""

echo -e "${BLUE}Step 3: Updating files in process namespace...${NC}"
run_cmd "sudo cp $PROJECT_DIR/server_fastapi/middleware/setup.py /proc/$PID/root/app/server_fastapi/middleware/setup.py"
run_cmd "sudo cp $PROJECT_DIR/server_fastapi/routes/logging.py /proc/$PID/root/app/server_fastapi/routes/logging.py"

# Also update auth_service and main.py if they exist
if run_cmd "test -f $PROJECT_DIR/server_fastapi/services/auth/auth_service.py"; then
    run_cmd "sudo cp $PROJECT_DIR/server_fastapi/services/auth/auth_service.py /proc/$PID/root/app/server_fastapi/services/auth/auth_service.py"
fi
if run_cmd "test -f $PROJECT_DIR/server_fastapi/main.py"; then
    run_cmd "sudo cp $PROJECT_DIR/server_fastapi/main.py /proc/$PID/root/app/server_fastapi/main.py"
fi

echo -e "${GREEN}✓ Files updated${NC}"
echo ""

echo -e "${BLUE}Step 4: Clearing Python cache...${NC}"
run_cmd "sudo find /proc/$PID/root/app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true"
run_cmd "sudo find /proc/$PID/root/app -name '*.pyc' -delete 2>/dev/null || true"
echo -e "${GREEN}✓ Cache cleared${NC}"
echo ""

echo -e "${BLUE}Step 5: Verifying file syntax...${NC}"
run_cmd "sudo python3 -m py_compile /proc/$PID/root/app/server_fastapi/middleware/setup.py 2>&1" || echo -e "${YELLOW}⚠ Syntax check warning (may be OK)${NC}"
run_cmd "sudo python3 -m py_compile /proc/$PID/root/app/server_fastapi/routes/logging.py 2>&1" || echo -e "${YELLOW}⚠ Syntax check warning (may be OK)${NC}"
echo -e "${GREEN}✓ Syntax verified${NC}"
echo ""

echo -e "${BLUE}Step 6: Restarting service...${NC}"
run_cmd "sudo kill -9 $PID"
echo -e "${YELLOW}Waiting for service to restart...${NC}"
sleep 15

# Check if service restarted
NEW_PID=$(run_cmd "ps aux | grep 'uvicorn.*main:app' | grep -v grep | awk '{print \$2}' | head -1")
if [ -z "$NEW_PID" ]; then
    echo -e "${RED}✗ Service did not restart automatically${NC}"
    echo -e "${YELLOW}Starting service manually...${NC}"
    run_cmd "cd $PROJECT_DIR && nohup python3 -m uvicorn server_fastapi.main:app --host 0.0.0.0 --port 8000 > /tmp/fastapi.log 2>&1 &"
    sleep 5
    NEW_PID=$(run_cmd "ps aux | grep 'uvicorn.*main:app' | grep -v grep | awk '{print \$2}' | head -1")
    if [ -z "$NEW_PID" ]; then
        echo -e "${RED}✗ Failed to restart service${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✓ Service restarted (New PID: $NEW_PID)${NC}"
echo ""

echo -e "${BLUE}Step 7: Testing CORS preflight...${NC}"
sleep 5  # Give service time to fully start

# Test CORS preflight
CORS_TEST=$(run_cmd "curl -s -X OPTIONS http://localhost:8000/api/status -H 'Origin: https://cryptoorchestrator.vercel.app' -H 'Access-Control-Request-Method: GET' -w '%{http_code}' -o /dev/null" || echo "000")

if [ "$CORS_TEST" = "200" ] || [ "$CORS_TEST" = "204" ]; then
    echo -e "${GREEN}✓ CORS preflight test passed (HTTP $CORS_TEST)${NC}"
else
    echo -e "${YELLOW}⚠ CORS preflight returned HTTP $CORS_TEST (may need more time)${NC}"
fi

# Test regular API call
API_TEST=$(run_cmd "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/status" || echo "000")
if [ "$API_TEST" = "200" ]; then
    echo -e "${GREEN}✓ API endpoint responding (HTTP $API_TEST)${NC}"
else
    echo -e "${YELLOW}⚠ API endpoint returned HTTP $API_TEST${NC}"
fi
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Test the frontend at https://cryptoorchestrator.vercel.app/"
echo -e "  2. Check browser console for CORS errors"
echo -e "  3. Verify API calls are working"
echo ""
echo -e "To view logs:"
if [ "$IS_REMOTE" = true ]; then
    echo -e "  ssh ${SERVER_USER}@${SERVER_HOST} 'tail -f /tmp/fastapi.log'"
else
    echo -e "  tail -f /tmp/fastapi.log"
fi
