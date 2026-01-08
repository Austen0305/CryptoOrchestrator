import logger from "./logger";
import { classifyError, logError, getUserFriendlyMessage, isRetryableError } from "@/utils/errorHandling2026";

interface RetryConfig {
  maxRetries?: number;
  initialDelay?: number;
  maxDelay?: number;
  backoffMultiplier?: number;
  retryableStatuses?: number[];
}

const defaultConfig: Required<RetryConfig> = {
  maxRetries: 3,
  initialDelay: 1000,
  maxDelay: 30000,
  backoffMultiplier: 2,
  retryableStatuses: [408, 429, 500, 502, 503, 504],
};

class ApiClient {
  private baseURL: string;
  private authToken: string | null = null;

  constructor(baseURL?: string) {
    // Use backend URL (from env or default) if not provided
    if (!baseURL) {
      // Priority: window.__API_BASE__ (runtime override) > VITE_API_URL (build-time) > VITE_API_BASE_URL > default
      const DEFAULT_API_URL = "https://gets-wise-sheets-rick.trycloudflare.com";

      const envBaseUrl =
        (typeof window !== "undefined" && (window as Window & { __API_BASE__?: string }).__API_BASE__) ||
        import.meta.env.VITE_API_URL ||
        import.meta.env.VITE_API_BASE_URL ||
        DEFAULT_API_URL;

      // Default to main FastAPI backend on port 8000.
      const rawBaseUrl = envBaseUrl || "http://localhost:8000";
      
      // Upgrade logic: If we are on HTTPS, ensuring the API is also HTTPS (unless it's localhost)
      let finalBaseUrl = rawBaseUrl;
      const isSecure = typeof window !== "undefined" && window.location.protocol === "https:";
      if (isSecure && finalBaseUrl.startsWith("http://") && !finalBaseUrl.includes("localhost")) {
         finalBaseUrl = finalBaseUrl.replace("http://", "https://");
      }
      
      // Ensure baseURL ends with /api (backend routes are all under /api)
      const cleanedUrl = finalBaseUrl.replace(/\/+$/, "");
      this.baseURL = cleanedUrl.endsWith("/api") ? cleanedUrl : cleanedUrl + "/api";
    } else {
      let finalBaseUrl = baseURL;
      const isSecure = typeof window !== "undefined" && window.location.protocol === "https:";
      if (isSecure && finalBaseUrl.startsWith("http://") && !finalBaseUrl.includes("localhost")) {
         finalBaseUrl = finalBaseUrl.replace("http://", "https://");
      }

      // If baseURL is provided explicitly, ensure it ends with /api
      const cleanedUrl = finalBaseUrl.replace(/\/+$/, "");
      this.baseURL = cleanedUrl.endsWith("/api") ? cleanedUrl : cleanedUrl + "/api";
    }
    // Initialize from localStorage if available
    if (typeof window !== "undefined") {
      this.authToken = localStorage.getItem("auth_token") || sessionStorage.getItem("auth_token");
    }
  }

  setAuthToken(token: string | null): void {
    this.authToken = token;
  }

  private async delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  private calculateDelay(attempt: number, config: Required<RetryConfig>): number {
    const delay = Math.min(
      config.initialDelay * Math.pow(config.backoffMultiplier, attempt),
      config.maxDelay
    );

    // Add jitter to prevent thundering herd
    return delay + Math.random() * 1000;
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryConfig: RetryConfig = {}
  ): Promise<T> {
    const config = { ...defaultConfig, ...retryConfig };
    const url = `${this.baseURL}${endpoint}`;
    let lastError: Error | null = null;

    // Attach Authorization if token exists
    const token =
      this.authToken ||
      (typeof window !== "undefined"
        ? localStorage.getItem("auth_token") || sessionStorage.getItem("auth_token")
        : null);

    for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
      try {
        logger.debug(`API Request: ${options.method || "GET"} ${url}`, { attempt });

        const response = await fetch(url, {
          ...options,
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...options.headers,
          },
          credentials: "include",
        });

        if (!response.ok) {
          const status = response.status;
          const retryable = config.retryableStatuses.includes(status);
          // If unauthorized/forbidden, clear token and notify app; do not retry
          if (status === 401 || status === 403) {
            try {
              if (typeof window !== "undefined") {
                localStorage.removeItem("auth_token");
                localStorage.removeItem("auth_user");
                window.dispatchEvent(new CustomEvent("auth:expired"));
              }
            } catch (error) {
              logger.warn("Failed to parse error response", { error });
            }
            const text = await response.text().catch(() => response.statusText);
            throw new Error(`HTTP ${status}: ${text || "Unauthorized"}`);
          }

          if (retryable && attempt < config.maxRetries) {
            const delay = this.calculateDelay(attempt, config);
            logger.warn(`Request failed, retrying in ${delay}ms`, { url, status, attempt });
            await this.delay(delay);
            continue;
          }
          const text = await response.text().catch(() => response.statusText);
          throw new Error(`HTTP ${status}: ${text}`);
        }

        const data = (await response.json()) as T;
        logger.debug(`API Response: ${url}`, { data });
        return data;
      } catch (error) {
        lastError = error as Error;
        
        // Enhanced error classification (2026 best practice)
        const errorClassification = classifyError(error);
        
        // Log error with context
        logError(error, {
          component: "ApiClient",
          action: options.method || "GET",
          additionalData: { url, attempt },
        });
        
        // Retry based on error classification (2026 best practice)
        if (errorClassification.retryable && attempt < config.maxRetries) {
          const delay = this.calculateDelay(attempt, config);
          logger.warn(`Error occurred, retrying in ${delay}ms`, {
            url,
            error: lastError.message,
            attempt,
            errorType: errorClassification.type,
            userMessage: getUserFriendlyMessage(error),
          });
          await this.delay(delay);
          continue;
        }
        break; // Non-retryable error
      }
    }

    // Final error logging with user-friendly message (2026 best practice)
    const userMessage = lastError ? getUserFriendlyMessage(lastError) : "Unknown API error";
    logger.error(`Request failed: ${userMessage}`, { 
      url,
      error: lastError?.message,
      errorType: lastError ? classifyError(lastError).type : "unknown",
    });
    throw lastError || new Error(userMessage);
  }

  async get<T>(endpoint: string, config?: RetryConfig): Promise<T> {
    return this.request<T>(endpoint, { method: "GET" }, config);
  }

  async post<T>(endpoint: string, data: unknown, config?: RetryConfig): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      config
    );
  }

  async put<T>(endpoint: string, data: unknown, config?: RetryConfig): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: "PUT",
        body: JSON.stringify(data),
      },
      config
    );
  }

  async delete<T>(endpoint: string, config?: RetryConfig): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE" }, config);
  }
}

export const api = new ApiClient();
