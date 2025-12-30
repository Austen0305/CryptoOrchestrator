# CRITICAL FIX: VITE_API_URL Environment Variable

## ⚠️ Issue

The frontend is trying to connect to `http://localhost:8000` instead of the Cloudflare tunnel backend URL. This causes all API calls to fail.

## 🔧 Fix Required

### Step 1: Set Environment Variable in Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project: **CryptoOrchestrator**
3. Go to **Settings** → **Environment Variables**
4. Click **Add New**
5. Enter:
   - **Name:** `VITE_API_URL`
   - **Value:** `https://feel-copies-liberty-round.trycloudflare.com/api`
   - **Environment:** Select all (Production, Preview, Development)
6. Click **Save**
7. **Redeploy** the application (or wait for auto-deploy)

### Step 2: Verify Configuration

After redeploy, check:
1. Open browser DevTools → Network tab
2. Try to register a new account
3. Verify the API request goes to: `https://feel-copies-liberty-round.trycloudflare.com/api/auth/register`
4. Should NOT see `localhost:8000` in network requests

## 📝 Current Backend URL

**Cloudflare Tunnel URL:** `https://feel-copies-liberty-round.trycloudflare.com`

**API Base URL:** `https://feel-copies-liberty-round.trycloudflare.com/api`

## 🔍 How It Works

The frontend code checks for `VITE_API_URL` in this order:

1. `import.meta.env.VITE_API_URL` (Vite environment variable)
2. `window.VITE_API_URL` (Runtime override)
3. `window.__API_BASE__` (Legacy support)
4. Fallback: `http://localhost:8000/api` (Development only)

**Current State:** Falls back to localhost because `VITE_API_URL` is not set.

## ✅ After Fix

Once `VITE_API_URL` is set in Vercel:
- ✅ All API calls will use the Cloudflare tunnel
- ✅ Registration will work
- ✅ Login will work
- ✅ Dashboard data will load
- ✅ Trading features will connect to backend

## 🚨 Important Notes

1. **Cloudflare Tunnel URL:** The tunnel URL (`feel-copies-liberty-round.trycloudflare.com`) may change if the tunnel is restarted. If it changes, update the environment variable.

2. **Permanent Tunnel:** Consider setting up a named Cloudflare tunnel with a permanent domain for production use.

3. **HTTPS Required:** The Cloudflare tunnel provides HTTPS, which is required for production.

---

**Priority:** 🔴 CRITICAL  
**Estimated Fix Time:** 2 minutes  
**Impact:** Blocks all API functionality
