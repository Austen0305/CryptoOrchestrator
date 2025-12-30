# Vercel Deployment Troubleshooting

## Current Configuration

### vercel.json
- Build Command: `npm run build`
- Output Directory: `dist`
- Framework: `vite`
- Install Command: `npm install --legacy-peer-deps`

### vite.config.ts
- Root: `client` directory
- Output: `dist` (in project root)

## Potential Issues

### 1. Root Directory Mismatch
**Problem:** Vite is configured to use `client` as root, but Vercel might not know this.

**Solution:** Set Root Directory in Vercel Dashboard:
1. Go to Settings → General
2. Set "Root Directory" to `.` (project root)
3. OR set it to `client` if you want Vercel to build from there

### 2. Build Command Location
**Problem:** The build command runs from root, but Vite expects to be in client context.

**Current setup should work because:**
- `vite.config.ts` has `root: path.resolve(__dirname, "client")`
- This means Vite knows to use `client` as the root even when run from project root

### 3. Output Directory
**Problem:** Output goes to `dist` in root, which matches `vercel.json` configuration.

**This should be correct.**

## Steps to Fix

### Option 1: Check Vercel Dashboard Settings
1. Go to **Settings → General**
2. Check if "Root Directory" is set correctly
3. Should be `.` (dot) for project root

### Option 2: Check Build Logs
1. Go to **Deployments** tab
2. Click on the failed/stuck deployment
3. Check the **Build Logs** for specific errors
4. Look for:
   - Module not found errors
   - Path resolution errors
   - Build command failures

### Option 3: Verify Build Works Locally
```bash
# Test the build locally
npm install --legacy-peer-deps
npm run build

# Check if dist folder is created
ls dist
```

### Option 4: Manual Redeploy
1. Go to **Deployments** tab
2. Find the latest deployment
3. Click **⋯** (three dots)
4. Click **Redeploy**
5. Watch the build logs

## Common Errors

### Error: "Cannot find module"
- **Cause:** Dependencies not installed
- **Fix:** Ensure `installCommand` is correct

### Error: "Output directory not found"
- **Cause:** Build didn't create dist folder
- **Fix:** Check build command runs successfully

### Error: "Build timeout"
- **Cause:** Build takes too long
- **Fix:** Optimize build or upgrade Vercel plan

## Next Steps

1. Check Vercel dashboard for specific error message
2. Review build logs
3. Verify local build works
4. Try manual redeploy

---

*Last Updated: December 29, 2025*
