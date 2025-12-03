# Render Deployment Guide

This guide covers deploying to Render.com using the API key and automated scripts.

## 🔑 API Key Setup

Your Render API key has been stored in `render-api-key.txt` (already in `.gitignore` for security).

**⚠️ Security Note:** Never commit API keys to git. The file is already in `.gitignore`.

## 🚀 Deployment Methods

### Method 1: Blueprint Deployment (Recommended - Easiest)

This uses the `render.yaml` file to deploy everything with one click:

1. **Run setup script:**
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/setup-render-services.ps1
   ```

2. **Or manually:**
   - Go to https://dashboard.render.com
   - Click "New +" → "Blueprint"
   - Connect your GitHub repo
   - Render will automatically use `render.yaml`
   - Click "Apply" to create all services

**Advantages:**
- ✅ One-click deployment
- ✅ Creates all services (database, Redis, backend, frontend)
- ✅ Automatically links services together
- ✅ Sets up environment variables

### Method 2: API Deployment (For Existing Services)

If you've already created services manually, use the API to trigger deployments:

```powershell
# Deploy all services
powershell -ExecutionPolicy Bypass -File scripts/deploy-render.ps1

# Deploy backend only
powershell -ExecutionPolicy Bypass -File scripts/deploy-render.ps1 -DeployBackend

# Deploy frontend only
powershell -ExecutionPolicy Bypass -File scripts/deploy-render.ps1 -DeployFrontend

# Deploy specific service by ID
powershell -ExecutionPolicy Bypass -File scripts/deploy-render.ps1 -ServiceId <service-id>
```

**What it does:**
- Lists all your Render services
- Triggers new deployments for selected services
- Shows deployment status

### Method 3: Manual Deployment (Step-by-Step)

Follow `QUICK_START_FREE_HOSTING.md` for detailed manual setup.

## 📋 Pre-Deployment Checklist

Before deploying:

- [ ] Code pushed to GitHub
- [ ] Secrets generated (run `scripts/setup-free-hosting.ps1`)
- [ ] `render.yaml` exists in project root
- [ ] API key stored in `render-api-key.txt`

## 🔧 Using the API Scripts

### List Services

The deployment script automatically lists all your services when run.

### Deploy Services

```powershell
# Show help
.\scripts\deploy-render.ps1 -Help

# Deploy everything
.\scripts\deploy-render.ps1

# Deploy specific service
.\scripts\deploy-render.ps1 -ServiceId <service-id>
```

### Check Deployment Status

After triggering a deployment:
1. Go to https://dashboard.render.com
2. Click on your service
3. View the "Events" or "Logs" tab

## 🎯 Recommended Workflow

### First Time Setup:

1. **Generate secrets:**
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/setup-free-hosting.ps1
   ```

2. **Deploy using Blueprint:**
   - Go to Render dashboard
   - Use Blueprint feature with `render.yaml`
   - Or run: `scripts/setup-render-services.ps1`

3. **Run migrations:**
   - Backend service → Shell tab
   - Run: `alembic upgrade head`

4. **Set up monitoring:**
   - Uptime Robot to keep services alive

### Subsequent Deployments:

1. **Push code to GitHub:**
   ```bash
   git add .
   git commit -m "Your changes"
   git push
   ```

2. **Trigger deployment via API:**
   ```powershell
   .\scripts\deploy-render.ps1
   ```

   Or Render will auto-deploy if you have auto-deploy enabled.

## 🔐 API Key Management

### Current Setup:
- API key stored in: `render-api-key.txt`
- File is in `.gitignore` (won't be committed)
- Used by deployment scripts

### To Update API Key:
1. Edit `render-api-key.txt`
2. Replace with new key
3. Save file

### To Get New API Key:
1. Go to https://dashboard.render.com/account/api-keys
2. Click "Create API Key"
3. Copy the key
4. Update `render-api-key.txt`

## 🚨 Troubleshooting

### API Key Issues:
- **Error: "API key is empty"**
  - Check `render-api-key.txt` exists and has content
  - Verify file is not empty

- **Error: "Failed to connect to Render API"**
  - Verify API key is correct
  - Check API key hasn't been revoked
  - Ensure you have internet connection

### Deployment Issues:
- **Service not found:**
  - Services must be created first (use Blueprint or manual setup)
  - Check service names match what you expect

- **Deployment fails:**
  - Check Render dashboard logs
  - Verify environment variables are set
  - Check build commands are correct

## 📚 Additional Resources

- [Render API Documentation](https://render.com/docs/api)
- [Render Blueprint Spec](https://render.com/docs/blueprint-spec)
- [Quick Start Guide](QUICK_START_FREE_HOSTING.md)
- [Full Hosting Guide](FREE_HOSTING_GUIDE.md)

## 🎉 Next Steps

1. ✅ API key is set up
2. 🚀 Deploy using Blueprint (recommended) or API scripts
3. ✅ Run database migrations
4. ✅ Set up Uptime Robot
5. ✅ Test your deployment

---

**Ready to deploy?** Run `scripts/setup-render-services.ps1` to get started!

