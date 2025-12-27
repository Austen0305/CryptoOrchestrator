/**
 * Request Correlation Utilities
 * Provides utilities for request ID and trace correlation
 */

/**
 * Get request ID from session storage
 */
export function getRequestId(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem("last_request_id");
}

/**
 * Get trace ID from session storage
 */
export function getTraceId(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem("trace_id");
}

/**
 * Get span ID from session storage
 */
export function getSpanId(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem("span_id");
}

/**
 * Get correlation IDs object
 */
export function getCorrelationIds(): {
  requestId: string | null;
  traceId: string | null;
  spanId: string | null;
} {
  return {
    requestId: getRequestId(),
    traceId: getTraceId(),
    spanId: getSpanId(),
  };
}

/**
 * Format correlation IDs for logging
 */
export function formatCorrelationIds(): string {
  const ids = getCorrelationIds();
  const parts: string[] = [];

  if (ids.requestId) parts.push(`Request-ID: ${ids.requestId}`);
  if (ids.traceId) parts.push(`Trace-ID: ${ids.traceId}`);
  if (ids.spanId) parts.push(`Span-ID: ${ids.spanId}`);

  return parts.join(", ");
}

