# Render API Automated Deployment

⚠️ **SECURITY WARNING**: Your Render API key has been exposed. Please rotate it after deployment:
1. Go to https://dashboard.render.com → Account Settings → API Keys
2. Delete the exposed key: `rnd_GKqBVkJWqGkGegqVL0DsID7Kfxze`
3. Generate a new API key
4. Update `render-api-key.txt` with the new key

## Quick Start

### Option 1: Automated Deployment (Recommended)

1. **Save your API key securely** (not in git):
   ```powershell
   # Save API key to a local file (gitignored)
   "rnd_GKqBVkJWqGkGegqVL0DsID7Kfxze" | Out-File -FilePath "render-api-key.txt" -NoNewline
   ```

2. **Run the deployment script**:
   ```powershell
   .\scripts\deploy-render.ps1 -GitHubRepo "your-username/Crypto-Orchestrator"
   ```

3. **Follow the prompts** and the script will create:
   - PostgreSQL database
   - Redis instance
   - Backend web service
   - Frontend static site

### Option 2: Manual Deployment (Easier)

The Render API can be complex. For first-time deployment, **manual deployment via dashboard is recommended**:

1. Follow **QUICK_START_FREE_HOSTING.md** for step-by-step manual instructions
2. It's faster and easier for first-time setup
3. You can use the API for future updates

## API Key Security

### Current Status
- ⚠️ Your API key was shared publicly
- 🔒 It's been saved to `render-api-key.txt` (gitignored)
- 🔄 **You should rotate it after deployment**

### How to Rotate

1. **Delete the exposed key**:
   - Go to https://dashboard.render.com
   - Account Settings → API Keys
   - Delete: `rnd_GKqBVkJWqGkGegqVL0DsID7Kfxze`

2. **Generate a new key**:
   - Click "New API Key"
   - Copy the new key
   - Update `render-api-key.txt`:
     ```powershell
     "your-new-key" | Out-File -FilePath "render-api-key.txt" -NoNewline
     ```

3. **Never commit API keys to git**:
   - ✅ `render-api-key.txt` is in `.gitignore`
   - ✅ Never share API keys publicly
   - ✅ Use environment variables in CI/CD

## Manual Deployment Steps

If you prefer manual deployment (recommended for first time):

1. **Generate secrets**:
   ```powershell
   .\scripts\setup-free-hosting.ps1
   ```

2. **Follow QUICK_START_FREE_HOSTING.md**:
   - Deploy PostgreSQL
   - Deploy Redis
   - Deploy Backend
   - Deploy Frontend
   - Run migrations

## Troubleshooting

### API Errors

If the automated script fails:
- **Use manual deployment** (it's actually easier!)
- Check Render API documentation: https://render.com/docs/api
- Verify your API key has proper permissions

### Common Issues

1. **"Owner ID required"**:
   - The API needs your Render account owner ID
   - Manual deployment avoids this complexity

2. **"Repository not found"**:
   - Connect your GitHub repo in Render dashboard first
   - Then retry the script

3. **"Invalid API key"**:
   - Verify the key is correct
   - Check if it was rotated/deleted

## Recommendation

**For your first deployment, use manual deployment:**
- ✅ Easier to understand
- ✅ Better error messages
- ✅ More control
- ✅ Faster to get started

**Use API automation for:**
- 🔄 Future updates
- 🔄 CI/CD pipelines
- 🔄 Multiple deployments
- 🔄 Automated scaling

## Next Steps

1. **Rotate your API key** (important!)
2. **Choose deployment method**:
   - Manual: Follow QUICK_START_FREE_HOSTING.md
   - Automated: Run `.\scripts\deploy-render.ps1`
3. **Set up Uptime Robot** to keep services alive
4. **Test your deployment**

---

**Remember**: Your API key is like a password - keep it secret! 🔒

