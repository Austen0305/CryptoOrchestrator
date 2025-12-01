# Server Restart Instructions

## Problem
The registration endpoint was hanging due to a blocking database check, causing 10-second timeouts.

## Solution Applied
✅ **Fixed**: Removed blocking database check from registration endpoint
- Endpoint now responds immediately
- Database persistence happens in background
- No more hanging/timeouts

## Steps to Fix

### 1. Stop Current Server

**Option A: Manual Stop (Recommended)**
1. Find the terminal window running the FastAPI server
2. Press `Ctrl+C` to stop it

**Option B: Force Stop Process**
```powershell
# Stop process 10484 (the unresponsive server)
Stop-Process -Id 10484 -Force
```

**Option C: Kill All Python Processes on Port 8000**
```powershell
Get-NetTCPConnection -LocalPort 8000 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

### 2. Verify Port is Free
```powershell
Get-NetTCPConnection -LocalPort 8000
```
Should return nothing (port is free).

### 3. Restart Server

**Start FastAPI server:**
```powershell
npm run dev:fastapi
```

**Or start both servers:**
```powershell
.\start-servers.ps1
```

### 4. Test Registration

After the server starts, try registering again. It should:
- ✅ Respond immediately (no timeout)
- ✅ Complete registration successfully
- ✅ Close the modal automatically

## Expected Results

**Before fix:**
- ❌ Request times out after 10 seconds
- ❌ "Connection timeout" error shown
- ❌ Form stuck on "Creating account..."

**After fix:**
- ✅ Registration completes in < 1 second
- ✅ Success message shown
- ✅ Modal closes automatically
- ✅ User can log in immediately

## Troubleshooting

If registration still fails:
1. Check server logs for errors
2. Verify server is running: `http://localhost:8000/docs`
3. Check browser console for API errors
4. Ensure frontend is using correct API URL: `http://localhost:8000/api`

