# Backend CORS Configuration Fix Guide

## ⚠️ Issue

Frontend requests from `https://cryptoorchestrator.vercel.app` are being blocked by CORS policy.

**Error:** `Access to fetch at 'https://feel-copies-liberty-round.trycloudflare.com/api/...' from origin 'https://cryptoorchestrator.vercel.app' has been blocked by CORS policy`

---

## 🔧 Fix: Configure CORS on Backend

### Option 1: Environment Variable (Recommended)

On your Google Cloud VM, set the `CORS_ORIGINS` environment variable:

```bash
# SSH into your VM
ssh labarcodez@cryptoorchestrator

# Edit your environment file (or add to systemd service)
sudo nano /etc/systemd/system/cryptoorchestrator.service
# Or edit your .env file if using one
```

Add or update:
```bash
CORS_ORIGINS=https://cryptoorchestrator.vercel.app,https://www.cryptoorchestrator.vercel.app
```

**For systemd service**, add to `[Service]` section:
```ini
[Service]
Environment="CORS_ORIGINS=https://cryptoorchestrator.vercel.app,https://www.cryptoorchestrator.vercel.app"
```

Then restart the service:
```bash
sudo systemctl daemon-reload
sudo systemctl restart cryptoorchestrator
```

### Option 2: Direct Code Edit

If environment variable doesn't work, edit the CORS configuration:

**File:** `server_fastapi/middleware/setup.py`

**Current code (around line 95):**
```python
if not cors_origins:
    cors_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]
```

**Update to:**
```python
if not cors_origins:
    cors_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "https://cryptoorchestrator.vercel.app",
        "https://www.cryptoorchestrator.vercel.app",
    ]
```

Then restart your FastAPI server.

---

## 📋 How CORS Works in This Project

**Location:** `server_fastapi/middleware/setup.py`

**Function:** `get_cors_origins()` (line 33)
- Reads from `CORS_ORIGINS` environment variable
- Splits by comma
- Validates URLs
- Falls back to defaults if not set

**Function:** `setup_cors_middleware()` (line 89)
- Configures FastAPI CORSMiddleware
- Sets allowed origins, methods, headers
- Adds custom middleware for error responses

---

## ✅ Verification

After fixing, test:

1. **Check CORS headers:**
```bash
curl -H "Origin: https://cryptoorchestrator.vercel.app" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://feel-copies-liberty-round.trycloudflare.com/api/auth/register \
     -v
```

Should return:
```
Access-Control-Allow-Origin: https://cryptoorchestrator.vercel.app
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

2. **Test from browser:**
- Open browser console on https://cryptoorchestrator.vercel.app
- Try to register/login
- Should NOT see CORS errors

---

## 🔍 Current CORS Configuration

**File:** `server_fastapi/middleware/setup.py`

**Default Origins (if CORS_ORIGINS not set):**
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (Alternative dev port)
- `http://127.0.0.1:5173` (Localhost IP)

**Required Addition:**
- `https://cryptoorchestrator.vercel.app` ✅
- `https://www.cryptoorchestrator.vercel.app` (if using www subdomain)

---

## 🚨 Important Notes

1. **Cloudflare Tunnel:** The tunnel URL may change. If it does, you may need to update CORS to allow the new tunnel domain as well.

2. **Multiple Origins:** You can specify multiple origins separated by commas:
   ```
   CORS_ORIGINS=https://cryptoorchestrator.vercel.app,https://www.cryptoorchestrator.vercel.app,http://localhost:5173
   ```

3. **Wildcard:** For development, you can use `*` but **NEVER in production** for security reasons.

4. **Restart Required:** After changing CORS settings, restart your FastAPI server.

---

## 📝 Quick Fix Commands

```bash
# SSH into VM
ssh labarcodez@cryptoorchestrator

# Add to environment (if using systemd)
sudo systemctl edit cryptoorchestrator
# Add:
# [Service]
# Environment="CORS_ORIGINS=https://cryptoorchestrator.vercel.app"

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart cryptoorchestrator

# Verify
sudo systemctl status cryptoorchestrator
```

---

**Priority:** 🔴 CRITICAL  
**Estimated Time:** 5 minutes  
**Impact:** Blocks all API calls from frontend
