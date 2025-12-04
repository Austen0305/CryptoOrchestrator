import React, { useState, useEffect, createContext, useContext, ReactNode } from "react";
import { api as apiClient } from "@/lib/apiClient";

interface User {
  id: number;
  email: string;
  username: string;
  role: string;
  is_active: boolean;
  is_email_verified: boolean;
  first_name?: string;
  last_name?: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<boolean>;
  register: (email: string, username: string, password: string, firstName?: string, lastName?: string) => Promise<boolean>;
  logout: () => Promise<void>;
  forgotPassword: (email: string) => Promise<boolean>;
  resetPassword: (token: string, newPassword: string) => Promise<boolean>;
  refreshToken: () => Promise<boolean>;
  setupMFA: () => Promise<{ secret: string; otpauthUrl: string }>;
  verifyMFA: (token: string) => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check for stored token and validate it
    const token = localStorage.getItem("auth_token") || sessionStorage.getItem("auth_token");
    if (token) {
      apiClient.setAuthToken(token);
      validateToken();
    } else {
      setIsLoading(false);
    }
  }, []);

  const validateToken = async () => {
    try {
      // Try /api/auth/profile first (main auth route), fallback to /api/auth/me (SaaS route)
      let response: User;
      try {
        response = await apiClient.get<User>("/auth/profile");
      } catch (err) {
        // Fallback to /me endpoint if profile doesn't exist
        response = await apiClient.get<User>("/auth/me");
      }
      setUser(response);
      setError(null);
    } catch (err) {
      // Token invalid or expired - clear it
      localStorage.removeItem("auth_token");
      localStorage.removeItem("refresh_token");
      sessionStorage.removeItem("auth_token");
      sessionStorage.removeItem("refresh_token");
      apiClient.setAuthToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string, rememberMe = false): Promise<boolean> => {
    try {
      setError(null);
      setIsLoading(true);
      
      // Add timeout to prevent infinite loading
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => {
          reject(new Error("Login request timed out. Please check your connection and try again."));
        }, 10000); // 10 second timeout
      });

      const loginPromise = apiClient.post("/auth/login", {
        email,
        password,
      });

      const response = await Promise.race([loginPromise, timeoutPromise]) as { access_token: string; refresh_token?: string; user: User };

      const { access_token, refresh_token, user: userData } = response;

      // Store tokens - use consistent key 'auth_token' to match API clients
      if (rememberMe) {
        localStorage.setItem("auth_token", access_token);
        localStorage.setItem("refresh_token", refresh_token || "");
      } else {
        sessionStorage.setItem("auth_token", access_token);
        sessionStorage.setItem("refresh_token", refresh_token || "");
      }

      // Set default token in apiClient
      apiClient.setAuthToken(access_token);

      setUser(userData);
      setIsLoading(false);
      return true;
    } catch (err: unknown) {
      let errorMessage = "Unable to sign in. Please check your email and password.";
      
      // Extract error message from various error formats
      interface ApiError extends Error {
        response?: {
          data?: {
            detail?: string;
          };
        };
      }
      const apiError = err as ApiError;
      const rawMessage = apiError.response?.data?.detail || apiError.message || "";
      
      // Map common login errors to user-friendly messages
      if (rawMessage.includes('Invalid credentials') || rawMessage.includes('incorrect') || rawMessage.includes('wrong password')) {
        errorMessage = "The email or password you entered is incorrect. Please try again.";
      } else if (rawMessage.includes('not found') || rawMessage.includes('does not exist')) {
        errorMessage = "No account found with this email. Please check your email or create an account.";
      } else if (rawMessage.includes('HTTP 401') || rawMessage.includes('Unauthorized')) {
        errorMessage = "Invalid email or password. Please try again.";
      } else if (rawMessage.includes('HTTP 429') || rawMessage.includes('rate limit')) {
        errorMessage = "Too many login attempts. Please wait a few minutes and try again.";
      } else if (rawMessage.includes('HTTP 500') || rawMessage.includes('HTTP 503')) {
        errorMessage = "Our servers are temporarily unavailable. Please try again in a few moments.";
      } else if (rawMessage.includes('timeout') || rawMessage.includes('network')) {
        errorMessage = "Connection timeout. Please check your internet connection and try again.";
      } else if (rawMessage && rawMessage.length < 150) {
        // Use the message if it's reasonably short and user-friendly
        errorMessage = rawMessage;
      }
      
      setError(errorMessage);
      setIsLoading(false);
      return false;
    }
  };

  const register = async (
    email: string,
    username: string,
    password: string,
    firstName?: string,
    lastName?: string
  ): Promise<boolean> => {
    let timeoutId: number | undefined;
    try {
      setError(null);
      setIsLoading(true);
      
      // Add timeout wrapper to prevent hanging (10 seconds)
      const timeoutPromise = new Promise<never>((_, reject) => {
        timeoutId = window.setTimeout(() => {
          reject(
            new Error(
              "The request took too long. Please check your internet connection and try again."
            )
          );
        }, 10000);
      });

      // Disable retries for registration to fail fast
      const requestPromise = apiClient
        .post(
          "/auth/register",
          {
            email,
            username,
            password,
            first_name: firstName,
            last_name: lastName,
          },
          { maxRetries: 0 } // Disable retries - fail fast if server not available
        )
        .catch((err) => {
          throw err;
        });

      const response = (await Promise.race([requestPromise, timeoutPromise])) as {
        access_token?: string;
        refresh_token?: string;
        user?: User;
      };

      // Validate response structure
      if (!response || !response.access_token) {
        throw new Error("Unable to complete registration. Please try again later.");
      }

      const { access_token, refresh_token, user: userData } = response;

      if (!userData) {
        throw new Error("Registration completed but user data is missing. Please try logging in.");
      }

      // Store tokens - use consistent key 'auth_token' to match API clients
      // Store in both localStorage and sessionStorage for compatibility
      localStorage.setItem("auth_token", access_token);
      sessionStorage.setItem("auth_token", access_token);
      localStorage.setItem("refresh_token", refresh_token || "");
      sessionStorage.setItem("refresh_token", refresh_token || "");

      // Set default token in apiClient
      apiClient.setAuthToken(access_token);

      setUser(userData);
      setIsLoading(false);
      return true;
    } catch (err: unknown) {
      // User-friendly error messages
      let errorMessage = "Unable to create your account. Please try again.";
      
      if (err instanceof Error) {
        const message = err.message;
        
        // Map common error messages to user-friendly versions
        if (message.includes('HTTP 400') || message.includes('HTTP 422')) {
          // Validation errors - try to extract user-friendly message
          const match = message.match(/HTTP \d+: (.+)/);
          if (match) {
            try {
              const parsed = JSON.parse(match[1]);
              const detail = parsed.detail || parsed.message || '';
              
              // Make validation errors more user-friendly
              if (detail.includes('email')) {
                errorMessage = "Please enter a valid email address.";
              } else if (detail.includes('password')) {
                errorMessage = "Password must be at least 8 characters long.";
              } else if (detail.includes('username')) {
                errorMessage = "Username is already taken. Please choose another.";
              } else if (detail.includes('already exists') || detail.includes('already registered')) {
                errorMessage = "An account with this email already exists. Please log in instead.";
              } else {
                errorMessage = detail || errorMessage;
              }
            } catch {
              errorMessage = match[1] || errorMessage;
            }
          }
        } else if (message.includes('HTTP 409')) {
          errorMessage = "An account with this email already exists. Please log in instead.";
        } else if (message.includes('HTTP 500') || message.includes('HTTP 503')) {
          errorMessage = "Our servers are temporarily unavailable. Please try again in a few moments.";
        } else if (message.includes('timeout') || message.includes('took too long')) {
          errorMessage = "The request took too long. Please check your internet connection and try again.";
        } else if (message.includes('Failed to fetch') || message.includes('NetworkError') || message.includes('Network request failed')) {
          errorMessage = "Unable to connect to our servers. Please check your internet connection.";
        } else if (message.includes('Invalid response') || message.includes('missing')) {
          errorMessage = "Something went wrong during registration. Please try again.";
        } else {
          // Use the error message if it's already user-friendly, otherwise use default
          errorMessage = message.length < 100 ? message : errorMessage;
        }
      }
      
      setError(errorMessage);
      setIsLoading(false);
      return false;
    } finally {
      // Always clear timeout if it was set to avoid stray timeout errors
      if (timeoutId !== undefined) {
        clearTimeout(timeoutId);
      }
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await apiClient.post("/auth/logout", {});
    } catch (err) {
      // Ignore errors on logout
    } finally {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("auth_user");
      sessionStorage.removeItem("auth_token");
      sessionStorage.removeItem("refresh_token");
      apiClient.setAuthToken(null);
      setUser(null);
    }
  };

  const forgotPassword = async (email: string): Promise<boolean> => {
    try {
      setError(null);
      await apiClient.post("/auth/forgot-password", { email });
      return true;
    } catch (err) {
      interface ApiError extends Error {
        response?: {
          data?: {
            detail?: string;
          };
        };
      }
      const apiError = err as ApiError;
      const rawMessage = apiError.response?.data?.detail || apiError.message || "";
      
      let errorMessage = "Unable to send password reset email. Please try again.";
      
      if (rawMessage.includes('not found') || rawMessage.includes('does not exist')) {
        errorMessage = "No account found with this email address.";
      } else if (rawMessage.includes('HTTP 429') || rawMessage.includes('rate limit')) {
        errorMessage = "Too many requests. Please wait a few minutes before requesting another reset email.";
      } else if (rawMessage.includes('HTTP 500') || rawMessage.includes('HTTP 503')) {
        errorMessage = "Our servers are temporarily unavailable. Please try again later.";
      } else if (rawMessage && rawMessage.length < 150) {
        errorMessage = rawMessage;
      }
      
      setError(errorMessage);
      return false;
    }
  };

  const resetPassword = async (token: string, newPassword: string): Promise<boolean> => {
    try {
      setError(null);
      await apiClient.post("/auth/reset-password", {
        token,
        new_password: newPassword,
      });
      return true;
    } catch (err) {
      interface ApiError extends Error {
        response?: {
          data?: {
            detail?: string;
          };
        };
      }
      const apiError = err as ApiError;
      const rawMessage = apiError.response?.data?.detail || apiError.message || "";
      
      let errorMessage = "Unable to reset your password. Please try again.";
      
      if (rawMessage.includes('invalid') || rawMessage.includes('expired') || rawMessage.includes('token')) {
        errorMessage = "This password reset link is invalid or has expired. Please request a new one.";
      } else if (rawMessage.includes('password') && (rawMessage.includes('weak') || rawMessage.includes('short'))) {
        errorMessage = "Password must be at least 8 characters long and contain both letters and numbers.";
      } else if (rawMessage.includes('HTTP 400') || rawMessage.includes('HTTP 422')) {
        errorMessage = "Please check that your password meets the requirements and try again.";
      } else if (rawMessage.includes('HTTP 500') || rawMessage.includes('HTTP 503')) {
        errorMessage = "Our servers are temporarily unavailable. Please try again later.";
      } else if (rawMessage && rawMessage.length < 150) {
        errorMessage = rawMessage;
      }
      
      setError(errorMessage);
      return false;
    }
  };

  const refreshToken = async (): Promise<boolean> => {
    try {
      const refreshTokenValue =
        localStorage.getItem("refresh_token") ||
        sessionStorage.getItem("refresh_token");

      if (!refreshTokenValue) {
        return false;
      }

      const response = await apiClient.post<{ access_token: string }>(
        "/auth/refresh",
        {
          refresh_token: refreshTokenValue,
        }
      );

      const { access_token } = response;

      // Update stored token - use consistent key 'auth_token'
      if (localStorage.getItem("refresh_token")) {
        localStorage.setItem("auth_token", access_token);
      } else {
        sessionStorage.setItem("auth_token", access_token);
      }

      apiClient.setAuthToken(access_token);
      return true;
    } catch (err) {
      // Refresh failed, clear tokens
      logout();
      return false;
    }
  };

  const setupMFA = async (): Promise<{ secret: string; otpauthUrl: string }> => {
    try {
      setError(null);
      const response = await apiClient.post<{ secret: string; qr_code: string; otpauthUrl?: string }>(
        "/2fa/setup",
        {}
      );
      return {
        secret: response.secret,
        otpauthUrl: response.otpauthUrl || response.qr_code || "",
      };
    } catch (err) {
      interface ApiError extends Error {
        response?: {
          data?: {
            detail?: string;
          };
        };
      }
      const apiError = err as ApiError;
      const errorMessage = apiError.response?.data?.detail || apiError.message || "Failed to set up 2FA. Please try again.";
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  const verifyMFA = async (token: string): Promise<boolean> => {
    try {
      setError(null);
      await apiClient.post("/2fa/verify", { token });
      return true;
    } catch (err) {
      interface ApiError extends Error {
        response?: {
          data?: {
            detail?: string;
          };
        };
      }
      const apiError = err as ApiError;
      const errorMessage = apiError.response?.data?.detail || apiError.message || "Invalid 2FA token. Please try again.";
      setError(errorMessage);
      return false;
    }
  };

  return (
    <AuthContext.Provider value={{
        user,
        isLoading,
        error,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        forgotPassword,
        resetPassword,
        refreshToken,
        setupMFA,
        verifyMFA,
      }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
