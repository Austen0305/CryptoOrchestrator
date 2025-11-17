import { useState, useEffect, createContext, useContext, ReactNode } from "react";

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
  login: (email: string, password: string, rememberMe?: boolean) => Promise<boolean>;
  register: (email: string, username: string, password: string, firstName?: string, lastName?: string) => Promise<boolean>;
  logout: () => Promise<void>;
  forgotPassword: (email: string) => Promise<boolean>;
  resetPassword: (token: string, newPassword: string) => Promise<boolean>;
  refreshToken: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check for stored token and validate it
    const token = localStorage.getItem("token");
    if (token) {
      validateToken();
    } else {
      setIsLoading(false);
    }
  }, []);

  const validateToken = async () => {
    try {
      const response = await apiClient.get("/auth/me");
      setUser(response.data);
      setError(null);
    } catch (err) {
      localStorage.removeItem("token");
      localStorage.removeItem("refreshToken");
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string, rememberMe = false): Promise<boolean> => {
    try {
      setError(null);
      setIsLoading(true);
      
      const response = await apiClient.post("/auth/login", {
        email,
        password,
      });

      const { access_token, refresh_token, user: userData } = response.data;

      // Store tokens
      if (rememberMe) {
        localStorage.setItem("token", access_token);
        localStorage.setItem("refreshToken", refresh_token || "");
      } else {
        sessionStorage.setItem("token", access_token);
        sessionStorage.setItem("refreshToken", refresh_token || "");
      }

      // Set default token in apiClient
      const { apiClient } = await import("@/lib/apiClient");
      apiClient.setAuthToken(access_token);

      setUser(userData);
      setIsLoading(false);
      return true;
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail ||
        err.message ||
        "Failed to login. Please check your credentials.";
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
    try {
      setError(null);
      setIsLoading(true);

      const response = await apiClient.post("/auth/register", {
        email,
        username,
        password,
        first_name: firstName,
        last_name: lastName,
      });

      const { access_token, refresh_token, user: userData } = response.data;

      // Store tokens
      sessionStorage.setItem("token", access_token);
      sessionStorage.setItem("refreshToken", refresh_token || "");

      // Set default token in apiClient
      const { apiClient } = await import("@/lib/apiClient");
      const { apiClient } = await import("@/lib/apiClient");
      apiClient.setAuthToken(access_token);

      setUser(userData);
      setIsLoading(false);
      return true;
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail ||
        err.message ||
        "Failed to register. Please try again.";
      setError(errorMessage);
      setIsLoading(false);
      return false;
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await apiClient.post("/auth/logout");
    } catch (err) {
      // Ignore errors on logout
    } finally {
      localStorage.removeItem("token");
      localStorage.removeItem("refreshToken");
      sessionStorage.removeItem("token");
      sessionStorage.removeItem("refreshToken");
      const { apiClient } = await import("@/lib/apiClient");
      apiClient.setAuthToken(null);
      setUser(null);
    }
  };

  const forgotPassword = async (email: string): Promise<boolean> => {
    try {
      setError(null);
      await apiClient.post("/auth/forgot-password", { email });
      return true;
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail ||
        err.message ||
        "Failed to send reset email. Please try again.";
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
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail ||
        err.message ||
        "Failed to reset password. Please try again.";
      setError(errorMessage);
      return false;
    }
  };

  const refreshToken = async (): Promise<boolean> => {
    try {
      const refreshTokenValue =
        localStorage.getItem("refreshToken") ||
        sessionStorage.getItem("refreshToken");

      if (!refreshTokenValue) {
        return false;
      }

      const response = await apiClient.post("/auth/refresh", {
        refresh_token: refreshTokenValue,
      });

      const { access_token } = response.data;

      // Update stored token
      if (localStorage.getItem("refreshToken")) {
        localStorage.setItem("token", access_token);
      } else {
        sessionStorage.setItem("token", access_token);
      }

      const { apiClient } = await import("@/lib/apiClient");
      apiClient.setAuthToken(access_token);
      return true;
    } catch (err) {
      // Refresh failed, clear tokens
      logout();
      return false;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        error,
        login,
        register,
        logout,
        forgotPassword,
        resetPassword,
        refreshToken,
      }}
    >
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
