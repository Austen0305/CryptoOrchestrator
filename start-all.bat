@echo off
echo Starting CryptoOrchestrator servers...
echo.

REM Check if ports are in use
netstat -ano | findstr ":5173" >nul
if %errorlevel% == 0 (
    echo ERROR: Port 5173 is already in use!
    echo Please close the application using port 5173
    pause
    exit /b 1
)

netstat -ano | findstr ":8000" >nul
if %errorlevel% == 0 (
    echo ERROR: Port 8000 is already in use!
    echo Please close the application using port 8000
    pause
    exit /b 1
)

echo Starting FastAPI backend on port 8000...
start "FastAPI Backend" cmd /k "cd /d %~dp0 && npm run dev:fastapi"

timeout /t 3 /nobreak >nul

echo Starting Vite frontend on port 5173...
start "Vite Frontend" cmd /k "cd /d %~dp0 && npm run dev"

echo.
echo Servers are starting in separate windows.
echo.
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
echo.
echo Check the command prompt windows for any errors.
echo Press any key to exit this window (servers will keep running)...
pause >nul

