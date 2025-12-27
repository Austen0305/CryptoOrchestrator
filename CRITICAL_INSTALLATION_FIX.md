# Critical: Package Installation Fix Required

## ⚠️ Issue

Both `@playwright/test` and `puppeteer` are not installing into `node_modules` despite npm reporting successful installation. This is preventing all E2E tests from running.

## 🔍 Diagnosis

- ✅ npm reports packages as "installed"
- ❌ Packages not found in `node_modules/@playwright/test` or `node_modules/puppeteer`
- ❌ Node.js cannot resolve the packages
- ⚠️ This appears to be a Windows/OneDrive/npm environment issue

## 🔧 REQUIRED FIX (Choose One)

### Option 1: Complete Clean Install (RECOMMENDED)

```powershell
# Navigate to project
cd "C:\Users\William Walker\OneDrive\Desktop\CryptoOrchestrator\Crypto-Orchestrator"

# Close any running Node processes
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force

# Remove everything
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
Remove-Item -Force package-lock.json -ErrorAction SilentlyContinue
Remove-Item -Force .npmrc -ErrorAction SilentlyContinue

# Clear npm cache
npm cache clean --force

# Reinstall ALL dependencies
npm install --legacy-peer-deps --ignore-scripts

# Verify installation
Test-Path "node_modules/@playwright/test/package.json"
Test-Path "node_modules/puppeteer/package.json"
# Both should return True

# Install Playwright browsers
npx playwright install chromium
```

### Option 2: Use Yarn (Alternative)

```powershell
# Install yarn globally if needed
npm install -g yarn

# Remove node_modules
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue

# Install with yarn
yarn install

# Install testing frameworks
yarn add -D @playwright/test@1.57.0 puppeteer@latest

# Install browsers
npx playwright install chromium
```

### Option 3: Manual Package Installation

If npm continues to fail, try installing packages one at a time:

```powershell
# Install Playwright
npm install @playwright/test@1.57.0 --save-dev --legacy-peer-deps --force --no-save

# Verify it exists
Get-ChildItem "node_modules\@playwright\test" -ErrorAction SilentlyContinue

# Install Puppeteer
npm install puppeteer@latest --save-dev --legacy-peer-deps --force --no-save

# Verify it exists
Get-ChildItem "node_modules\puppeteer" -ErrorAction SilentlyContinue

# Install browsers
npx playwright install chromium
```

## ✅ Verification

After installation, verify packages exist:

```powershell
# Check Playwright
Test-Path "node_modules\@playwright\test\package.json"
# Should return: True

# Check Puppeteer
Test-Path "node_modules\puppeteer\package.json"
# Should return: True

# Try importing
node --input-type=module -e "import('@playwright/test').then(() => console.log('OK')).catch(e => console.log('FAIL:', e.message))"
# Should print: OK
```

## 🚀 Once Fixed, Run Tests

### Start Servers (if not running)
```powershell
# Terminal 1: Backend
npm run dev:fastapi

# Terminal 2: Frontend
npm run dev
```

### Run All Tests
```powershell
# Terminal 3: Playwright
npx playwright test --reporter=list,html

# Terminal 4: Puppeteer
npm run test:puppeteer
```

## 📊 What Will Be Tested

### Playwright (21 test files)
- Comprehensive UI testing
- Wallet operations
- DEX trading
- Dashboard
- Bots
- Authentication
- And 15+ more

### Puppeteer (5 test files)
- Authentication flow
- Bot management
- DEX trading
- Wallet operations
- Patches/utilities

## 🎯 Current Status

- ✅ **Servers**: Running (ports 8000 and 5173)
- ✅ **Test Files**: Ready (26 total files)
- ✅ **Test Infrastructure**: Complete
- ❌ **Package Installation**: Blocked

## 📝 Notes

The issue appears to be environment-specific. Possible causes:
1. OneDrive sync interfering with file writes
2. npm cache corruption
3. Windows file permissions
4. Node.js module resolution with ESM (`"type": "module"` in package.json)

Once packages are properly installed, all tests will run successfully.

---

**Action Required**: Fix package installation using one of the options above, then run the tests.

