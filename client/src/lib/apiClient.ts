import logger from './logger';

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
  private   baseURL: string;
  private authToken: string | null = null;

  constructor(baseURL: string = '/api') {
    this.baseURL = baseURL;
    // Initialize from localStorage if available
    if (typeof window !== 'undefined') {
      this.authToken = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    }
  }

  setAuthToken(token: string | null): void {
    this.authToken = token;
  }

  private async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private calculateDelay(attempt: number, config: Required<RetryConfig>): number {
    const delay = Math.min(
      config.initialDelay * Math.pow(config.backoffMultiplier, attempt),
      config.maxDelay
    );
    
    // Add jitter to prevent thundering herd
    return delay + Math.random() * 1000;
  }

  async request<T>(endpoint: string, options: RequestInit = {}, retryConfig: RetryConfig = {}): Promise<T> {
    const config = { ...defaultConfig, ...retryConfig };
    const url = `${this.baseURL}${endpoint}`;
    let lastError: Error | null = null;

    // Attach Authorization if token exists
    const token = this.authToken || (typeof window !== 'undefined' ? localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token') : null);

    for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
      try {
        logger.debug(`API Request: ${options.method || 'GET'} ${url}`, { attempt });

        const response = await fetch(url, {
          ...options,
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...options.headers,
          },
          credentials: 'include',
        });

        if (!response.ok) {
          const status = response.status;
          const retryable = config.retryableStatuses.includes(status);
          // If unauthorized/forbidden, clear token and notify app; do not retry
          if (status === 401 || status === 403) {
            try {
              if (typeof window !== 'undefined') {
                localStorage.removeItem('auth_token');
                localStorage.removeItem('auth_user');
                window.dispatchEvent(new CustomEvent('auth:expired'));
              }
            } catch {}
            const text = await response.text().catch(() => response.statusText);
            throw new Error(`HTTP ${status}: ${text || 'Unauthorized'}`);
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

        const data = await response.json();
        logger.debug(`API Response: ${url}`, { data });
        return data;
      } catch (error) {
        lastError = error as Error;
        // Only retry network errors (TypeError) or explicitly marked retryable by status logic above
        const isNetworkError = error instanceof TypeError;
        if (isNetworkError && attempt < config.maxRetries) {
          const delay = this.calculateDelay(attempt, config);
            logger.warn(`Network error, retrying in ${delay}ms`, { url, error: lastError.message, attempt });
          await this.delay(delay);
          continue;
        }
        break; // Non-retryable error
      }
    }

    logger.error(`Request failed${lastError ? `: ${lastError.message}` : ''}`, { url });
    throw lastError || new Error('Unknown API error');
  }

  async get<T>(endpoint: string, config?: RetryConfig): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' }, config);
  }

  async post<T>(endpoint: string, data: any, config?: RetryConfig): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: 'POST',
        body: JSON.stringify(data),
      },
      config
    );
  }

  async put<T>(endpoint: string, data: any, config?: RetryConfig): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: 'PUT',
        body: JSON.stringify(data),
      },
      config
    );
  }

  async delete<T>(endpoint: string, config?: RetryConfig): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' }, config);
  }
}

export const api = new ApiClient();
