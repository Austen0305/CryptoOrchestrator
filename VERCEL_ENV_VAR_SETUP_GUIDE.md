# Vercel Environment Variable Setup Guide

## ⚠️ Critical: Configure VITE_API_URL

The frontend needs to know where your backend API is located.

---

## 🚀 Step-by-Step Instructions

### Method 1: Vercel Dashboard (Recommended)

1. **Go to Vercel Dashboard**
   - Visit: https://vercel.com/dashboard
   - Sign in to your account

2. **Select Your Project**
   - Click on **CryptoOrchestrator** project

3. **Navigate to Settings**
   - Click **Settings** in the top navigation
   - Click **Environment Variables** in the left sidebar

4. **Add New Variable**
   - Click **Add New** button
   - Enter:
     - **Key:** `VITE_API_URL`
     - **Value:** `https://feel-copies-liberty-round.trycloudflare.com/api`
     - **Environment:** Select all three:
       - ✅ Production
       - ✅ Preview
       - ✅ Development
   - Click **Save**

5. **Redeploy**
   - Go to **Deployments** tab
   - Click **⋯** (three dots) on latest deployment
   - Click **Redeploy**
   - Or wait for auto-deploy (happens automatically on next push)

### Method 2: Vercel CLI

```bash
# Install Vercel CLI (if not installed)
npm i -g vercel

# Login
vercel login

# Add environment variable
vercel env add VITE_API_URL

# When prompted:
# - Value: https://feel-copies-liberty-round.trycloudflare.com/api
# - Environment: Production, Preview, Development (select all)

# Redeploy
vercel --prod
```

---

## ✅ Verification

### After Setting Variable

1. **Check Build Logs**
   - Go to Vercel Dashboard → Your Project → Deployments
   - Click on latest deployment
   - Check build logs for `VITE_API_URL`

2. **Test in Browser**
   - Open https://cryptoorchestrator.vercel.app
   - Open DevTools → Network tab
   - Try to register/login
   - Check network requests - should go to:
     - ✅ `https://feel-copies-liberty-round.trycloudflare.com/api/...`
     - ❌ NOT `http://localhost:8000/...`

3. **Check Console**
   - Open browser console
   - Should NOT see "localhost" in API requests
   - API calls should succeed (after CORS is also fixed)

---

## 🔍 Current Backend URL

**Cloudflare Tunnel URL:** `https://feel-copies-liberty-round.trycloudflare.com`

**API Base URL:** `https://feel-copies-liberty-round.trycloudflare.com/api`

**Note:** This tunnel URL may change if the tunnel is restarted. If it changes:
1. Update `VITE_API_URL` in Vercel
2. Update CORS origins on backend
3. Redeploy frontend

---

## 📋 All Required Environment Variables

### Required
- ✅ `VITE_API_URL` = `https://feel-copies-liberty-round.trycloudflare.com/api`

### Optional (for full functionality)
- `VITE_WS_BASE_URL` = `wss://feel-copies-liberty-round.trycloudflare.com` (auto-derived if not set)
- `VITE_WALLETCONNECT_PROJECT_ID` = Your WalletConnect project ID (if using Web3)
- `VITE_VAPID_PUBLIC_KEY` = Your VAPID public key (if using push notifications)

---

## 🚨 Important Notes

1. **Variable Name:** Must start with `VITE_` for Vite to include it in the build
2. **HTTPS Required:** Must use HTTPS URL (not HTTP) for production
3. **No Trailing Slash:** Don't include trailing slash in URL
4. **Redeploy Required:** Changes only take effect after redeployment

---

## 🔄 After Configuration

Once `VITE_API_URL` is set:

1. ✅ Frontend will connect to correct backend
2. ✅ Registration will work
3. ✅ Login will work
4. ✅ All API calls will use correct URL
5. ⚠️ Still need to fix CORS on backend (see `BACKEND_CORS_FIX_GUIDE.md`)

---

## 📝 Quick Reference

**Variable Name:** `VITE_API_URL`  
**Value:** `https://feel-copies-liberty-round.trycloudflare.com/api`  
**Environments:** Production, Preview, Development  
**Time to Apply:** Immediate after redeploy

---

**Priority:** 🔴 CRITICAL  
**Estimated Time:** 2 minutes  
**Impact:** Enables all API functionality
