# Frontend Fixes Applied

## Issues Fixed

### 1. Token Storage Inconsistency (CRITICAL)
**Problem**: `useAuth.tsx` was storing tokens as `"token"` and `"refreshToken"`, but all API clients (`apiClient.ts`, `queryClient.ts`) and WebSocket hooks were looking for `"auth_token"` and `"refresh_token"`.

**Impact**: Users could log in successfully, but all API calls and WebSocket connections would fail because they couldn't find the token.

**Fix**: Updated `useAuth.tsx` to use consistent token keys:
- Changed `localStorage.setItem("token", ...)` → `localStorage.setItem("auth_token", ...)`
- Changed `localStorage.setItem("refreshToken", ...)` → `localStorage.setItem("refresh_token", ...)`
- Updated all token retrieval and cleanup code to use the new keys
- Added `apiClient.setAuthToken()` call in `useEffect` to initialize token on mount

**Files Modified**:
- `client/src/hooks/useAuth.tsx`

### 2. useWalletWebSocket Token Access
**Problem**: `useWalletWebSocket.ts` was trying to access `token` from `useAuth()`, but `useAuth` doesn't expose a `token` property.

**Impact**: Wallet WebSocket connections would fail to initialize.

**Fix**: Updated `useWalletWebSocket` to:
- Use `isAuthenticated` from `useAuth()` instead
- Get token directly from localStorage/sessionStorage (consistent with other hooks)
- Only connect when authenticated and token exists

**Files Modified**:
- `client/src/hooks/useWalletWebSocket.ts`

## Testing Checklist

- [ ] Frontend loads at http://localhost:5173
- [ ] Landing page displays correctly
- [ ] Login flow works and stores token correctly
- [ ] API calls work after login (check browser Network tab)
- [ ] WebSocket connections establish successfully
- [ ] Token persists across page refreshes
- [ ] Logout clears tokens properly

## Next Steps

1. Test the frontend by starting both servers:
   ```bash
   npm run dev:fastapi  # Terminal 1
   npm run dev          # Terminal 2
   ```

2. Navigate to http://localhost:5173 and verify:
   - Landing page loads
   - Can register/login
   - After login, dashboard loads
   - API calls succeed (check browser console)
   - WebSocket connections work

3. If issues persist, check:
   - Browser console for errors
   - Network tab for failed API calls
   - Backend server is running on port 8000
   - CORS configuration allows frontend origin

## Notes

- The `main.tsx` file contains very aggressive layout fix code (runs every 25-50ms). This might cause performance issues but shouldn't prevent the app from loading.
- All token storage now consistently uses `auth_token` and `refresh_token` keys.
- API clients automatically read from localStorage/sessionStorage, so no additional changes needed.

