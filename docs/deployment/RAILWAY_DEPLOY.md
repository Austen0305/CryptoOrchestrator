# 🚂 **RAILWAY DEPLOYMENT GUIDE**

**Date:** December 26, 2025  
**Status:** Ready to Deploy ✅

---

## ✅ **PROJECT CONFIGURED FOR RAILWAY**

Your CryptoOrchestrator project is now **fully configured** for Railway + Vercel deployment!

### **Changes Made:**

1. ✅ **TimescaleDB Migrations** - Auto-skip if not available (Railway compatible)
2. ✅ **Railway Config Files** - `railway.json`, `railway.toml`, `nixpacks.toml`, `Procfile`
3. ✅ **Vercel Config** - `client/vercel.json`, `.vercelignore`
4. ✅ **Database Compatibility** - Works with standard PostgreSQL (no TimescaleDB required)

---

## 🚀 **DEPLOYMENT STEPS**

### **STEP 1: Deploy Backend to Railway (5 minutes)**

**1. Create Railway Account**
```
→ Go to: https://railway.app
→ Click "Login with GitHub"
→ Authorize Railway
✅ Done!
```

**2. Create New Project**
```
→ Click "New Project"
→ Select "Deploy from GitHub repo"
→ Choose "Crypto-Orchestrator"
✅ Railway starts building...
```

**3. Add Database Services**
```
→ In your project, click "+ New"
→ Select "Database" → "PostgreSQL"
→ Click "+ New" again
→ Select "Database" → "Redis"
✅ Databases created!
```

**4. Configure Environment Variables**

Railway auto-configures `DATABASE_URL` and `REDIS_URL`. You need to add:

```bash
# In Railway dashboard → Variables:
JWT_SECRET=your-secret-key-here
EXCHANGE_KEY_ENCRYPTION_KEY=your-encryption-key-here

# Generate secure keys:
# JWT_SECRET: openssl rand -hex 32
# EXCHANGE_KEY_ENCRYPTION_KEY: openssl rand -base64 32
```

**Optional Variables (for full features):**
```bash
# Blockchain RPC (for testnet)
ETHEREUM_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/your-key
BASE_RPC_URL=https://base-sepolia.g.alchemy.com/v2/your-key

# DEX Aggregators (optional)
ZEROX_API_KEY=your-0x-key
OKX_DEX_API_KEY=your-okx-key
```

**5. Deploy!**
```
→ Railway automatically detects Python/FastAPI
→ Uses nixpacks.toml configuration
→ Runs database migrations (alembic upgrade head)
→ Starts uvicorn server
✅ Backend deployed!
```

**6. Get Your Backend URL**
```
→ Click on your service
→ Go to "Settings"
→ Click "Generate Domain"
→ Copy URL (e.g., https://crypto-orchestrator.up.railway.app)
✅ Save this for Vercel!
```

---

### **STEP 2: Deploy Frontend to Vercel (5 minutes)**

**1. Create Vercel Account**
```
→ Go to: https://vercel.com
→ Click "Sign Up"
→ Choose "Continue with GitHub"
→ Authorize Vercel
✅ Done!
```

**2. Import Project**
```
→ Click "Add New..." → "Project"
→ Find "Crypto-Orchestrator"
→ Click "Import"
✅ Vercel analyzing...
```

**3. Configure Build Settings**
```
Framework Preset: Vite
Root Directory: client
Build Command: npm run build
Output Directory: dist
Install Command: npm install

✅ Leave as auto-detected!
```

**4. Add Environment Variables**

```bash
# Required:
VITE_API_URL=https://your-railway-backend.up.railway.app
VITE_WS_URL=wss://your-railway-backend.up.railway.app

# Optional (if using blockchain features):
VITE_ENABLE_TESTNET=true
```

**5. Deploy!**
```
→ Click "Deploy"
→ Vercel builds your frontend
→ Wait 2-3 minutes
✅ Frontend deployed!
```

**6. Visit Your App**
```
→ Click "Visit" button
→ Your app is live!
✅ Start testing!
```

---

## ✅ **VERIFICATION CHECKLIST**

After deployment, verify everything works:

**Backend (Railway):**
- [ ] Service is running (check Railway logs)
- [ ] Database migrations completed successfully
- [ ] Health endpoint works: `https://your-backend.railway.app/health`
- [ ] API docs accessible: `https://your-backend.railway.app/docs`
- [ ] No TimescaleDB errors (auto-skipped)

**Frontend (Vercel):**
- [ ] App loads successfully
- [ ] Can see login/register page
- [ ] API connection works (check browser console)
- [ ] No CORS errors

**Database:**
- [ ] PostgreSQL connected (check Railway logs)
- [ ] Tables created (check Railway PostgreSQL dashboard)
- [ ] Can query database

**Redis:**
- [ ] Redis connected (check Railway logs)
- [ ] Caching works (check app performance)

---

## 🔧 **CONFIGURATION FILES EXPLAINED**

### **railway.json / railway.toml**
- Tells Railway how to build and deploy your backend
- Configures health checks and restart policies
- Sets Python 3.12 environment

### **nixpacks.toml**
- Railway's build system configuration
- Installs Python 3.12, PostgreSQL client, OpenSSL
- Runs database migrations before starting

### **Procfile**
- Defines processes for Railway
- `web`: Main FastAPI server
- `worker`: Celery workers (for background jobs)
- `beat`: Celery beat (for scheduled tasks)

### **client/vercel.json**
- Vercel build configuration
- Enables SPA routing (all routes → index.html)
- Configures caching for static assets
- Sets environment variables

---

## 📊 **RESOURCE USAGE**

### **Railway Free Tier ($5 credit):**

```yaml
Usage Estimate:
- Backend (FastAPI):     ~$1.50/week
- PostgreSQL:            ~$1.00/week
- Redis:                 ~$0.50/week
- Total:                 ~$3/week = 3-4 weeks free

Optimization Tips:
- Use 1 worker (not 3) to save memory
- Pause services when not testing
- Monitor usage in Railway dashboard
```

### **Vercel Free Tier:**

```yaml
Always Free:
- 100GB bandwidth/month
- Unlimited deployments
- Automatic HTTPS
- Global CDN
- Preview deployments

✅ Frontend is FREE FOREVER!
```

---

## 🐛 **TROUBLESHOOTING**

### **Backend Won't Deploy**

**Error: "ModuleNotFoundError"**
```bash
# Solution: Check requirements.txt includes all dependencies
# Railway installs from requirements.txt automatically
```

**Error: "Port already in use"**
```bash
# Solution: Railway sets $PORT automatically
# Our config uses: --port $PORT (no need to change)
```

**Error: "Database connection failed"**
```bash
# Solution: Check DATABASE_URL is set
# Railway auto-injects this when you add PostgreSQL
```

### **Frontend Won't Build**

**Error: "VITE_API_URL not defined"**
```bash
# Solution: Add environment variable in Vercel:
# VITE_API_URL=https://your-railway-backend.up.railway.app
```

**Error: "Build failed"**
```bash
# Solution: Check build command is correct:
# Build Command: npm run build
# Output Directory: dist
```

### **TimescaleDB Warnings**

**Warning: "TimescaleDB extension not available"**
```bash
# This is NORMAL and EXPECTED on Railway!
# Our migrations automatically skip TimescaleDB features
# Your app works perfectly with regular PostgreSQL ✅
```

---

## 🔄 **DEPLOYING UPDATES**

### **Backend Updates (Railway):**

```bash
# 1. Make changes locally
# 2. Commit to GitHub
git add .
git commit -m "Update backend"
git push origin main

# 3. Railway auto-deploys! ✅
# Watch progress in Railway dashboard
```

### **Frontend Updates (Vercel):**

```bash
# 1. Make changes locally
# 2. Commit to GitHub
git add .
git commit -m "Update frontend"
git push origin main

# 3. Vercel auto-deploys! ✅
# Watch progress in Vercel dashboard
```

### **Database Migrations:**

```bash
# 1. Create new migration locally:
cd Crypto-Orchestrator
alembic revision --autogenerate -m "your migration name"

# 2. Test locally:
alembic upgrade head

# 3. Commit and push:
git add .
git commit -m "Add migration: your migration name"
git push origin main

# 4. Railway automatically runs migrations on deploy ✅
```

---

## 📈 **MONITORING**

### **Railway Dashboard:**
```
→ View logs (real-time)
→ Monitor CPU/memory usage
→ Check $5 credit remaining
→ Restart services if needed
→ View database metrics
```

### **Vercel Dashboard:**
```
→ View deployments
→ Check build logs
→ Monitor bandwidth usage
→ View analytics
→ Configure custom domain
```

---

## 🎯 **NEXT STEPS**

**After Successful Deployment:**

1. ✅ **Test Core Features** (1-2 hours)
   - Create account
   - Login/logout
   - Create trading bot
   - Test paper trading
   - Check background jobs

2. ✅ **Configure External Services** (optional)
   - Add Alchemy API keys for blockchain
   - Add 0x API key for DEX trading
   - Market Data Service works automatically (CoinCap/CoinLore)

3. ✅ **Set Up Monitoring** (30 minutes)
   - Enable error tracking (Sentry optional)
   - Set up alerts in Railway
   - Monitor usage daily

4. ✅ **Plan Production Migration** (Day 20)
   - Decide: Oracle Cloud (free forever)
   - Or: Upgrade Railway ($5/month)
   - Export data if migrating

---

## 💡 **TIPS FOR SUCCESS**

**1. Monitor Your Credit Daily**
```
Railway Dashboard → Usage
Check remaining credit
Plan migration before it runs out
```

**2. Optimize for Testing**
```
- Use 1 Celery worker (not 3)
- Pause services when not testing
- Use testnet for blockchain (free)
- Test with small data sets first
```

**3. Keep Frontend on Vercel Forever**
```
Vercel is free forever for frontend
After testing, only backend needs migration
Frontend stays on Vercel = zero changes!
```

**4. Use Railway CLI for Faster Deploys**
```bash
npm install -g @railway/cli
railway login
railway link
railway logs  # View real-time logs
```

---

## 🏆 **SUCCESS!**

**Your CryptoOrchestrator is now deployed!**

```yaml
✅ Backend:   https://your-app.up.railway.app
✅ Frontend:  https://your-app.vercel.app
✅ Database:  PostgreSQL (Railway)
✅ Cache:     Redis (Railway)
✅ Workers:   Celery (Railway)
✅ Cost:      $0 for 20 days
```

**Start testing and enjoy! 🎉**

---

**Need Help?**
- Railway Docs: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs
- Railway Discord: https://discord.gg/railway
- Check logs first (Railway Dashboard → Deployments → Logs)

---

**Last Updated:** December 26, 2025  
**Status:** Production Ready ✅  
**Deployment Time:** 10 minutes total
