/**
 * Enhanced API Client with Backend Integration
 * Provides integration with all new backend features
 */

import { apiRequest } from "./queryClient";

// Re-export all existing APIs
export * from "./api";

// Enhanced API client with backend feature support
export class EnhancedApiClient {
  private baseUrl: string;
  private apiVersion: string = "v2";

  constructor(baseUrl: string = "http://localhost:8000") {
    this.baseUrl = baseUrl;
  }

  /**
   * Set API version for requests
   */
  setApiVersion(version: string) {
    this.apiVersion = version;
  }

  /**
   * Get current API version
   */
  getApiVersion(): string {
    return this.apiVersion;
  }

  /**
   * Make request with enhanced headers
   */
  async request<T>(
    endpoint: string,
    options: {
      method?: string;
      body?: string | object;
      headers?: Record<string, string>;
      signal?: AbortSignal;
      version?: string;
    } = {}
  ): Promise<T> {
    const headers: Record<string, string> = {
      ...options.headers,
      "X-API-Version": options.version || this.apiVersion,
    };

    // Add request ID if available
    if (typeof window !== "undefined") {
      const requestId = sessionStorage.getItem("last_request_id");
      if (requestId) {
        headers["X-Request-ID"] = requestId;
      }
    }

    return apiRequest<T>(endpoint, {
      ...options,
      headers,
    });
  }
}

// Global enhanced API client instance
export const enhancedApiClient = new EnhancedApiClient();

// Helper to check if feature is enabled
export async function isFeatureEnabled(featureName: string): Promise<boolean> {
  try {
    const flag = await apiRequest<{
      name: string;
      enabled: boolean;
      status: string;
    }>(`/api/feature-flags/${featureName}`, { method: "GET" });
    return flag.enabled;
  } catch {
    return false;
  }
}

// Helper to get request ID from response
export function getRequestId(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem("last_request_id");
}

// Helper to get trace ID
export function getTraceId(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem("trace_id");
}

// Helper to get rate limit info
export function getRateLimitInfo(): {
  remaining: number | null;
  reset: number | null;
} {
  if (typeof window === "undefined") {
    return { remaining: null, reset: null };
  }

  const remaining = sessionStorage.getItem("rate_limit_remaining");
  const reset = sessionStorage.getItem("rate_limit_reset");

  return {
    remaining: remaining ? parseInt(remaining, 10) : null,
    reset: reset ? parseInt(reset, 10) : null,
  };
}

