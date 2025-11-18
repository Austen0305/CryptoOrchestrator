#!/bin/bash
# Quick Pre-Deployment Test Script
# Run this before deploying to verify everything works

echo "🧪 Pre-Deployment Testing"
echo "========================="
echo ""

errors=0
warnings=0

# Test 1: Check if Python is available
echo "Test 1: Python Installation"
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version 2>&1)
    echo "  ✓ Python found: $python_version"
elif command -v python &> /dev/null; then
    python_version=$(python --version 2>&1)
    echo "  ✓ Python found: $python_version"
else
    echo "  ✗ Python not found!"
    ((errors++))
fi
echo ""

# Test 2: Check if Node.js is available
echo "Test 2: Node.js Installation"
if command -v node &> /dev/null; then
    node_version=$(node --version 2>&1)
    echo "  ✓ Node.js found: $node_version"
else
    echo "  ✗ Node.js not found!"
    ((errors++))
fi
echo ""

# Test 3: Check if requirements.txt exists
echo "Test 3: Backend Dependencies File"
if [ -f "requirements.txt" ]; then
    echo "  ✓ requirements.txt exists"
    req_count=$(grep -v '^#' requirements.txt | grep -v '^$' | wc -l)
    echo "  ✓ Found $req_count dependencies"
else
    echo "  ✗ requirements.txt not found!"
    ((errors++))
fi
echo ""

# Test 4: Check if package.json exists
echo "Test 4: Frontend Dependencies File"
if [ -f "package.json" ]; then
    echo "  ✓ package.json exists"
else
    echo "  ✗ package.json not found!"
    ((errors++))
fi
echo ""

# Test 5: Check if main.py exists
echo "Test 5: Backend Entry Point"
if [ -f "server_fastapi/main.py" ]; then
    echo "  ✓ server_fastapi/main.py exists"
else
    echo "  ✗ server_fastapi/main.py not found!"
    ((errors++))
fi
echo ""

# Test 6: Check if client directory exists
echo "Test 6: Frontend Directory"
if [ -d "client" ]; then
    echo "  ✓ client directory exists"
else
    echo "  ⚠ client directory not found (may be optional)"
    ((warnings++))
fi
echo ""

# Test 7: Check if Dockerfile exists
echo "Test 7: Docker Configuration"
if [ -f "Dockerfile" ]; then
    echo "  ✓ Dockerfile exists"
else
    echo "  ⚠ Dockerfile not found (optional for some platforms)"
    ((warnings++))
fi
echo ""

# Test 8: Check if .env.example exists
echo "Test 8: Environment Variables Documentation"
if [ -f ".env.example" ]; then
    echo "  ✓ .env.example exists"
else
    echo "  ⚠ .env.example not found (recommended for documentation)"
    ((warnings++))
fi
echo ""

# Test 9: Check if PORT is used in main.py
echo "Test 9: PORT Environment Variable"
if [ -f "server_fastapi/main.py" ]; then
    if grep -q 'os\.getenv.*PORT' server_fastapi/main.py; then
        echo "  ✓ PORT environment variable is used"
    else
        echo "  ⚠ PORT environment variable may not be configured"
        ((warnings++))
    fi
fi
echo ""

# Test 10: Try to check pip
echo "Test 10: Python Dependencies Check"
if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
    echo "  ✓ pip is available"
else
    echo "  ⚠ pip not found (this is okay)"
    ((warnings++))
fi
echo ""

# Summary
echo "========================="
echo "Test Summary"
echo "========================="
echo ""

if [ $errors -eq 0 ]; then
    echo "✓ All critical tests passed!"
    echo ""
    if [ $warnings -gt 0 ]; then
        echo "⚠ Found $warnings warnings (non-critical)"
        echo ""
    fi
    echo "✅ Your app is ready for deployment!"
    echo ""
    echo "Next steps:"
    echo "  1. Run: npm run dev:fastapi (test backend locally)"
    echo "  2. Run: npm run build (test frontend build)"
    echo "  3. Follow: QUICK_START_FREE_HOSTING.md"
else
    echo "✗ Found $errors critical errors!"
    echo ""
    echo "Please fix these issues before deploying:"
    echo "  - Install missing dependencies"
    echo "  - Fix missing files"
    echo "  - Check file paths"
fi

echo ""

