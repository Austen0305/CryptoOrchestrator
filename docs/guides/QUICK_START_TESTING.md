# Quick Start Testing Guide

Get up and running with the complete E2E test suite in minutes.

## One Command to Rule Them All

```bash
npm run test:e2e:complete
```

This single command will:
- ✅ Validate your environment
- ✅ Start all services (PostgreSQL, Redis, FastAPI, Frontend)
- ✅ Run Playwright E2E tests
- ✅ Run Puppeteer tests
- ✅ Generate comprehensive test reports
- ✅ Clean up services

## Prerequisites

1. **Node.js 18+** installed
2. **Python 3.12+** installed
3. **Dependencies** installed:
   ```bash
   npm install
   pip install -r requirements.txt
   ```

## Quick Commands

### Run All Tests
```bash
npm run test:e2e:complete
```

### Start Services Only
```bash
npm run start:all
```

### Run Individual Test Suites
```bash
# Playwright only
npm run test:e2e

# Puppeteer only
npm run test:puppeteer

# Backend tests
npm test

# Frontend tests
npm run test:frontend
```

### Validation & Diagnostics
```bash
# Check environment
npm run validate:env

# Check service health
npm run check:services

# Detect issues
node scripts/detect-issues.js

# Auto-fix issues
node scripts/auto-fix.js

# Pre-flight check
node scripts/preflight-check.js
```

## First Time Setup

1. **Install dependencies**:
   ```bash
   npm install
   pip install -r requirements.txt
   ```

2. **Set up environment**:
   ```bash
   # Create .env from example
   cp .env.example .env
   
   # Or auto-fix
   node scripts/auto-fix.js
   ```

3. **Validate setup**:
   ```bash
   npm run validate:env
   ```

4. **Run tests**:
   ```bash
   npm run test:e2e:complete
   ```

## Troubleshooting

### Port Already in Use
```bash
# Detect the issue
node scripts/detect-issues.js

# Auto-fix (if possible)
node scripts/auto-fix.js

# Or manually stop the service
# Windows: netstat -ano | findstr :8000
# Linux/Mac: lsof -i :8000
```

### Missing Dependencies
```bash
# Install everything
npm install
pip install -r requirements.txt

# Verify
node scripts/preflight-check.js
```

### Services Won't Start
```bash
# Check what's wrong
node scripts/detect-issues.js

# Check service health
npm run check:services

# Review logs in terminal
```

## Test Reports

After running tests, find reports in:
- **HTML Report**: `test-results/combined-report.html`
- **JSON Report**: `test-results/combined-results.json`
- **Screenshots**: `tests/puppeteer/screenshots/`

## What Gets Tested

### Playwright Tests (17 test files)
- Authentication flows
- Bot management
- Dashboard functionality
- DEX trading
- Wallet operations
- Trading operations
- Critical user journeys
- And more...

### Puppeteer Tests (4 test files)
- Authentication flow
- Bot management
- DEX trading
- Wallet operations

## Next Steps

- Read [Complete Testing Guide](docs/TESTING_COMPLETE.md) for detailed documentation
- Check [Troubleshooting](docs/TESTING_COMPLETE.md#troubleshooting) for common issues
- Review [Test Writing Guidelines](docs/TESTING_COMPLETE.md#test-writing-guidelines) to add tests

## Support

If you encounter issues:
1. Run `node scripts/detect-issues.js`
2. Run `node scripts/auto-fix.js`
3. Check `test-results/` for detailed logs
4. Review [Complete Testing Guide](docs/TESTING_COMPLETE.md)
