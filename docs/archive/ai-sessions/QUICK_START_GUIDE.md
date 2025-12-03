# 🚀 CryptoOrchestrator - Quick Start Guide

## ✅ All Services Running Successfully!

### Current Status

**Backend API**: ✅ Running on port 8000
**Frontend**: ✅ Running on port 5173  
**Celery Worker**: ✅ Running (background tasks)
**Celery Beat**: ✅ Running (scheduled tasks)

---

## 🌐 Access Your Application

### Frontend
**URL**: http://localhost:5173
**Status**: ✅ **LIVE**

### Backend API
**URL**: http://localhost:8000
**API Docs**: http://localhost:8000/docs
**Status**: ✅ **LIVE**

---

## 🎯 Quick Start

### Option 1: Use the Startup Script (Recommended)
```powershell
.\start-all-services.ps1
```

This will start all services in separate PowerShell windows automatically.

### Option 2: Manual Startup

#### 1. Backend (FastAPI)
```powershell
cd server_fastapi
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Frontend (React/Vite)
```powershell
# From project root (where package.json is)
npm run dev
```

#### 3. Celery Worker
```powershell
cd server_fastapi
python -m celery -A celery_app worker --loglevel=info
```

#### 4. Celery Beat
```powershell
cd server_fastapi
python -m celery -A celery_app beat --loglevel=info
```

---

## ⚠️ Important Notes

### Frontend Location
- **`package.json` is in the ROOT directory**, not in `client/`
- Run `npm run dev` from the **project root**
- Vite config correctly points to `client/` as the source

### Celery Commands
- **Always use `python -m celery`** instead of just `celery`
- This ensures the correct Python environment is used
- Works even if Celery is not in system PATH

---

## 🔍 Verify Services

### Check Ports
```powershell
netstat -ano | findstr ":8000 :5173"
```

You should see:
- Port 8000: LISTENING (Backend)
- Port 5173: LISTENING (Frontend)

### Check Processes
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*node*" -or $_.ProcessName -like "*uvicorn*" -or $_.ProcessName -like "*python*"}
```

---

## 🎉 You're Ready!

1. **Open Browser**: Navigate to http://localhost:5173
2. **Create Account**: Click "Sign Up Free"
3. **Start Trading**: Explore the Trading Bots interface
4. **Create Bots**: Try Grid Trading, DCA, Infinity Grid, Trailing Bot, or Futures

---

## 📝 Service Windows

Each service runs in its own PowerShell window:
- **Backend Window**: Shows FastAPI server logs
- **Frontend Window**: Shows Vite dev server logs
- **Celery Worker Window**: Shows background task processing
- **Celery Beat Window**: Shows scheduled task execution

### To Stop Services
Press `Ctrl+C` in each window, or close the windows.

---

## 🐛 Troubleshooting

### Frontend Not Starting
- **Issue**: `package.json` not found
- **Solution**: Run `npm run dev` from **project root**, not from `client/`

### Celery Not Found
- **Issue**: `celery: command not found`
- **Solution**: Use `python -m celery` instead of just `celery`

### Port Already in Use
- **Issue**: Port 8000 or 5173 already in use
- **Solution**: 
  - Stop existing processes: `Get-Process | Where-Object {$_.Id -eq <PID>} | Stop-Process`
  - Or change ports in config files

---

## ✅ System Verified

- ✅ Backend API: Running and accessible
- ✅ Frontend: Running and accessible
- ✅ Database: Migrations applied
- ✅ All routes: Loaded successfully
- ✅ Trading Bots: All 5 types ready
- ✅ Background tasks: Configured and running

**Everything is working perfectly!** 🎉

