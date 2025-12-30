# Vercel Environment Variables Configuration

This document describes all environment variables required for deploying the CryptoOrchestrator frontend to Vercel.

## Required Environment Variables

### Backend API Configuration

#### `VITE_API_URL`
- **Description**: The base URL for the backend API (HTTPS required for production)
- **Example**: `https://feel-copies-liberty-round.trycloudflare.com` (Cloudflare Tunnel)
- **Required**: Yes
- **Format**: Must be HTTPS when frontend is HTTPS (Vercel)
- **Note**: If using Cloudflare Tunnel, use the HTTPS URL provided by the tunnel

#### `VITE_WS_BASE_URL` (Optional)
- **Description**: The base WebSocket URL for real-time connections
- **Example**: `wss://feel-copies-liberty-round.trycloudflare.com` (WSS for secure WebSocket)
- **Required**: No (will derive from `VITE_API_URL` if not set)
- **Format**: Must be WSS (secure WebSocket) when frontend is HTTPS
- **Note**: Automatically converts HTTP to WS and HTTPS to WSS if not provided

### Web3/Wallet Configuration

#### `VITE_WALLETCONNECT_PROJECT_ID`
- **Description**: WalletConnect Project ID for Web3 wallet connections
- **Example**: `your-walletconnect-project-id`
- **Required**: No (only if using WalletConnect features)
- **How to get**: Create a project at https://cloud.walletconnect.com/

#### `VITE_VAPID_PUBLIC_KEY`
- **Description**: VAPID public key for push notifications
- **Example**: `BKx...` (base64 encoded public key)
- **Required**: No (only if using push notifications)
- **How to generate**: Use web-push library or online generator

## Setting Environment Variables in Vercel

### Via Vercel Dashboard

1. Go to your project: https://vercel.com/dashboard
2. Click on **Settings** → **Environment Variables**
3. Add each variable:
   - **Name**: `VITE_API_URL`
   - **Value**: Your backend HTTPS URL
   - **Environment**: Production, Preview, Development (select all)
4. Click **Save**
5. Repeat for other variables

### Via Vercel CLI

```bash
vercel env add VITE_API_URL
# Enter the value when prompted
# Select environments: Production, Preview, Development

vercel env add VITE_WS_BASE_URL
# Enter the WSS URL (optional)

vercel env add VITE_WALLETCONNECT_PROJECT_ID
# Enter your WalletConnect project ID (optional)
```

### Via vercel.json (Not Recommended)

Environment variables in `vercel.json` are not recommended as they may expose sensitive data. Use the dashboard or CLI instead.

## Cloudflare Tunnel Setup

If your backend is behind a Cloudflare Tunnel, you need to:

1. **Set up the tunnel** on your backend server (see `scripts/deployment/setup-cloudflare-tunnel.sh`)
2. **Get the HTTPS URL** from Cloudflare (e.g., `https://your-tunnel.trycloudflare.com`)
3. **Set `VITE_API_URL`** to the HTTPS URL
4. **Set `VITE_WS_BASE_URL`** to the WSS URL (replace `https://` with `wss://`)

Example:
```bash
VITE_API_URL=https://feel-copies-liberty-round.trycloudflare.com
VITE_WS_BASE_URL=wss://feel-copies-liberty-round.trycloudflare.com
```

## Verification

After setting environment variables:

1. **Redeploy** your Vercel project (or wait for auto-deploy)
2. **Check build logs** to ensure variables are loaded
3. **Test the site**:
   - Open browser console
   - Check network requests to verify API calls use correct URL
   - Verify WebSocket connections use WSS (secure)

## Troubleshooting

### Mixed Content Errors
- **Problem**: Frontend (HTTPS) trying to connect to backend (HTTP)
- **Solution**: Use HTTPS backend URL (Cloudflare Tunnel or reverse proxy)

### WebSocket Connection Failed
- **Problem**: WebSocket trying to use WS instead of WSS
- **Solution**: Set `VITE_WS_BASE_URL` to WSS URL or ensure `VITE_API_URL` is HTTPS

### Environment Variables Not Loading
- **Problem**: Variables set but not available in build
- **Solution**: 
  - Ensure variables start with `VITE_` prefix
  - Redeploy after adding variables
  - Check variable names match exactly (case-sensitive)

## Current Configuration

Based on the codebase, the following variables are currently used:

- ✅ `VITE_API_URL` - Backend API URL
- ✅ `VITE_WS_BASE_URL` - WebSocket base URL (optional, derives from API URL)
- ✅ `VITE_WALLETCONNECT_PROJECT_ID` - WalletConnect integration (optional)
- ✅ `VITE_VAPID_PUBLIC_KEY` - Push notifications (optional)

## Security Notes

- ⚠️ Never commit environment variables to git
- ⚠️ Use HTTPS/WSS in production
- ⚠️ Keep WalletConnect Project ID and VAPID keys secure
- ⚠️ Rotate keys regularly
