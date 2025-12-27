# ⚡ **DEPLOY NOW - 10 MINUTE GUIDE**

**Date:** December 26, 2025  
**Goal:** Get your app live for testing in 10 minutes!

---

## 🎯 **THE PLAN**

```yaml
Platform:    Railway (backend) + Vercel (frontend)
Cost:        $0
Duration:    20 days free testing
Setup Time:  10 minutes
Difficulty:  EASY (just click buttons!)
```

---

## 🚀 **STEP-BY-STEP (10 MINUTES)**

### **PART 1: Railway Backend (5 min) 🚂**

**1. Create Railway Account (1 min)**
```
→ Go to: https://railway.app
→ Click "Login with GitHub"
→ Authorize Railway
✅ Done!
```

**2. Create New Project (1 min)**
```
→ Click "New Project"
→ Click "Deploy from GitHub repo"
→ Select "Crypto-Orchestrator"
✅ Railway starts analyzing...
```

**3. Add Database Services (2 min)**
```
→ In project dashboard, click "New"
→ Click "Database" → "Add PostgreSQL"
→ Click "New" again
→ Click "Database" → "Add Redis"
✅ Both databases created!
```

**4. Configure Backend (1 min)**
```
→ Click on your "Crypto-Orchestrator" service
→ Go to "Variables" tab
→ Railway auto-added DATABASE_URL and REDIS_URL ✅
→ Add these variables:
   - JWT_SECRET: (generate random: openssl rand -hex 32)
   - EXCHANGE_KEY_ENCRYPTION_KEY: (generate: openssl rand -base64 32)
→ Click "Deploy"
✅ Backend deploying!
```

**Copy Backend URL:**
```
→ Click "Settings" tab
→ Copy "Public Domain" (e.g., https://crypto-orchestrator.up.railway.app)
→ Save this URL for next step!
```

---

### **PART 2: Vercel Frontend (5 min) ▲**

**1. Create Vercel Account (1 min)**
```
→ Go to: https://vercel.com
→ Click "Sign Up" → "Continue with GitHub"
→ Authorize Vercel
✅ Done!
```

**2. Import Project (1 min)**
```
→ Click "Add New..." → "Project"
→ Find "Crypto-Orchestrator"
→ Click "Import"
✅ Vercel analyzing...
```

**3. Configure Build Settings (2 min)**
```
→ Framework Preset: Vite
→ Root Directory: client
→ Build Command: (auto-filled)
→ Output Directory: dist
✅ Looks good!
```

**4. Add Environment Variables (1 min)**
```
→ Scroll to "Environment Variables"
→ Add:
   - Key: VITE_API_URL
   - Value: (your Railway URL from Part 1)
   
   - Key: VITE_WS_URL
   - Value: (Railway URL but change https:// to wss://)

Example:
  VITE_API_URL=https://crypto-orchestrator.up.railway.app
  VITE_WS_URL=wss://crypto-orchestrator.up.railway.app

→ Click "Deploy"
✅ Frontend deploying!
```

---

### **PART 3: Wait for Deployment (2-3 min) ⏳**

**Railway (watch build logs):**
```
→ Go back to Railway dashboard
→ Click on "Crypto-Orchestrator" service
→ Go to "Deployments" tab
→ Watch logs...
→ Wait for: "✓ Build successful"
✅ Backend live!
```

**Vercel (watch build):**
```
→ Vercel shows build progress
→ Wait for: "Deployment Ready"
→ Click "Visit" to see your app!
✅ Frontend live!
```

---

## 🎉 **YOU'RE LIVE!**

**Your app is now deployed:**
- **Frontend:** https://your-app.vercel.app
- **Backend:** https://your-app.up.railway.app

**Test it:**
```
1. Visit your Vercel URL
2. Try creating an account
3. Log in
4. Create a test bot
5. Check if everything works!
```

---

## ⚠️ **ONE-TIME FIX (5 minutes)**

**Issue:** TimescaleDB migrations will fail on Railway

**Quick Fix:**

```bash
# In your local repo:
cd Crypto-Orchestrator

# Create deployment branch:
git checkout -b railway-deploy

# Skip TimescaleDB files:
# Option 1: Delete them (quick)
rm alembic/versions/20251208_add_timescaledb_hypertables.py
rm alembic/versions/20251212_enhance_timescaledb_partitioning.py

# Option 2: Comment them out (better)
# Just add this at the top of each file:
"""
SKIPPED FOR RAILWAY - No TimescaleDB support
Using regular PostgreSQL instead
"""

# Commit and push:
git add .
git commit -m "Skip TimescaleDB for Railway"
git push origin railway-deploy

# Railway will auto-deploy the fix ✅
```

---

## 📊 **WHAT YOU HAVE NOW**

```yaml
✅ Live app (frontend + backend)
✅ PostgreSQL database (1GB)
✅ Redis cache (256MB)
✅ Celery workers (background jobs)
✅ Real-time WebSocket
✅ 20 days free testing ($5 credit)
✅ Easy to manage (no SSH, no VMs)
```

---

## 🔍 **MONITOR YOUR USAGE**

**Railway Dashboard:**
```
→ Go to Project Settings
→ Click "Usage"
→ See how much credit you've used
→ You have $5 = ~20 days
```

**Tips to extend usage:**
- Delete unused deployments
- Use sleep/wake for non-critical services
- Pause Redis if not using cache heavily

---

## 🚨 **TROUBLESHOOTING**

**Backend not deploying?**
```
→ Check Railway logs
→ Look for error messages
→ Common issue: Missing environment variables
→ Fix: Add all required env vars
```

**Frontend showing "API Error"?**
```
→ Check VITE_API_URL is correct
→ Make sure Railway backend is running
→ Check Railway logs for backend errors
```

**Database connection failed?**
```
→ Railway should auto-configure DATABASE_URL
→ Check "Variables" tab in Railway
→ DATABASE_URL should look like:
  postgresql://postgres:...@...railway.app:5432/railway
```

**Migrations failing?**
```
→ Did you skip TimescaleDB migrations?
→ Check the one-time fix above
→ Re-deploy after fixing
```

---

## 📈 **NEXT STEPS**

**Today:**
- [x] Deploy to Railway + Vercel (10 min) ✅
- [ ] Test core features (30 min)
- [ ] Skip TimescaleDB migrations (5 min)

**This Week:**
- [ ] Test all features thoroughly
- [ ] Check background workers
- [ ] Try DEX swaps (testnet)
- [ ] Test ML predictions
- [ ] Monitor performance

**Week 2-3:**
- [ ] Stress test with multiple bots
- [ ] Check database performance
- [ ] Test with real-time market data
- [ ] Fix any bugs found

**Day 20:**
- [ ] Decide: Migrate to Oracle Cloud (free forever)
- [ ] Or: Upgrade Railway ($5/month)

---

## 💡 **PRO TIPS**

**1. Keep Frontend on Vercel Forever**
```
Vercel is free forever for frontend
After testing, only migrate backend to Oracle
Frontend stays on Vercel = no changes needed!
```

**2. Use Railway CLI for Faster Deploys**
```bash
# Install Railway CLI:
npm install -g @railway/cli

# Login:
railway login

# Link to project:
railway link

# Deploy instantly:
railway up

# View logs:
railway logs
```

**3. Monitor Costs**
```
Check Railway usage daily
You have $5 = 20 days
Plan migration to Oracle before Day 20
```

---

## 🏆 **SUCCESS CRITERIA**

**You've succeeded if:**
- ✅ App loads at Vercel URL
- ✅ Can register and login
- ✅ Can create a bot
- ✅ Backend API responds
- ✅ WebSocket connects
- ✅ Background jobs run
- ✅ Database saves data

**If all above work: 🎉 CONGRATULATIONS! You're live!**

---

## 📞 **NEED HELP?**

**Railway Issues:**
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway
- Status: https://status.railway.app

**Vercel Issues:**
- Docs: https://vercel.com/docs
- Discord: https://vercel.com/discord
- Status: https://vercel-status.com

**Project Issues:**
- Check: `docs/troubleshooting/common_issues.md`
- Check: Railway logs (in dashboard)
- Check: Browser console (F12)

---

## 🎯 **SUMMARY**

```yaml
✅ Deploy to Railway (backend): 5 min
✅ Deploy to Vercel (frontend): 5 min
✅ Fix TimescaleDB: 5 min
✅ Total: 15 minutes
✅ Cost: $0 for 20 days
✅ Result: Live app ready for testing!
```

**START NOW:** [Railway](https://railway.app) + [Vercel](https://vercel.com)

**Your app will be live in 10 minutes! 🚀**

---

**Last Updated:** December 26, 2025  
**Status:** Ready to Deploy ✅  
**Time Required:** 10 minutes
