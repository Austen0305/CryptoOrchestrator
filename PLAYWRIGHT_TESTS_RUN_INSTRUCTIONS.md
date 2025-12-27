# Playwright Tests - Manual Run Instructions

## ⚠️ Installation Issue

There appears to be a dependency conflict preventing `@playwright/test` from installing properly. Here's how to fix it and run the tests:

## 🔧 Fix Installation

### Option 1: Clean Install
```bash
# Remove node_modules and package-lock.json
Remove-Item -Recurse -Force node_modules
Remove-Item -Force package-lock.json

# Reinstall everything
npm install --legacy-peer-deps --ignore-scripts

# Install Playwright specifically
npm install @playwright/test@1.57.0 --save-dev --legacy-peer-deps

# Install browsers
npx playwright install chromium
```

### Option 2: Manual Installation
```bash
# Install Playwright directly
npm install @playwright/test@1.57.0 playwright@1.57.0 --save-dev --legacy-peer-deps --force

# Install browsers
npx playwright install chromium
```

## 🚀 Run Tests

### Step 1: Start Backend Server
Open Terminal 1:
```bash
cd "C:\Users\William Walker\OneDrive\Desktop\CryptoOrchestrator\Crypto-Orchestrator"
npm run dev:fastapi
```

Or:
```bash
python -m uvicorn server_fastapi.main:app --port 8000 --host 127.0.0.1
```

Wait for: `Uvicorn running on http://127.0.0.1:8000`

### Step 2: Start Frontend Server
Open Terminal 2:
```bash
cd "C:\Users\William Walker\OneDrive\Desktop\CryptoOrchestrator\Crypto-Orchestrator"
npm run dev
```

Wait for: `Local: http://localhost:5173/`

### Step 3: Run All Tests
Open Terminal 3:
```bash
cd "C:\Users\William Walker\OneDrive\Desktop\CryptoOrchestrator\Crypto-Orchestrator"
npx playwright test --reporter=list --timeout=60000
```

### Run Specific Tests
```bash
# Comprehensive UI test
npx playwright test tests/e2e/comprehensive-ui-test.spec.ts

# Wallet tests
npx playwright test tests/e2e/wallet.spec.ts

# DEX swap tests
npx playwright test tests/e2e/dex-swap.spec.ts

# Dashboard tests
npx playwright test tests/e2e/dashboard.spec.ts

# All tests with UI mode
npx playwright test --ui

# All tests with headed browser (see what's happening)
npx playwright test --headed
```

## 📊 Test Results

After running tests, check:
- **HTML Report**: `playwright-report/index.html` - Open in browser
- **Screenshots**: `test-results/` directory
- **Videos**: `test-results/` directory (on failures)
- **JSON Results**: `test-results/results.json`

## ✅ What Tests Are Available

Your project has 20+ E2E test files:

1. `comprehensive-ui-test.spec.ts` - **NEW** - Tests all pages and features
2. `wallet.spec.ts` - Wallet operations
3. `dex-swap.spec.ts` - DEX trading
4. `dashboard.spec.ts` - Dashboard
5. `bots.spec.ts` - Bot management
6. `trading.spec.ts` - Trading functionality
7. `auth.spec.ts` - Authentication
8. `registration.spec.ts` - User registration
9. `settings-updates.spec.ts` - Settings
10. `portfolio-management.spec.ts` - Portfolio
11. `trading-mode-switching.spec.ts` - Mode switching
12. `withdrawal-flow.spec.ts` - Withdrawals
13. `critical-flows.spec.ts` - Critical flows
14. `dex-trading-flow.spec.ts` - DEX flows
15. `wallet-management.spec.ts` - Wallet management
16. `app.spec.ts` - App-wide tests
17. `analytics.spec.ts` - Analytics
18. `markets.spec.ts` - Markets
19. `dex-trading.spec.ts` - DEX features
20. `wallets.spec.ts` - Multi-wallet
21. `trading-mode.spec.ts` - Trading mode

## 🎯 Test Coverage

The comprehensive test suite tests:
- ✅ Homepage loading
- ✅ Navigation to all pages
- ✅ Form interactions
- ✅ Button clicks
- ✅ Responsive design
- ✅ Error handling
- ✅ Loading states
- ✅ Screenshots of all pages

## 📝 Notes

- Tests automatically create test database (`test_e2e.db`)
- Tests use authentication helpers
- All tests take screenshots
- Failed tests record videos
- Tests have 60-second timeout
- Tests retry 2 times on failure

---

**Status**: Test files are ready. Once Playwright is properly installed, all tests can be run.

