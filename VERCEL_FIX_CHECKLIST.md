# Vercel Deployment Fix Checklist

## ✅ Fixed Issues
1. ✅ Removed `rootDirectory` from `vercel.json` (causes schema validation error)
2. ✅ Removed conflicting `client/vercel.json` file
3. ✅ Verified `vercel.json` is correct

## 🔍 Current Configuration

### vercel.json (Root)
- Build Command: `npm run build`
- Output Directory: `dist`
- Framework: `vite`
- Install Command: `npm install --legacy-peer-deps`

### vite.config.ts
- Root: `client` directory (set in config)
- Output: `dist` (in project root)

## ⚙️ Vercel Dashboard Settings to Check

### 1. Settings → General
- **Root Directory:** Should be `.` (dot) or left empty
- This tells Vercel where the project root is

### 2. Settings → Build and Deployment
Verify these match `vercel.json`:
- **Framework Preset:** Vite
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Install Command:** `npm install --legacy-peer-deps`
- **Development Command:** `npm run dev`

### 3. Settings → Environment Variables
Make sure these are set:
- `VITE_API_URL` = `https://feel-copies-liberty-round.trycloudflare.com`
- `VITE_WS_BASE_URL` = `wss://feel-copies-liberty-round.trycloudflare.com`

## 🚨 Common Issues & Solutions

### Issue 1: Build Fails with "Cannot find module"
**Solution:** 
- Check that `installCommand` includes `--legacy-peer-deps`
- Verify all dependencies are in root `package.json`

### Issue 2: Output Directory Not Found
**Solution:**
- Verify build creates `dist` folder
- Check that `outDir` in `vite.config.ts` matches `outputDirectory` in `vercel.json`

### Issue 3: Schema Validation Error
**Solution:**
- ✅ Already fixed - removed `rootDirectory` from `vercel.json`
- Make sure no other invalid properties exist

### Issue 4: Build Succeeds but Site Doesn't Work
**Solution:**
- Check environment variables are set correctly
- Verify API URLs are correct
- Check browser console for errors

## 📋 Next Steps

1. **Check Latest Deployment:**
   - Go to Deployments tab
   - Find the latest deployment (commit `07f158a`)
   - Check if it's building or failed
   - Read the build logs

2. **If Still Failing:**
   - Copy the exact error message from build logs
   - Check which step failed (Installing, Building, etc.)
   - Verify all settings match this checklist

3. **Manual Redeploy:**
   - Go to Deployments
   - Click "Redeploy" on latest deployment
   - Watch build logs in real-time

## 🔧 If Build Still Fails

Please provide:
1. The exact error message from Vercel build logs
2. Which step failed (Installing dependencies, Building, etc.)
3. Any warnings or errors shown

---

*Last Updated: December 29, 2025*
