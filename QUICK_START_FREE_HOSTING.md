# Quick Start: Free Hosting Deployment

This is a simplified guide to get your app running on free hosting in under 10 minutes.

## 🎯 Recommended: Render.com (Easiest)

### Step 1: Prepare Your Repository

1. Make sure your code is pushed to GitHub
2. Run the setup script to generate secrets:
   ```bash
   # Windows
   powershell -ExecutionPolicy Bypass -File scripts/setup-free-hosting.ps1
   
   # Mac/Linux
   bash scripts/setup-free-hosting.sh
   ```

### Step 2: Deploy to Render (5 minutes)

1. **Sign up**: Go to https://render.com and sign up with GitHub

2. **Deploy Database**:
   - Click "New +" → "PostgreSQL"
   - Name: `crypto-db`
   - Plan: **Free**
   - Click "Create"
   - **Copy the Internal Database URL** (starts with `postgresql://`)

3. **Deploy Redis**:
   - Click "New +" → "Redis"
   - Name: `crypto-redis`
   - Plan: **Free**
   - Click "Create"
   - **Copy the Internal Redis URL** (starts with `redis://`)

4. **Deploy Backend**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Name: `crypto-backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m uvicorn server_fastapi.main:app --host 0.0.0.0 --port $PORT`
   - Plan: **Free**
   - Add Environment Variables:
     ```
     DATABASE_URL=<paste Internal Database URL>
     REDIS_URL=<paste Internal Redis URL>
     JWT_SECRET=<paste from .env.production>
     JWT_REFRESH_SECRET=<paste from .env.production>
     EXCHANGE_KEY_ENCRYPTION_KEY=<paste from .env.production>
     PORT=8000
     ENVIRONMENT=production
     ```
   - Click "Create Web Service"
   - Wait for deployment (2-3 minutes)

5. **Run Migrations**:
   - Once backend is live, click "Shell" tab
   - Run: `alembic upgrade head`

6. **Deploy Frontend**:
   - Click "New +" → "Static Site"
   - Connect your GitHub repo
   - Name: `crypto-frontend`
   - Root Directory: `client`
   - Build Command: `npm install --legacy-peer-deps && npm run build`
   - Publish Directory: `client/dist`
   - Add Environment Variable:
     ```
     VITE_API_URL=https://crypto-backend.onrender.com
     ```
   - Click "Create Static Site"

### Step 3: Keep It Alive (Important!)

Render free tier spins down after 15 minutes of inactivity. Set up a monitor:

1. Go to https://uptimerobot.com (free)
2. Sign up and add a monitor:
   - URL: `https://crypto-backend.onrender.com/health`
   - Type: HTTP(s)
   - Interval: 5 minutes
3. This will ping your app every 5 minutes to keep it awake

### Step 4: Test Your Deployment

1. Visit your frontend URL (from Render dashboard)
2. Try logging in or creating an account
3. Check backend logs if something doesn't work

## ✅ You're Done!

Your app is now live on:
- Frontend: `https://crypto-frontend.onrender.com`
- Backend: `https://crypto-backend.onrender.com`

## 🚨 Common Issues

**Backend won't start:**
- Check logs in Render dashboard
- Verify all environment variables are set
- Make sure DATABASE_URL and REDIS_URL are correct

**Frontend can't connect:**
- Verify VITE_API_URL matches your backend URL
- Check CORS settings (should be enabled for Render domains)

**Database connection error:**
- Use the **Internal Database URL** (not external)
- Make sure database is in same region as backend

**App spins down:**
- Set up Uptime Robot monitor (see Step 3)
- Or upgrade to paid tier

## 📚 Next Steps

- Read [FREE_HOSTING_GUIDE.md](./FREE_HOSTING_GUIDE.md) for detailed options
- Set up custom domain (optional)
- Configure CI/CD for auto-deployments
- Set up monitoring and alerts

---

**Need help?** Check the full guide or open an issue!

