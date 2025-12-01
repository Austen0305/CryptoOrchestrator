@echo off
title CryptoOrchestrator - Quick Start
color 0A
echo.
echo ========================================
echo   CryptoOrchestrator - Starting Servers
echo ========================================
echo.

cd /d "%~dp0"

echo [1/4] Checking Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found! Please install Node.js 18+
    pause
    exit /b 1
)
node --version

echo [2/4] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found! Please install Python 3.8+
    pause
    exit /b 1
)
python --version

echo [3/4] Checking ports...
netstat -ano | findstr ":5173" >nul
if %errorlevel% == 0 (
    echo WARNING: Port 5173 is in use. Closing existing process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
    timeout /t 2 /nobreak >nul
)

netstat -ano | findstr ":8000" >nul
if %errorlevel% == 0 (
    echo WARNING: Port 8000 is in use. Closing existing process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
    timeout /t 2 /nobreak >nul
)

echo [4/4] Starting servers...
echo.
echo Starting FastAPI backend (port 8000)...
start "FastAPI Backend - Port 8000" cmd /k "cd /d %~dp0 && echo Starting FastAPI... && npm run dev:fastapi"

timeout /t 5 /nobreak >nul

echo Starting Vite frontend (port 5173)...
start "Vite Frontend - Port 5173" cmd /k "cd /d %~dp0 && echo Starting Vite... && npm run dev"

echo.
echo ========================================
echo   Servers are starting!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Check the two command prompt windows that opened.
echo They will show when servers are ready.
echo.
echo Press any key to open the frontend in your browser...
pause >nul

start http://localhost:5173

echo.
echo Frontend opened in browser!
echo Servers will continue running in the background windows.
echo.
echo To stop servers, close the command prompt windows.
echo.
pause

