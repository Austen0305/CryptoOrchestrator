import { QueryClient, QueryFunction } from "@tanstack/react-query";

async function throwIfResNotOk(res: Response) {
  if (!res.ok) {
    // Clone so callers can still read the body later
    const text = (await res.clone().text()) || res.statusText;
    throw new Error(`${res.status}: ${text}`);
  }
}

export async function apiRequest(
  method: string,
  url: string,
  data?: unknown | undefined,
): Promise<Response> {
  const baseUrl = (globalThis as any).VITE_API_URL || "http://localhost:8000";
  const fullUrl = url.startsWith('http') ? url : `${baseUrl}${url}`;

  console.log(`[API Request] ${method} ${fullUrl}`, data);

  // Attach Authorization header if token exists (proper fix: use login flow)
  const headers: Record<string, string> = {};
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (data) headers['Content-Type'] = 'application/json';

  const res = await fetch(fullUrl, {
    method,
    headers,
    body: data ? JSON.stringify(data) : undefined,
    credentials: "include",
  });

  console.log(`[API Response] ${method} ${fullUrl} - Status: ${res.status}`, res.headers.get('content-type'));

  // Centralized 401 handling and error log without consuming original body
  if (!res.ok) {
    const errorText = await res.clone().text();
    console.error(`[API Error] ${method} ${fullUrl} - ${res.status}: ${errorText}`);

    if (res.status === 401) {
      try {
        const obj = JSON.parse(errorText);
        const detail = (obj && (obj.detail || obj.message)) || String(errorText);
        if (/token/i.test(detail)) {
          // Clear invalid token and notify app
          localStorage.removeItem('auth_token');
          localStorage.removeItem('auth_user');
          window.dispatchEvent(new CustomEvent('auth:expired'));
        }
      } catch {
        // ignore JSON parse failure
      }
    }
  }

  await throwIfResNotOk(res);
  return res;
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
      staleTime: Infinity,
      retry: false,
    },
    mutations: {
      retry: false,
    },
  },
});
