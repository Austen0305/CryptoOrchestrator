# ⚡ Quick Start - Deployment Fix

**Time Required:** 20 minutes  
**Difficulty:** Easy

---

## 🎯 What You Need to Do

1. Set up HTTPS for backend (15 min)
2. Configure Vercel environment variable (5 min)
3. Verify everything works (5 min)

---

## Step 1: Set Up HTTPS Backend

### Option A: Production (Nginx + SSL) - RECOMMENDED

**On your Google Cloud VM (SSH in):**

```bash
# SSH into VM
ssh user@34.16.15.56

# Run setup script
cd /path/to/CryptoOrchestrator
sudo bash scripts/deployment/setup-https-backend.sh

# Follow prompts (enter domain or press Enter for IP)
```

**Result:** Backend accessible at `https://yourdomain.com` or `http://34.16.15.56`

---

### Option B: Quick Test (Cloudflare Tunnel) - 5 MINUTES

**On your Google Cloud VM (SSH in):**

```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/

# Start tunnel (use screen for background)
screen -S cloudflare
cloudflared tunnel --url http://localhost:8000
# Press Ctrl+A then D to detach
```

**Result:** Copy the HTTPS URL shown (e.g., `https://xxxxx.trycloudflare.com`)

---

## Step 2: Configure Vercel

### Method 1: PowerShell Script (Windows)

```powershell
# Run the helper script
.\scripts\deployment\setup-vercel-env.ps1

# Follow the prompts
```

### Method 2: Vercel Dashboard

1. Go to: https://vercel.com/dashboard
2. Select your project → **Settings** → **Environment Variables**
3. Add:
   ```
   VITE_API_URL = https://yourdomain.com/api
   ```
   *(Use your backend URL from Step 1)*
4. Select: **Production**, **Preview**, **Development**
5. Click **Save**
6. **Redeploy** your project

---

## Step 3: Verify

### Quick Test Script (on VM):

```bash
# Run verification script
bash scripts/deployment/verify-deployment.sh

# Enter your backend URL when prompted
```

### Manual Verification:

1. **Test backend:**
   ```bash
   curl https://yourdomain.com/health
   # Should return: {"status": "healthy"}
   ```

2. **Test frontend:**
   - Visit: https://cryptoorchestrator.vercel.app
   - Open browser console (F12)
   - Should see **no errors**
   - Try registering/logging in

---

## ✅ Success Checklist

- [ ] Backend accessible via HTTPS
- [ ] Backend `/health` returns `{"status": "healthy"}`
- [ ] Vercel `VITE_API_URL` environment variable set
- [ ] Frontend redeployed
- [ ] No mixed content errors in browser console
- [ ] User registration/login works

---

## 🆘 Quick Troubleshooting

**Mixed Content Error?**
- Ensure backend URL uses `https://` (not `http://`)
- Verify Vercel env var is set correctly
- Clear browser cache (Ctrl+Shift+R)

**Backend Not Accessible?**
- Check nginx: `sudo systemctl status nginx`
- Check backend: `curl http://localhost:8000/health`
- Check logs: `sudo tail -f /var/log/nginx/error.log`

**CORS Errors?**
- Verify backend CORS allows Vercel origin
- Check `VITE_API_URL` includes `/api` suffix

---

## 📚 Full Documentation

- **Detailed Guide:** `DEPLOYMENT_ACTION_PLAN.md`
- **Quick Fix Summary:** `QUICK_FIX_SUMMARY.md`
- **Setup Script:** `scripts/deployment/setup-https-backend.sh`
- **Verification Script:** `scripts/deployment/verify-deployment.sh`

---

**Last Updated:** January 2, 2026  
**Estimated Time:** 20 minutes  
**Status:** Ready to Execute ✅

---

## 📅 Current as of January 2, 2026

All instructions and scripts have been verified and updated with:
- ✅ Latest Vercel environment variable best practices (2026)
- ✅ Certbot installation via snap (recommended method)
- ✅ Latest Cloudflare Tunnel setup (cloudflared 2025.10.0+)
- ✅ Current Let's Encrypt SSL setup procedures
