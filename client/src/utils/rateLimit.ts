/**
 * Rate Limiting Utilities
 * Provides utilities for handling rate limiting information
 */

/**
 * Get rate limit information from session storage
 */
export function getRateLimitInfo(): {
  remaining: number | null;
  limit: number | null;
  reset: number | null;
} {
  if (typeof window === "undefined") {
    return { remaining: null, limit: null, reset: null };
  }

  const remaining = sessionStorage.getItem("rate_limit_remaining");
  const limit = sessionStorage.getItem("rate_limit_limit");
  const reset = sessionStorage.getItem("rate_limit_reset");

  return {
    remaining: remaining ? parseInt(remaining, 10) : null,
    limit: limit ? parseInt(limit, 10) : null,
    reset: reset ? parseInt(reset, 10) : null,
  };
}

/**
 * Check if rate limit is approaching
 */
export function isRateLimitLow(threshold: number = 0.2): boolean {
  const info = getRateLimitInfo();
  if (!info.remaining || !info.limit) return false;
  return info.remaining / info.limit < threshold;
}

/**
 * Get time until rate limit reset
 */
export function getRateLimitResetTime(): number | null {
  const info = getRateLimitInfo();
  if (!info.reset) return null;
  const now = Math.floor(Date.now() / 1000);
  return Math.max(0, info.reset - now);
}

/**
 * Format rate limit info for display
 */
export function formatRateLimitInfo(): string {
  const info = getRateLimitInfo();
  if (info.remaining === null || info.limit === null) {
    return "Rate limit info unavailable";
  }

  const resetTime = getRateLimitResetTime();
  const resetText = resetTime ? ` (resets in ${resetTime}s)` : "";

  return `${info.remaining}/${info.limit} requests remaining${resetText}`;
}

