@echo off
REM Quick Start Batch File - Run All Tests
REM Run this from the project root directory

echo.
echo 🚀 CryptoOrchestrator - Quick Test Start
echo.

REM Check if package.json exists
if not exist "package.json" (
    echo ✗ Not in project root. Please run from project root directory.
    echo   Current directory: %CD%
    exit /b 1
)

echo ✓ Found package.json - in project root
echo.
echo Running Playwright E2E tests...
echo.

REM Run Playwright tests
call npm run test:e2e

echo.
echo ✅ Test execution complete!
echo.
echo For more options, see: tests\QUICK_START.md
pause
