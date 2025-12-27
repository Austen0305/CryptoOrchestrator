#!/bin/bash
# Setup Testing Dependencies
# Installs all dependencies needed for testing scripts

echo "🔧 Setting up testing dependencies..."

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Virtual environment not detected."
    echo "   Activate your virtual environment first:"
    echo "   source .venv/bin/activate  # Linux/Mac"
    echo "   .venv\\Scripts\\Activate.ps1  # Windows PowerShell"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install requirements
echo "📦 Installing requirements..."
pip install -r requirements.txt

# Install dev requirements (includes testing tools)
echo "📦 Installing dev requirements..."
pip install -r requirements-dev.txt

# Verify critical packages
echo "✅ Verifying critical packages..."
python -c "import web3; print(f'  ✅ web3 {web3.__version__}')" || echo "  ❌ web3 not installed"
python -c "import httpx; print(f'  ✅ httpx {httpx.__version__}')" || echo "  ❌ httpx not installed"
python -c "import pytest; print(f'  ✅ pytest {pytest.__version__}')" || echo "  ❌ pytest not installed"

echo ""
echo "✅ Setup complete!"
echo ""
echo "You can now run:"
echo "  python scripts/testing/testnet_verification.py --network sepolia"
echo "  python scripts/monitoring/set_performance_baseline.py"
echo "  python scripts/security/security_audit.py"
echo "  python scripts/testing/load_test.py"
