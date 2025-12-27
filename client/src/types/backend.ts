/**
 * Backend Integration Types
 * TypeScript types that match backend Pydantic models
 */

// Re-export API types
export * from "./api";

// Backend response format (v2)
export interface BackendResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  meta?: {
    timestamp: string;
    version: string;
    request_id?: string;
  };
}

// Backend error response
export interface BackendError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    validation_errors?: Array<{
      field: string;
      message: string;
    }>;
  };
  meta?: {
    timestamp: string;
    version: string;
    request_id?: string;
  };
}

// Rate limit response
export interface RateLimitResponse {
  error: "Rate limit exceeded";
  message: string;
  retry_after: number;
  limit: number;
  window: number;
}

// Health check response
export interface HealthCheckResponse {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: string;
  checks: Record<
    string,
    {
      status: "healthy" | "degraded" | "unhealthy" | "unknown";
      message?: string;
      details?: Record<string, unknown>;
      timestamp: string;
    }
  >;
}

// Middleware stats response
export interface MiddlewareStatsResponse {
  performance: {
    requests: number;
    errors: number;
    avg_duration_ms: number;
    p95_duration_ms: number;
    p99_duration_ms: number;
  };
  database_pool: {
    total_connections: number;
    active_connections: number;
    idle_connections: number;
    utilization: number;
  };
  background_tasks: {
    queued: number;
    running: number;
    completed: number;
    failed: number;
  };
  websockets: {
    connected: number;
    total_messages: number;
  };
  api_analytics: {
    total_requests: number;
    total_errors: number;
    error_rate: number;
    unique_clients: number;
    unique_endpoints: number;
  };
}

