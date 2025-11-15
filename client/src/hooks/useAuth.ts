import { useState, useEffect, useCallback } from 'react';
import { useToast } from '@/hooks/use-toast';
import type { User, RegisterRequest } from '../../../shared/schema';

const API_BASE =
  (typeof window !== 'undefined' && (window as any).__API_BASE__) ||
  (import.meta as any)?.env?.VITE_API_BASE_URL ||
  '';

interface MFASetupResponse {
  secret: string;
  otpauthUrl: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

export const useAuth = () => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    token: null,
    isLoading: true,
    isAuthenticated: false,
  });

  const { toast } = useToast();

  // Initialize auth state from localStorage
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    const userStr = localStorage.getItem('auth_user');

    if (token && userStr) {
      try {
        const user = JSON.parse(userStr);
        setAuthState({
          user,
          token,
          isLoading: false,
          isAuthenticated: true,
        });
      } catch (error) {
        // Invalid stored data, clear it
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        setAuthState(prev => ({ ...prev, isLoading: false }));
      }
    } else {
      setAuthState(prev => ({ ...prev, isLoading: false }));
    }
  }, []);

  const login = useCallback(async (emailOrUsername: string, password: string): Promise<boolean> => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true }));

      console.log('[Auth] Attempting login with:', emailOrUsername);
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: emailOrUsername, password }),
      });
      console.log('[Auth] Login response status:', response.status);

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Login failed');
      }

      const { user, token } = data.data;

      // Store in localStorage
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_user', JSON.stringify(user));

      setAuthState({
        user,
        token,
        isLoading: false,
        isAuthenticated: true,
      });

      toast({
        title: 'Login successful',
        description: `Welcome back, ${user.name}!`,
      });

      return true;
    } catch (error) {
      setAuthState(prev => ({ ...prev, isLoading: false }));

      toast({
        title: 'Login failed',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });

      return false;
    }
  }, [toast]);

  const register = useCallback(async (userData: RegisterRequest): Promise<boolean> => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true }));

      const response = await fetch(`${API_BASE}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Registration failed');
      }

      const { user, token } = data.data;

      // Store in localStorage
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_user', JSON.stringify(user));

      setAuthState({
        user,
        token,
        isLoading: false,
        isAuthenticated: true,
      });

      toast({
        title: 'Registration successful',
        description: `Welcome, ${user.name}!`,
      });

      return true;
    } catch (error) {
      setAuthState(prev => ({ ...prev, isLoading: false }));

      toast({
        title: 'Registration failed',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });

      return false;
    }
  }, [toast]);

  const logout = useCallback(() => {
    // Clear localStorage
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');

    setAuthState({
      user: null,
      token: null,
      isLoading: false,
      isAuthenticated: false,
    });

    toast({
      title: 'Logged out',
      description: 'You have been successfully logged out.',
    });
  }, [toast]);

  const getAuthHeaders = useCallback(() => {
    const headers: Record<string, string> = {};
    if (!authState.token) return headers;
    headers['Authorization'] = `Bearer ${authState.token}`;
    return headers;
  }, [authState.token]);

  const setupMFA = useCallback(async (): Promise<MFASetupResponse> => {
    const response = await fetch(`${API_BASE}/api/auth/mfa/setup`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Failed to setup MFA');
    }

    return data.data ?? data;
  }, [getAuthHeaders]);

  const verifyMFA = useCallback(async (token: string): Promise<boolean> => {
    const response = await fetch(`${API_BASE}/api/auth/mfa/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: JSON.stringify({ token }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Failed to verify MFA');
    }

    // Update user state to reflect MFA is enabled
    if (authState.user) {
      const updatedUser = { ...authState.user, mfaEnabled: true };
      localStorage.setItem('auth_user', JSON.stringify(updatedUser));
      setAuthState(prev => ({ ...prev, user: updatedUser }));
    }

    toast({
      title: 'MFA enabled',
      description: 'Two-factor authentication has been successfully enabled.',
    });

    return true;
  }, [getAuthHeaders, authState.user, toast]);

  return {
    ...authState,
    login,
    register,
    logout,
    getAuthHeaders,
    setupMFA,
    verifyMFA,
  };
};
