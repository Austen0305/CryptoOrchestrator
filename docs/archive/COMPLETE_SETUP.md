# Complete Setup Guide - CryptoOrchestrator

## ✅ Code Fixes Applied

1. **Token Storage Fixed** - All authentication now uses consistent `auth_token` keys
2. **Vite Config Fixed** - Path resolution updated to work with all Node versions
3. **useWalletWebSocket Fixed** - Now correctly accesses tokens

## 🚀 How to Start Everything

### Method 1: Use the Batch File (Easiest)

Double-click `start-all.bat` in the project root. This will:
- Check if ports are available
- Start backend in one window
- Start frontend in another window
- Show you the URLs

### Method 2: Manual Start

**Open TWO separate Command Prompt or PowerShell windows:**

**Window 1 - Backend:**
```bash
cd "C:\Users\William Walker\OneDrive\Desktop\CryptoOrchestrator\Crypto-Orchestrator"
npm run dev:fastapi
```

Wait until you see: `Uvicorn running on http://0.0.0.0:8000`

**Window 2 - Frontend:**
```bash
cd "C:\Users\William Walker\OneDrive\Desktop\CryptoOrchestrator\Crypto-Orchestrator"
npm run dev
```

Wait until you see: `Local: http://localhost:5173`

### Method 3: PowerShell Script

```powershell
cd "C:\Users\William Walker\OneDrive\Desktop\CryptoOrchestrator\Crypto-Orchestrator"
powershell -ExecutionPolicy Bypass -File start-servers.ps1
```

## 🔍 Troubleshooting

### If ports are in use:
```bash
# Find what's using the ports
netstat -ano | findstr ":5173"
netstat -ano | findstr ":8000"

# Kill the process (replace PID with actual process ID)
taskkill /F /PID <PID>
```

### If dependencies are missing:
```bash
npm install --legacy-peer-deps
pip install -r requirements.txt
```

### If you see "command not found":
- Make sure Node.js 18+ is installed: `node -v`
- Make sure Python 3.8+ is installed: `python --version`
- Make sure both are in your PATH

### If Vite won't start:
```bash
# Try running Vite directly
cd client
npx vite --host localhost --port 5173
```

## ✅ Verification

Once both servers are running:

1. **Backend**: Open http://localhost:8000/docs (should show FastAPI docs)
2. **Frontend**: Open http://localhost:5173 (should show landing page)

## 📝 What Was Fixed

- ✅ Token storage keys standardized (`auth_token` instead of `token`)
- ✅ Vite config path resolution fixed (`__dirname` instead of `import.meta.dirname`)
- ✅ useWalletWebSocket token access fixed
- ✅ Server configuration improved with explicit host/port

## 🎯 Next Steps

1. Start the servers using one of the methods above
2. Open http://localhost:5173 in your browser
3. You should see the landing page
4. Try registering/logging in to test authentication

If you encounter any errors, check:
- The terminal windows where servers are running
- Browser console (F12) for JavaScript errors
- Network tab for failed API calls

