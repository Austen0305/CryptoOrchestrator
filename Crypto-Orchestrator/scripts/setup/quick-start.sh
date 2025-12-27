#!/bin/bash
# CryptoOrchestrator Quick Start Script (Unix)
# Automates the complete setup process

set -e

echo "🚀 CryptoOrchestrator Quick Start"
echo "================================="
echo ""

# Check Python
echo "Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ $PYTHON_VERSION"
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    echo "✓ $PYTHON_VERSION"
    PYTHON_CMD=python
else
    echo "✗ Python not found. Please install Python 3.11+"
    exit 1
fi

# Check Node.js
echo "Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✓ $NODE_VERSION"
else
    echo "✗ Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check if .env exists
echo ""
echo "Checking environment..."
if [ -f ".env" ]; then
    echo "✓ .env file exists"
else
    echo "⚠ .env file not found, creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✓ .env file created"
    else
        echo "✗ .env.example not found"
        exit 1
    fi
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
$PYTHON_CMD -m pip install -q -r requirements.txt || echo "⚠ Some Python dependencies may have failed (continuing...)"

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install --legacy-peer-deps --silent || echo "⚠ Some Node.js dependencies may have failed (continuing...)"

# Initialize database
echo ""
echo "Initializing database..."
mkdir -p data
alembic upgrade head || echo "⚠ Database initialization had issues (you may need to run 'alembic upgrade head' manually)"

# Verify installation
echo ""
echo "Verifying installation..."
$PYTHON_CMD scripts/verification/startup_verification.py || echo "⚠ Verification had warnings (check output above)"

echo ""
echo "✅ Setup Complete!"
echo ""
echo "Next steps:"
echo "  1. Start services: npm run start:all"
echo "  2. Access frontend: http://localhost:5173"
echo "  3. Access API docs: http://localhost:8000/docs"
echo ""

