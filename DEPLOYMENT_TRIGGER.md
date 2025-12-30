# Manual Vercel Deployment Trigger Guide

## 🚨 Issue: Deployment Not Triggering Automatically

If Vercel isn't auto-deploying after git push, here are multiple ways to trigger a deployment:

## Method 1: Manual Redeploy via Vercel Dashboard (Easiest)

1. Go to: **https://vercel.com/dashboard**
2. Click on your project: **cryptoorchestrator**
3. Go to **"Deployments"** tab
4. Find the **latest deployment** (even if it's old/failed)
5. Click the **three dots (⋯)** menu on that deployment
6. Select **"Redeploy"**
7. **IMPORTANT:** Check **"Redeploy without cache"** checkbox
8. Click **"Redeploy"**

This will trigger a new build with the latest code from GitHub.

## Method 2: Update Vercel Settings (Triggers Deployment)

1. Go to: **Vercel Dashboard → Project Settings → Build and Deployment**
2. Find **"Node.js Version"** section
3. Change from **"24.x"** to **"20.x"** (or vice versa, then back to 20.x)
4. Click **"Save"**
5. This automatically triggers a new deployment

## Method 3: Create Empty Commit to Trigger

Run this command to create an empty commit that triggers Vercel:

```bash
git commit --allow-empty -m "Trigger Vercel deployment - Node.js version fix"
git push origin main
```

## Method 4: Check GitHub Integration

Verify Vercel is connected to GitHub:

1. Go to: **Vercel Dashboard → Project Settings → Git**
2. Verify **"Connected Git Repository"** shows your repo
3. Check **"Production Branch"** is set to `main`
4. If disconnected, reconnect it

## Method 5: Use Vercel CLI (If Installed)

```bash
# Install Vercel CLI if not installed
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

## 🔍 Troubleshooting: Why Auto-Deploy Might Not Work

### Check 1: GitHub Webhook Status
1. Go to: **GitHub → Repository → Settings → Webhooks**
2. Look for Vercel webhook
3. Check if it's active and has recent deliveries

### Check 2: Vercel Git Integration
1. Go to: **Vercel Dashboard → Project Settings → Git**
2. Verify integration is active
3. Check if there are any error messages

### Check 3: Branch Protection
- Ensure you're pushing to the branch Vercel is watching (usually `main`)
- Check if branch protection rules are blocking webhooks

## ✅ Recommended Action Plan

**Right Now:**
1. **Update Node.js version in Vercel** (Method 2) - This will trigger deployment AND fix the version issue
2. **OR** Use Method 1 to manually redeploy

**After Deployment:**
1. Monitor build logs
2. Verify deployment succeeds
3. Test the deployed site

## 📝 Current Status

- [x] Code committed and pushed to GitHub
- [x] Node.js version updated in project files (20.x)
- [ ] **Action Required:** Update Vercel Node.js version to 20.x (triggers deployment)
- [ ] Verify deployment succeeds

---

**Quick Fix:** Use Method 2 (Update Vercel Settings) - it fixes the Node version AND triggers deployment in one step!
