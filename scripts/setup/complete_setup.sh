#!/bin/bash
# Complete Setup Script for Linux/Mac
# One-command setup for CryptoOrchestrator

set -e

echo "🚀 CryptoOrchestrator Complete Setup (Linux/Mac)"
echo "============================================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo "✅ Found: $PYTHON_VERSION"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

NODE_VERSION=$(node --version 2>&1)
echo "✅ Found: $NODE_VERSION"

# Run Python setup script
echo ""
echo "📦 Running complete setup..."
python3 scripts/setup/complete_setup.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Setup failed. Check errors above."
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next Steps:"
echo "  1. Start services: npm run start:all"
echo "  2. Verify health: npm run setup:health"
echo "  3. Verify features: npm run setup:verify"
