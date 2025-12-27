# Quick Start: Testing Scripts

## Python 3.13 Compatibility Issue

If you're using Python 3.13, TensorFlow is not yet available, which prevents installing the full `requirements.txt`.

## Solution: Install Testing Dependencies Only

### Option 1: Use Testing-Only Requirements (Recommended)

```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install only testing dependencies
pip install -r requirements-testing.txt
```

### Option 2: Install Packages Individually

```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install essential packages for testing scripts
pip install web3>=7.14.0 httpx>=0.25.2
```

## Verify Installation

```powershell
python -c "import web3; import httpx; print('web3:', web3.__version__); print('httpx:', httpx.__version__)"
```

## Run Testing Scripts

Once dependencies are installed:

```powershell
# Testnet verification
python scripts/testing/testnet_verification.py --network sepolia

# Performance baseline
python scripts/monitoring/set_performance_baseline.py

# Security audit
python scripts/security/security_audit.py

# Load testing
python scripts/testing/load_test.py
```

## Note on Full Project

For the full project (including ML features with TensorFlow), you'll need:
- **Python 3.11** or **Python 3.12** (TensorFlow doesn't support Python 3.13 yet)

The testing scripts work fine with Python 3.13 since they don't require TensorFlow.
