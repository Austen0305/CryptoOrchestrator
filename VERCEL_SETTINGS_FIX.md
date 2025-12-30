# Fix Vercel Project Settings Warning

## 🔍 Problem Identified

The **Project Settings** have overrides enabled that differ from `vercel.json`:
- **Current Project Settings:**
  - Build Command: `cd client && npm install --legacy-peer-deps && npm run build`
  - Output Directory: `client/dist`
  - Install Command: `cd client && npm install --legacy-peer-deps`

- **vercel.json (Correct):**
  - Build Command: `npm run build`
  - Output Directory: `dist`
  - Install Command: `npm install --legacy-peer-deps`

## ✅ Solution: Update Project Settings

### Step-by-Step Instructions:

1. **In Vercel Dashboard → Settings → Build and Deployment:**

2. **Find "Project Settings" section** (expand it if collapsed)

3. **Update each field and turn OFF overrides:**

   **Build Command:**
   - Change from: `cd client && npm install --legacy-peer-deps && npm run build`
   - Change to: `npm run build`
   - **Turn OFF the "Override" toggle** (should be grey, not blue)

   **Output Directory:**
   - Change from: `client/dist`
   - Change to: `dist`
   - **Turn OFF the "Override" toggle** (should be grey, not blue)

   **Install Command:**
   - Change from: `cd client && npm install --legacy-peer-deps`
   - Change to: `npm install --legacy-peer-deps`
   - **Turn OFF the "Override" toggle** (should be grey, not blue)

   **Development Command:**
   - Should be: `npm run dev`
   - **Turn OFF the "Override" toggle** (should be grey, not blue)

4. **Click "Save" button** at the bottom right

5. **Verify:**
   - The warning should disappear
   - Project Settings should now match Production Overrides
   - Both should match `vercel.json`

## 🎯 Why This Works

- `vite.config.ts` is in the root directory
- It has `root: path.resolve(__dirname, "client")` which tells Vite to use `client` as the source
- It has `outDir: path.resolve(__dirname, "dist")` which outputs to `dist` in the root
- So we build from root, Vite handles the client directory internally
- This matches our `vercel.json` configuration

## 📝 After Saving

Once you save, the warning should disappear and new deployments will use the correct settings from `vercel.json`.

---

*Last Updated: December 29, 2025*
