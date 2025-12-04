import { QueryClient, QueryFunction } from "@tanstack/react-query";
import logger from "./logger";

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

export async function apiRequest<T = unknown>(
  url: string,
  options?: {
    method?: string;
    body?: string | object;
    headers?: Record<string, string>;
  },
): Promise<T> {
  const windowWithGlobals = typeof window !== 'undefined' ? window as WindowWithGlobals : null;
  const baseUrl = windowWithGlobals?.VITE_API_URL || "http://localhost:8000";
  const fullUrl = url.startsWith('http') ? url : `${baseUrl}${url}`;
  const method = options?.method || 'GET';
  const body = options?.body;
  const customHeaders = options?.headers || {};

  logger.debug(`API Request: ${method} ${fullUrl}`, body);

  // Attach Authorization header if token exists (check both localStorage and sessionStorage)
  const headers: Record<string, string> = {
    ...customHeaders,
  };
  let token: string | null = null;
  if (typeof window !== 'undefined') {
    // Check localStorage first, then sessionStorage
    token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
  }
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (body) headers['Content-Type'] = 'application/json';

  const res = await fetch(fullUrl, {
    method,
    headers,
    body: body ? (typeof body === 'string' ? body : JSON.stringify(body)) : undefined,
    credentials: "include",
  });

  logger.debug(`API Response: ${method} ${fullUrl} - Status: ${res.status}`, { contentType: res.headers.get('content-type') });

  // Centralized 401 handling and error log without consuming original body
  if (!res.ok) {
    const errorText = await res.clone().text();
    logger.error(`API Error: ${method} ${fullUrl} - ${res.status}`, { errorText });

    if (res.status === 401) {
      try {
        const obj = JSON.parse(errorText);
        const detail = (obj && (obj.detail || obj.message)) || String(errorText);
        if (/token/i.test(detail) || /unauthorized/i.test(detail) || /expired/i.test(detail)) {
          // Clear invalid token and notify app
          localStorage.removeItem('auth_token');
          localStorage.removeItem('auth_user');
          sessionStorage.removeItem('auth_token');
          sessionStorage.removeItem('auth_user');
          window.dispatchEvent(new CustomEvent('auth:expired'));
        }
      } catch {
        // If JSON parse fails, still clear tokens on 401
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        sessionStorage.removeItem('auth_token');
        sessionStorage.removeItem('auth_user');
        window.dispatchEvent(new CustomEvent('auth:expired'));
      }
    }
  }

  await throwIfResNotOk(res);
  return await res.json();
}

type UnauthorizedBehavior = "returnNull" | "throw";
export const getQueryFn: <T>(options: {
  on401: UnauthorizedBehavior;
}) => QueryFunction<T> =
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

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      queryFn: getQueryFn({ on401: "throw" }),
      refetchInterval: false,
      refetchOnWindowFocus: false,
      staleTime: 30000, // 30 seconds - better balance between freshness and performance
      gcTime: 5 * 60 * 1000, // 5 minutes (formerly cacheTime)
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors (client errors)
        if (error instanceof Error && error.message.includes('4')) {
          return false;
        }
        // Retry up to 2 times for network errors
        return failureCount < 2;
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff
    },
    mutations: {
      retry: false, // Mutations shouldn't retry automatically
    },
  },
});
