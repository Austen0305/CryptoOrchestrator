# Free Hosting Deployment Guide

This guide provides step-by-step instructions for deploying CryptoOrchestrator to various free hosting platforms.

## 🎯 Overview

Your application requires:
- **Backend**: FastAPI (Python) - Port 8000
- **Frontend**: React (Vite) - Static files
- **Database**: PostgreSQL
- **Cache**: Redis
- **Background Jobs**: Celery (optional for free tier)

## 📊 Free Hosting Options Comparison

| Platform | Backend | Database | Redis | Frontend | Free Tier Limits |
|----------|---------|----------|-------|----------|------------------|
| **Render** | ✅ | ✅ | ✅ | ✅ | 750 hrs/month, spins down after 15min inactivity |
| **Railway** | ✅ | ✅ | ✅ | ✅ | $5 credit/month, pay-as-you-go |
| **Fly.io** | ✅ | ✅ | ✅ | ✅ | 3 shared VMs, 3GB storage |
| **Vercel** | ❌ | ❌ | ❌ | ✅ | Unlimited static hosting |
| **Netlify** | ❌ | ❌ | ❌ | ✅ | 100GB bandwidth/month |
| **Supabase** | ❌ | ✅ | ❌ | ❌ | 500MB database, 2GB bandwidth |
| **Neon** | ❌ | ✅ | ❌ | ❌ | 0.5GB storage, unlimited projects |
| **Upstash** | ❌ | ❌ | ✅ | ❌ | 10K commands/day, 256MB storage |

## 🚀 Recommended Setup: Render.com (Easiest)

Render offers the most complete free tier with PostgreSQL, Redis, and web services.

### Prerequisites
1. GitHub account
2. Render.com account (sign up at https://render.com)
3. Your code pushed to GitHub

### Step 1: Deploy PostgreSQL Database

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `crypto-orchestrator-db`
   - **Database**: `cryptoorchestrator`
   - **User**: `crypto_user`
   - **Region**: Choose closest to you
   - **PostgreSQL Version**: 15
   - **Plan**: Free
4. Click **"Create Database"**
5. **Save the Internal Database URL** (you'll need it later)

### Step 2: Deploy Redis

1. Click **"New +"** → **"Redis"**
2. Configure:
   - **Name**: `crypto-orchestrator-redis`
   - **Region**: Same as database
   - **Plan**: Free
3. Click **"Create Redis"**
4. **Save the Internal Redis URL**

### Step 3: Deploy Backend (FastAPI)

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `crypto-orchestrator-backend`
   - **Region**: Same as database
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: Leave empty
   - **Runtime**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     python -m uvicorn server_fastapi.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: Free
4. Add Environment Variables:
   ```
   DATABASE_URL=<Internal Database URL from Step 1>
   REDIS_URL=<Internal Redis URL from Step 2>
   JWT_SECRET=<Generate a random secret>
   JWT_REFRESH_SECRET=<Generate another random secret>
   EXCHANGE_KEY_ENCRYPTION_KEY=<Generate a random 32-char key>
   PORT=8000
   ENVIRONMENT=production
   ```
   **Generate secrets:**
   ```bash
   # On Linux/Mac
   openssl rand -hex 32
   
   # On Windows PowerShell
   -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
   ```
5. Click **"Create Web Service"**

### Step 4: Deploy Frontend (React)

**Option A: Deploy as Static Site on Render**

1. Click **"New +"** → **"Static Site"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `crypto-orchestrator-frontend`
   - **Branch**: `main`
   - **Root Directory**: `client`
   - **Build Command**: 
     ```bash
     npm install --legacy-peer-deps && npm run build
     ```
   - **Publish Directory**: `client/dist`
   - **Plan**: Free
4. Add Environment Variable:
   ```
   VITE_API_URL=https://crypto-orchestrator-backend.onrender.com
   ```
5. Click **"Create Static Site"**

**Option B: Deploy to Vercel (Recommended for Frontend)**

See [Vercel Deployment](#vercel-deployment) section below.

### Step 5: Run Database Migrations

After backend is deployed:

1. Go to your backend service on Render
2. Click **"Shell"** tab
3. Run:
   ```bash
   alembic upgrade head
   ```

### Step 6: Update Frontend API URL

Update your frontend environment to point to your Render backend URL.

---

## 🚂 Alternative: Railway.app

Railway offers $5 free credit monthly with pay-as-you-go pricing.

### Setup

1. Sign up at https://railway.app
2. Create new project
3. Add services:
   - **PostgreSQL** (from template)
   - **Redis** (from template)
   - **GitHub Repo** (connect your repo)

### Backend Configuration

1. Add service from GitHub repo
2. Configure:
   - **Root Directory**: `/`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn server_fastapi.main:app --host 0.0.0.0 --port $PORT`
3. Add environment variables (Railway auto-generates DATABASE_URL and REDIS_URL)
4. Add custom variables:
   ```
   JWT_SECRET=<your-secret>
   JWT_REFRESH_SECRET=<your-secret>
   EXCHANGE_KEY_ENCRYPTION_KEY=<your-key>
   PORT=8000
   ```

### Frontend Configuration

1. Add new service from same repo
2. Configure:
   - **Root Directory**: `client`
   - **Build Command**: `npm install --legacy-peer-deps && npm run build`
   - **Start Command**: `npx serve -s dist -l $PORT`
3. Add environment variable:
   ```
   VITE_API_URL=<your-backend-railway-url>
   ```

---

## ✈️ Alternative: Fly.io

Fly.io offers 3 shared VMs for free.

### Setup

1. Install Fly CLI:
   ```bash
   # Windows (PowerShell)
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   
   # Mac/Linux
   curl -L https://fly.io/install.sh | sh
   ```
2. Sign up: `fly auth signup`
3. Login: `fly auth login`

### Deploy Backend

1. Navigate to project root
2. Initialize Fly app:
   ```bash
   fly launch
   ```
3. Follow prompts (use `fly.toml` from this repo)
4. Deploy:
   ```bash
   fly deploy
   ```

### Database & Redis

Fly.io doesn't provide managed databases on free tier. Use:
- **Supabase** or **Neon** for PostgreSQL (free)
- **Upstash** for Redis (free)

Update `fly.toml` with external database URLs.

---

## ▲ Vercel Deployment (Frontend Only)

Vercel is excellent for React frontends with automatic deployments.

### Setup

1. Sign up at https://vercel.com
2. Import your GitHub repository
3. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `client`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Add Environment Variable:
   ```
   VITE_API_URL=https://your-backend-url.onrender.com
   ```
5. Deploy

### Custom Domain (Optional)

Vercel provides free SSL and custom domains on free tier.

---

## 🗄️ Free Database Options

### Supabase (PostgreSQL)

1. Sign up at https://supabase.com
2. Create new project
3. Get connection string from Settings → Database
4. Use format: `postgresql+asyncpg://postgres:[PASSWORD]@[HOST]:5432/postgres`

**Free Tier:**
- 500MB database
- 2GB bandwidth
- Unlimited API requests

### Neon (PostgreSQL)

1. Sign up at https://neon.tech
2. Create new project
3. Get connection string from dashboard

**Free Tier:**
- 0.5GB storage
- Unlimited projects
- Serverless PostgreSQL

---

## 🔴 Free Redis Options

### Upstash

1. Sign up at https://upstash.com
2. Create Redis database
3. Get REST API URL and token

**Free Tier:**
- 10,000 commands/day
- 256MB storage
- Global replication

**Note:** Upstash uses REST API, not direct Redis connection. You may need to update your Redis client code.

---

## 🔧 Environment Variables Template

Create a `.env.production` file with these variables:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://:password@host:6379/0

# JWT Secrets (generate random strings)
JWT_SECRET=your-jwt-secret-here
JWT_REFRESH_SECRET=your-refresh-secret-here

# Encryption
EXCHANGE_KEY_ENCRYPTION_KEY=your-32-char-encryption-key

# Application
PORT=8000
ENVIRONMENT=production
NODE_ENV=production

# Frontend API URL (for frontend builds)
VITE_API_URL=https://your-backend-url.com

# Optional: Stripe (if using payments)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Optional: Email (if using SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com

# Optional: Sentry (error tracking)
SENTRY_DSN=https://...
```

---

## 🚨 Important Notes

### Render.com Limitations

- **Spins down after 15 minutes** of inactivity
- **First request after spin-down takes ~30 seconds** (cold start)
- **750 hours/month** free tier (enough for 24/7 if you keep it active)
- **Solution**: Use a cron job or uptime monitor to ping your app every 10 minutes

### Railway.app Limitations

- **$5 free credit/month** - pay for what you use
- **Spins down after inactivity** (similar to Render)
- **Better performance** than Render free tier

### Fly.io Limitations

- **3 shared VMs** on free tier
- **3GB storage** total
- **No managed databases** - must use external services

### Database Limitations

- **Supabase**: 500MB limit, may need to upgrade for production
- **Neon**: 0.5GB limit, but can create multiple projects
- **Render PostgreSQL**: 90 days retention, 1GB limit

### Redis Limitations

- **Upstash**: REST API only (not standard Redis protocol)
- **Render Redis**: 25MB limit, 90 days retention

---

## 🔄 Keeping Services Active (Render)

To prevent Render services from spinning down:

1. **Use Uptime Robot** (free):
   - Sign up at https://uptimerobot.com
   - Add monitor for your backend URL
   - Set interval to 5 minutes

2. **Use cron-job.org** (free):
   - Create cron job to ping your URL every 10 minutes
   - URL: `https://your-app.onrender.com/health`

3. **Self-ping script** (if you have another server):
   ```bash
   */10 * * * * curl https://your-app.onrender.com/health
   ```

---

## 📝 Deployment Checklist

- [ ] Database deployed and connection string saved
- [ ] Redis deployed and connection string saved
- [ ] Backend deployed with all environment variables
- [ ] Database migrations run successfully
- [ ] Frontend deployed with correct API URL
- [ ] Health check endpoint working (`/health`)
- [ ] Uptime monitor configured (for Render)
- [ ] Custom domain configured (optional)
- [ ] SSL certificate active (automatic on most platforms)

---

## 🆘 Troubleshooting

### Backend won't start
- Check logs in platform dashboard
- Verify all environment variables are set
- Ensure PORT environment variable is used (Render uses dynamic ports)

### Database connection errors
- Verify DATABASE_URL format is correct
- Check if database is accessible from your region
- Ensure database is not paused (Render)

### Frontend can't connect to backend
- Verify VITE_API_URL is set correctly
- Check CORS settings in backend
- Ensure backend URL is accessible (not internal)

### Services spinning down
- Set up uptime monitor
- Consider upgrading to paid tier if needed

---

## 💡 Cost Optimization Tips

1. **Use separate services** for database/Redis (Supabase/Upstash) to avoid Render limits
2. **Deploy frontend to Vercel** (unlimited bandwidth)
3. **Use Render for backend only** (750 hours is enough)
4. **Monitor usage** to avoid unexpected charges
5. **Set up alerts** for service limits

---

## 🎉 Next Steps

After deployment:

1. Test all endpoints
2. Set up monitoring
3. Configure custom domain (optional)
4. Set up CI/CD for automatic deployments
5. Configure backups (important for production)

---

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Railway Documentation](https://docs.railway.app)
- [Fly.io Documentation](https://fly.io/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Neon Documentation](https://neon.tech/docs)
- [Upstash Documentation](https://upstash.com/docs)

---

**Need help?** Check the platform-specific configuration files in this directory or open an issue on GitHub.

