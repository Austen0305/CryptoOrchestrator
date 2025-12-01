/**
 * Token Refresh Hook
 * Automatically refreshes JWT tokens before expiration
 */

import { useEffect, useRef } from 'react';
import { useAuth } from './useAuth';

const TOKEN_REFRESH_BUFFER = 5 * 60 * 1000; // Refresh 5 minutes before expiration

export function useTokenRefresh() {
  const { refreshToken, isAuthenticated } = useAuth();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    // Parse token to get expiration time
    const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    if (!token) return;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expirationTime = payload.exp * 1000; // Convert to milliseconds
      const now = Date.now();
      const timeUntilExpiration = expirationTime - now;
      const refreshTime = timeUntilExpiration - TOKEN_REFRESH_BUFFER;

      // If token expires soon, refresh immediately
      if (refreshTime <= 0) {
        refreshToken();
      } else {
        // Schedule refresh before expiration
        const timeout = setTimeout(() => {
          refreshToken();
        }, refreshTime);

        // Also set up periodic check (every minute)
        intervalRef.current = setInterval(() => {
          const currentToken = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
          if (!currentToken) {
            if (intervalRef.current) {
              clearInterval(intervalRef.current);
              intervalRef.current = null;
            }
            return;
          }

          try {
            const currentPayload = JSON.parse(atob(currentToken.split('.')[1]));
            const currentExpiration = currentPayload.exp * 1000;
            const timeLeft = currentExpiration - Date.now();

            if (timeLeft <= TOKEN_REFRESH_BUFFER) {
              refreshToken();
            }
          } catch (e) {
            // Token invalid, clear interval
            if (intervalRef.current) {
              clearInterval(intervalRef.current);
              intervalRef.current = null;
            }
          }
        }, 60000); // Check every minute

        return () => {
          clearTimeout(timeout);
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
        };
      }
    } catch (e) {
      // Token parsing failed, try to refresh
      refreshToken();
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isAuthenticated, refreshToken]);
}

