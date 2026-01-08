import { QueryClient, QueryFunction, QueryCache, MutationCache } from "@tanstack/react-query";
import logger from "./logger";
import { deduplicateRequest } from "@/utils/performance";
import { handleApiError, showErrorToast } from "@/utils/error-handling";

async function throwIfResNotOk(res: Response) {
  if (!res.ok) {
    // Clone so callers can still read the body later
    const text = (await res.clone().text()) || res.statusText;
    throw new Error(`${res.status}: ${text}`);
  }
}

interface WindowWithGlobals extends Window {
  VITE_API_URL?: string;
}

// Extended Error type with API metadata
interface ApiError extends Error {
  code?: string;
  status?: number;
  response?: unknown;
  url?: string;
  isNetworkError?: boolean;
  originalError?: unknown;
}

/**
 * Get API base URL from environment variables (Vite) or window, with fallback
 * Ensures base URL doesn't end with /api since endpoints already include /api
 */
function getApiBaseUrl(): string {
  let baseUrl: string = "";
  
  // Priority 1: Vite environment variable (available at build time)
  if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_URL) {
    baseUrl = import.meta.env.VITE_API_URL;
  }
  
  // Priority 2: Window global (runtime override)
  if (!baseUrl && typeof window !== "undefined") {
    const windowWithGlobals = window as WindowWithGlobals;
    if (windowWithGlobals.VITE_API_URL) {
      baseUrl = windowWithGlobals.VITE_API_URL;
    }
  }
  
  // Fallback: localhost for development
  if (!baseUrl) {
    baseUrl = "http://localhost:8000";
  }
  
  // Remove trailing /api if present, since endpoints already include /api
  if (baseUrl.endsWith('/api')) {
    baseUrl = baseUrl.slice(0, -4);
  }
  
  // Ensure no trailing slash
  if (baseUrl.endsWith('/')) {
    baseUrl = baseUrl.slice(0, -1);
  }
  
  return baseUrl;
}

/**
 * Enhanced API request function with improved error handling
 * Note: Retry logic is handled by React Query, not here
 */
export async function apiRequest<T = unknown>(
  url: string,
  options?: {
    method?: string;
    body?: string | object;
    headers?: Record<string, string>;
    signal?: AbortSignal;
    deduplicate?: boolean; // Enable request deduplication for GET requests
  }
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const fullUrl = url.startsWith("http") ? url : `${baseUrl}${url}`;
  const method = options?.method || "GET";
  const body = options?.body;
  const customHeaders = options?.headers || {};
  const shouldDeduplicate = options?.deduplicate !== false && method === "GET";

  logger.debug(`API Request: ${method} ${fullUrl}`, body);

  // Request deduplication for GET requests
  if (shouldDeduplicate) {
    const requestKey = `${method}:${fullUrl}`;
    return deduplicateRequest(requestKey, () =>
      executeRequest<T>(fullUrl, method, body, customHeaders, options?.signal)
    );
  }

  return executeRequest<T>(fullUrl, method, body, customHeaders, options?.signal);
}

async function executeRequest<T>(
  fullUrl: string,
  method: string,
  body: string | object | undefined,
  customHeaders: Record<string, string>,
  signal?: AbortSignal
): Promise<T> {
  // Attach Authorization header if token exists (check both localStorage and sessionStorage)
  const headers: Record<string, string> = {
    ...customHeaders,
  };
  let token: string | null = null;
  if (typeof window !== "undefined") {
    // Check localStorage first, then sessionStorage
    token = localStorage.getItem("auth_token") || sessionStorage.getItem("auth_token");
  }
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (body) headers["Content-Type"] = "application/json";
  
  // Add API version header (v2 for enhanced features)
  headers["X-API-Version"] = "v2";
  
  // Add request ID for correlation (if available from previous response)
  const lastRequestId = sessionStorage.getItem("last_request_id");
  if (lastRequestId) {
    headers["X-Request-ID"] = lastRequestId;
  }

  try {
    const res = await fetch(fullUrl, {
      method,
      headers,
      body: body ? (typeof body === "string" ? body : JSON.stringify(body)) : undefined,
      credentials: "include",
      signal, // Support for request cancellation
    });

    logger.debug(`API Response: ${method} ${fullUrl} - Status: ${res.status}`, {
      contentType: res.headers.get("content-type"),
    });

    // Handle non-OK responses
    if (!res.ok) {
      const errorText = await res.clone().text();
      logger.error(`API Error: ${method} ${fullUrl} - ${res.status}`, { errorText });

      // Handle authentication errors
      if (res.status === 401 || res.status === 403) {
        try {
          const obj: { detail?: string; message?: string } = JSON.parse(errorText);
          const detail: string = (obj && (obj.detail || obj.message)) || String(errorText);
          if (/token/i.test(detail) || /unauthorized/i.test(detail) || /expired/i.test(detail)) {
            // Clear invalid token and notify app
            if (typeof window !== "undefined") {
              localStorage.removeItem("auth_token");
              localStorage.removeItem("auth_user");
              localStorage.removeItem("refresh_token");
              sessionStorage.removeItem("auth_token");
              sessionStorage.removeItem("auth_user");
              sessionStorage.removeItem("refresh_token");
              window.dispatchEvent(new CustomEvent("auth:expired"));
            }
          }
        } catch {
          // If JSON parse fails, still clear tokens on 401/403
          if (typeof window !== "undefined") {
            localStorage.removeItem("auth_token");
            localStorage.removeItem("auth_user");
            localStorage.removeItem("refresh_token");
            sessionStorage.removeItem("auth_token");
            sessionStorage.removeItem("auth_user");
            sessionStorage.removeItem("refresh_token");
            window.dispatchEvent(new CustomEvent("auth:expired"));
          }
        }
      }

      // Parse error response for user-friendly messages
      let errorMessage = `${res.status}: ${res.statusText}`;
      let errorCode: string | undefined;
      let errorResponse: unknown;

      try {
        const errorObj: {
          error?: { code?: string; message?: string };
          code?: string;
          message?: string;
          detail?: string;
        } = JSON.parse(errorText);
        errorCode = errorObj?.error?.code || errorObj?.code;
        errorMessage =
          errorObj?.error?.message || errorObj?.message || errorObj?.detail || errorMessage;
        errorResponse = errorObj;
      } catch {
        // If parsing fails, use status text
        errorMessage = errorText || errorMessage;
      }

      // Create enhanced error with metadata
      const error = new Error(errorMessage) as ApiError;
      error.code = errorCode;
      error.status = res.status;
      error.response = errorResponse;
      error.url = fullUrl;

      throw error;
    }

    // Store request ID for correlation
    const requestId = res.headers.get("X-Request-ID");
    if (requestId && typeof window !== "undefined") {
      sessionStorage.setItem("last_request_id", requestId);
    }
    
    // Store trace ID for distributed tracing
    const traceId = res.headers.get("X-Trace-ID");
    if (traceId && typeof window !== "undefined") {
      sessionStorage.setItem("trace_id", traceId);
    }
    
    // Handle rate limiting headers
    const rateLimitRemaining = res.headers.get("X-RateLimit-Remaining");
    const rateLimitLimit = res.headers.get("X-RateLimit-Limit");
    const rateLimitReset = res.headers.get("X-RateLimit-Reset");
    if (rateLimitRemaining !== null && typeof window !== "undefined") {
      // Store rate limit info for UI display
      sessionStorage.setItem("rate_limit_remaining", rateLimitRemaining);
      if (rateLimitLimit) {
        sessionStorage.setItem("rate_limit_limit", rateLimitLimit);
      }
      if (rateLimitReset) {
        sessionStorage.setItem("rate_limit_reset", rateLimitReset);
      }
    }
    
    // Store span ID for correlation
    const spanId = res.headers.get("X-Span-ID");
    if (spanId && typeof window !== "undefined") {
      sessionStorage.setItem("span_id", spanId);
    }

    // Handle successful responses
    const contentType = res.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      const data = await res.json();
      
      // Handle v2 API response format (with meta field)
      if (data && typeof data === "object" && "data" in data && "meta" in data) {
        // Extract data from v2 format
        return data.data as T;
      }
      
      // Handle v1 format (direct data or wrapped)
      if (data && typeof data === "object" && "data" in data) {
        return data.data as T;
      }
      
      // Direct response
      return data as T;
    } else if (contentType && contentType.includes("text/")) {
      return (await res.text()) as T;
    } else {
      // For other content types, return response as-is
      return res as unknown as T;
    }
  } catch (error) {
    // Handle network errors and other fetch failures
    if (error instanceof TypeError && error.message.includes("fetch")) {
      const networkError = new Error("Network error: Unable to connect to server") as ApiError;
      networkError.code = "NETWORK_ERROR";
      networkError.isNetworkError = true;
      networkError.url = fullUrl;
      logger.error("Network error", { url: fullUrl, error: error.message });
      throw networkError;
    }

    // Re-throw if already an Error with metadata
    if (error instanceof Error && (error as ApiError).status !== undefined) {
      throw error;
    }

    // Wrap unknown errors
    const wrappedError = new Error(
      error instanceof Error ? error.message : "Unknown API error"
    ) as ApiError;
    wrappedError.originalError = error;
    wrappedError.url = fullUrl;
    throw wrappedError;
  }
}

type UnauthorizedBehavior = "returnNull" | "throw";
export const getQueryFn: <T>(options: { on401: UnauthorizedBehavior }) => QueryFunction<T> =
  ({ on401: unauthorizedBehavior }) =>
  async ({ queryKey }) => {
    const res = await fetch(queryKey.join("/") as string, {
      credentials: "include",
    });

    if (unauthorizedBehavior === "returnNull" && res.status === 401) {
      return null;
    }

    await throwIfResNotOk(res);
    return await res.json();
  };

// Global error handling for queries
const queryCache = new QueryCache({
  onError: (error) => {
    const appError = handleApiError(error, 'Query');
    // Only show toast for non-401 errors (auth errors handled separately)
    if (appError.statusCode !== 401 && appError.statusCode !== 403) {
      showErrorToast(error, 'Query');
    }
  },
});

// Global error handling for mutations
const mutationCache = new MutationCache({
  onError: (error) => {
    const appError = handleApiError(error, 'Mutation');
    // Only show toast for non-401 errors
    if (appError.statusCode !== 401 && appError.statusCode !== 403) {
      showErrorToast(error, 'Mutation');
    }
  },
});

export const queryClient = new QueryClient({
  queryCache,
  mutationCache,
  defaultOptions: {
    queries: {
      queryFn: getQueryFn({ on401: "throw" }),
      refetchInterval: false,
      refetchOnWindowFocus: false,
      staleTime: 30000, // 30 seconds - better balance between freshness and performance
      gcTime: 5 * 60 * 1000, // 5 minutes (formerly cacheTime)
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors (client errors) except 408, 429
        if (error instanceof Error) {
          const apiError = error as ApiError;
          if (apiError.status !== undefined) {
            // Retry on timeout and rate limit errors
            if (apiError.status === 408 || apiError.status === 429) {
              return failureCount < 3;
            }
            // Don't retry other 4xx errors (client errors)
            if (apiError.status >= 400 && apiError.status < 500) {
              return false;
            }
          }
          // Check for network errors
          if (apiError.isNetworkError || error.message.includes("Network error")) {
            return failureCount < 2;
          }
        }
        // Retry up to 2 times for 5xx errors (server errors)
        return failureCount < 2;
      },
      retryDelay: (attemptIndex) => {
        // Exponential backoff with jitter: min(1000 * 2^attempt, 30000) + random(0-1000)
        const baseDelay = Math.min(1000 * Math.pow(2, attemptIndex), 30000);
        return baseDelay + Math.random() * 1000;
      },
    },
    mutations: {
      retry: false, // Mutations shouldn't retry automatically (let user trigger retry)
    },
  },
});
