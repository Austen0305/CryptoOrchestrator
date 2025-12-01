#!/bin/bash

# Feature Testing Script
# Helps test features systematically

FEATURE_NAME="$1"
PHASE="$2"

if [ -z "$FEATURE_NAME" ]; then
    echo "Usage: ./scripts/test_feature.sh <feature_name> [phase]"
    echo ""
    echo "Examples:"
    echo "  ./scripts/test_feature.sh login 1"
    echo "  ./scripts/test_feature.sh dashboard 1"
    echo "  ./scripts/test_feature.sh bot_creation 1"
    exit 1
fi

echo "🧪 Testing Feature: $FEATURE_NAME"
echo "📋 Phase: ${PHASE:-N/A}"
echo ""

# Start backend if not running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  Backend not running. Starting backend..."
    npm run dev:fastapi &
    BACKEND_PID=$!
    sleep 5
    echo "✅ Backend started (PID: $BACKEND_PID)"
fi

# Start frontend if not running
if ! curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "⚠️  Frontend not running. Starting frontend..."
    npm run dev &
    FRONTEND_PID=$!
    sleep 3
    echo "✅ Frontend started (PID: $FRONTEND_PID)"
fi

echo ""
echo "✅ Environment ready!"
echo ""
echo "📝 Testing Checklist:"
echo "  [ ] Feature loads correctly"
echo "  [ ] All interactions work"
echo "  [ ] Error handling works"
echo "  [ ] Loading states work"
echo "  [ ] Responsive design works"
echo "  [ ] Accessibility works"
echo ""
echo "🌐 Open http://localhost:5173 to test"
echo ""
echo "Press Ctrl+C to stop servers"

# Wait for user to finish testing
wait

