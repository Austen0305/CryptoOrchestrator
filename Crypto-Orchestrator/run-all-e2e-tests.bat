@echo off
echo ========================================
echo Installing and Running All E2E Tests
echo ========================================
echo.

cd /d "%~dp0"

echo Step 1: Installing Puppeteer...
call npm install puppeteer --save-dev --legacy-peer-deps --ignore-scripts
if exist "node_modules\puppeteer" (
    echo [OK] Puppeteer installed
) else (
    echo [FAIL] Puppeteer installation failed
)

echo.
echo Step 2: Installing Playwright...
call npm install @playwright/test@1.57.0 playwright@1.57.0 --save-dev --legacy-peer-deps --ignore-scripts --force
if exist "node_modules\@playwright\test" (
    echo [OK] Playwright installed
    echo Installing Chromium browser...
    call npx playwright install chromium
    echo [OK] Chromium installed
) else (
    echo [FAIL] Playwright installation failed
)

echo.
echo Step 3: Checking servers...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Backend server is running
) else (
    echo [WARN] Backend server is not running
    echo Please start it with: npm run dev:fastapi
)

curl -s http://localhost:5173 >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Frontend server is running
) else (
    echo [WARN] Frontend server is not running
    echo Please start it with: npm run dev
)

echo.
echo ========================================
echo Running Puppeteer Tests
echo ========================================
echo.
set BASE_URL=http://localhost:5173
set API_URL=http://localhost:8000
if exist "node_modules\puppeteer" (
    call node scripts/testing/run-puppeteer-tests.js
) else (
    echo [SKIP] Puppeteer not installed
)

echo.
echo ========================================
echo Running Playwright Tests
echo ========================================
echo.
if exist "node_modules\@playwright\test" (
    call npx playwright test --reporter=list --timeout=60000 --max-failures=20
) else (
    echo [SKIP] Playwright not installed
)

echo.
echo ========================================
echo All Tests Complete!
echo ========================================
echo.
echo Check test results:
echo   - Playwright HTML Report: playwright-report\index.html
echo   - Screenshots: test-results\
echo   - Puppeteer Screenshots: tests\puppeteer\screenshots\
echo.
pause

