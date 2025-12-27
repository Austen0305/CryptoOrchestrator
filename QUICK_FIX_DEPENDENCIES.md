# Quick Fix: Install Testing Dependencies

## The Issue

The testing scripts require `web3` and `httpx` packages which are already in `requirements.txt` but may not be installed in your virtual environment.

## Quick Fix (PowerShell)

```powershell
# 1. Activate virtual environment (if not already activated)
.venv\Scripts\Activate.ps1

# 2. Install all requirements
pip install -r requirements.txt

# 3. Verify installation
python -c "import web3; print('web3 installed')"
python -c "import httpx; print('httpx installed')"

# 4. Run the testnet verification script
python scripts/testing/testnet_verification.py --network sepolia
```

## Alternative: Use Setup Script

```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run setup script
.\scripts\setup_testing_dependencies.ps1
```

## What Gets Installed

- **web3>=7.14.0** - For blockchain/testnet interactions
- **httpx>=0.25.2** - For HTTP requests
- All other dependencies from `requirements.txt`

## After Installation

You can now run all testing scripts:

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

## Need Help?

See `docs/TESTING_SCRIPTS_SETUP.md` for detailed setup instructions.
