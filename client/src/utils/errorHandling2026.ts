/**
 * Comprehensive Error Handling Utilities (2026 Best Practices)
 * Provides robust error handling for React 19 + TypeScript 5.9
 */

import logger from "@/lib/logger";

export interface ErrorInfo {
  message: string;
  code?: string;
  statusCode?: number;
  details?: Record<string, unknown>;
  retryable?: boolean;
  timestamp: string;
}

export class AppError extends Error {
  constructor(
    message: string,
    public code?: string,
    public statusCode?: number,
    public details?: Record<string, unknown>,
    public retryable: boolean = false
  ) {
    super(message);
    this.name = "AppError";
    Object.setPrototypeOf(this, AppError.prototype);
  }

  toJSON(): ErrorInfo {
    return {
      message: this.message,
      code: this.code,
      statusCode: this.statusCode,
      details: this.details,
      retryable: this.retryable,
      timestamp: new Date().toISOString(),
    };
  }
}

/**
 * Classify error type for appropriate handling (2026 best practice)
 */
export function classifyError(error: unknown): {
  type: "user_error" | "system_error" | "network_error" | "unknown";
  retryable: boolean;
  userMessage: string;
} {
  if (error instanceof AppError) {
    return {
      type: error.statusCode && error.statusCode < 500 ? "user_error" : "system_error",
      retryable: error.retryable,
      userMessage: error.message,
    };
  }

  if (error instanceof TypeError && error.message.includes("fetch")) {
    return {
      type: "network_error",
      retryable: true,
      userMessage: "Network error. Please check your connection and try again.",
    };
  }

  if (error instanceof Error) {
    // Check for common error patterns
    if (error.message.includes("timeout") || error.message.includes("network")) {
      return {
        type: "network_error",
        retryable: true,
        userMessage: "Request timed out. Please try again.",
      };
    }

    if (error.message.includes("401") || error.message.includes("Unauthorized")) {
      return {
        type: "user_error",
        retryable: false,
        userMessage: "Your session has expired. Please log in again.",
      };
    }

    if (error.message.includes("403") || error.message.includes("Forbidden")) {
      return {
        type: "user_error",
        retryable: false,
        userMessage: "You don't have permission to perform this action.",
      };
    }

    if (error.message.includes("404") || error.message.includes("Not Found")) {
      return {
        type: "user_error",
        retryable: false,
        userMessage: "The requested resource was not found.",
      };
    }

    if (error.message.includes("429") || error.message.includes("rate limit")) {
      return {
        type: "user_error",
        retryable: true,
        userMessage: "Too many requests. Please wait a moment and try again.",
      };
    }

    if (error.message.includes("500") || error.message.includes("Internal Server Error")) {
      return {
        type: "system_error",
        retryable: true,
        userMessage: "A server error occurred. Please try again later.",
      };
    }
  }

  return {
    type: "unknown",
    retryable: false,
    userMessage: "An unexpected error occurred. Please try again.",
  };
}

/**
 * Log error with structured data (2026 best practice)
 */
export function logError(
  error: unknown,
  context?: {
    component?: string;
    action?: string;
    userId?: string | number;
    additionalData?: Record<string, unknown>;
  }
): void {
  const errorInfo = error instanceof AppError ? error.toJSON() : {
    message: error instanceof Error ? error.message : String(error),
    timestamp: new Date().toISOString(),
  };

  logger.error("Application error", {
    error: errorInfo,
    context: context || {},
    stack: error instanceof Error ? error.stack : undefined,
  });

  // Report to error tracking service (e.g., Sentry)
  if (typeof window !== "undefined" && (window as any).Sentry) {
    (window as any).Sentry.captureException(error, {
      contexts: {
        app: context || {},
      },
      tags: {
        error_type: classifyError(error).type,
      },
    });
  }
}

/**
 * Create user-friendly error message (2026 best practice)
 */
export function getUserFriendlyMessage(error: unknown): string {
  const classification = classifyError(error);
  return classification.userMessage;
}

/**
 * Check if error is retryable (2026 best practice)
 */
export function isRetryableError(error: unknown): boolean {
  return classifyError(error).retryable;
}

/**
 * Format error for display (2026 best practice)
 */
export function formatErrorForDisplay(error: unknown): {
  title: string;
  message: string;
  retryable: boolean;
  showDetails: boolean;
} {
  const classification = classifyError(error);
  const isDev = import.meta.env.DEV;

  return {
    title: classification.type === "user_error" ? "Error" : "Something went wrong",
    message: classification.userMessage,
    retryable: classification.retryable,
    showDetails: isDev && error instanceof Error,
  };
}
