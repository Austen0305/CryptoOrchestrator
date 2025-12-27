/**
 * Error Message Mapping
 * Maps error codes and messages to user-friendly messages with recovery actions
 */

export interface ErrorCategory {
  category: "user_error" | "system_error" | "security_error" | "network_error";
  userMessage: string;
  recoveryAction?: string;
  supportContact?: boolean;
}

export interface ErrorMapping {
  [key: string]: ErrorCategory;
}

/**
 * Error code to user-friendly message mapping
 */
const ERROR_MAPPINGS: ErrorMapping = {
  // Authentication & Authorization
  AUTHENTICATION_ERROR: {
    category: "security_error",
    userMessage: "Your session has expired. Please log in again.",
    recoveryAction: "Click 'Log In' to refresh your session.",
  },
  AUTHORIZATION_ERROR: {
    category: "security_error",
    userMessage: "You don't have permission to perform this action.",
    recoveryAction: "Contact support if you believe this is an error.",
    supportContact: true,
  },
  INVALID_TOKEN: {
    category: "security_error",
    userMessage: "Your authentication token is invalid. Please log in again.",
    recoveryAction: "Click 'Log In' to get a new token.",
  },
  
  // Validation Errors
  VALIDATION_ERROR: {
    category: "user_error",
    userMessage: "Please check your input and try again.",
    recoveryAction: "Review the highlighted fields and correct any errors.",
  },
  INVALID_ADDRESS: {
    category: "user_error",
    userMessage: "The address format is invalid. Please check and try again.",
    recoveryAction: "Ensure the address is a valid Ethereum address (0x...).",
  },
  INSUFFICIENT_BALANCE: {
    category: "user_error",
    userMessage: "You don't have enough balance to complete this transaction.",
    recoveryAction: "Deposit more funds or reduce the transaction amount.",
  },
  INVALID_AMOUNT: {
    category: "user_error",
    userMessage: "The amount entered is invalid.",
    recoveryAction: "Enter a positive number greater than the minimum amount.",
  },
  
  // Trading Errors
  TRADING_ERROR: {
    category: "system_error",
    userMessage: "A trading error occurred. Your funds are safe.",
    recoveryAction: "Please try again in a few moments.",
    supportContact: true,
  },
  INSUFFICIENT_BALANCE_ERROR: {
    category: "user_error",
    userMessage: "Insufficient balance for this trade.",
    recoveryAction: "Check your wallet balance and try again.",
  },
  INVALID_SYMBOL_ERROR: {
    category: "user_error",
    userMessage: "The trading pair is invalid or not supported.",
    recoveryAction: "Select a different trading pair.",
  },
  ORDER_EXECUTION_FAILED: {
    category: "system_error",
    userMessage: "Failed to execute your order. No funds were deducted.",
    recoveryAction: "Please try again. If the problem persists, contact support.",
    supportContact: true,
  },
  EXCHANGE_CONNECTION_ERROR: {
    category: "network_error",
    userMessage: "Unable to connect to blockchain trading service.",
    recoveryAction: "Check your internet connection and blockchain RPC status. Try again in a few moments.",
  },
  SLIPPAGE_EXCEEDED: {
    category: "user_error",
    userMessage: "The price moved too much. Your trade was not executed.",
    recoveryAction: "Try again with a higher slippage tolerance or wait for better market conditions.",
  },
  INSUFFICIENT_LIQUIDITY: {
    category: "user_error",
    userMessage: "Not enough liquidity available for this trade.",
    recoveryAction: "Try a smaller amount or a different trading pair.",
  },
  
  // Wallet Errors
  WALLET_NOT_FOUND: {
    category: "user_error",
    userMessage: "Wallet not found.",
    recoveryAction: "Create a new wallet or check your wallet ID.",
  },
  WITHDRAWAL_FAILED: {
    category: "system_error",
    userMessage: "Withdrawal failed. Your funds remain in your wallet.",
    recoveryAction: "Check the transaction details and try again. Contact support if needed.",
    supportContact: true,
  },
  INVALID_WALLET_ADDRESS: {
    category: "user_error",
    userMessage: "The wallet address is invalid.",
    recoveryAction: "Enter a valid Ethereum address (0x...).",
  },
  
  // DEX Trading Errors
  DEX_QUOTE_ERROR: {
    category: "system_error",
    userMessage: "Unable to get a quote for this trade.",
    recoveryAction: "Try again in a few moments or select a different trading pair.",
  },
  DEX_SWAP_ERROR: {
    category: "system_error",
    userMessage: "The swap failed. No funds were deducted.",
    recoveryAction: "Try again or contact support if the problem persists.",
    supportContact: true,
  },
  TRANSACTION_NOT_FOUND: {
    category: "user_error",
    userMessage: "Transaction not found.",
    recoveryAction: "Check the transaction hash and try again.",
  },
  
  // Network Errors
  NETWORK_ERROR: {
    category: "network_error",
    userMessage: "Network connection error. Please check your internet.",
    recoveryAction: "Check your internet connection and try again.",
  },
  TIMEOUT_ERROR: {
    category: "network_error",
    userMessage: "Request timed out. The server may be busy.",
    recoveryAction: "Wait a moment and try again.",
  },
  
  // Rate Limiting
  RATE_LIMIT_EXCEEDED: {
    category: "user_error",
    userMessage: "Too many requests. Please wait a moment.",
    recoveryAction: "Wait a few seconds before trying again.",
  },
  
  // Database Errors
  DATABASE_ERROR: {
    category: "system_error",
    userMessage: "A database error occurred. Please try again later.",
    recoveryAction: "Try again in a few moments. Contact support if the problem persists.",
    supportContact: true,
  },
  INTEGRITY_ERROR: {
    category: "user_error",
    userMessage: "This resource already exists or conflicts with existing data.",
    recoveryAction: "Check if the resource already exists or use different values.",
  },
  
  // Generic Errors
  NOT_FOUND: {
    category: "user_error",
    userMessage: "The requested resource was not found.",
    recoveryAction: "Check the URL or resource ID and try again.",
  },
  INTERNAL_ERROR: {
    category: "system_error",
    userMessage: "An unexpected error occurred. We're working on it.",
    recoveryAction: "Please try again later. Contact support if the problem persists.",
    supportContact: true,
  },
  HTTP_ERROR: {
    category: "system_error",
    userMessage: "A server error occurred.",
    recoveryAction: "Try again in a few moments.",
  },
};

/**
 * Extract error code from error message or response
 */
function extractErrorCode(error: Error | string | unknown): string | null {
  if (typeof error === "string") {
    // Try to extract error code from string
    const match = error.match(/([A-Z_]+_ERROR|ERROR_[A-Z_]+)/);
    if (match && match[1]) return match[1];
    
    // Check for common patterns
    if (error.includes("401") || error.includes("unauthorized")) return "AUTHENTICATION_ERROR";
    if (error.includes("403") || error.includes("forbidden")) return "AUTHORIZATION_ERROR";
    if (error.includes("404") || error.includes("not found")) return "NOT_FOUND";
    if (error.includes("429") || error.includes("rate limit")) return "RATE_LIMIT_EXCEEDED";
    if (error.includes("500") || error.includes("internal")) return "INTERNAL_ERROR";
    if (error.includes("network") || error.includes("fetch")) return "NETWORK_ERROR";
    if (error.includes("timeout")) return "TIMEOUT_ERROR";
    if (error.includes("validation") || error.includes("invalid")) return "VALIDATION_ERROR";
    if (error.includes("insufficient balance")) return "INSUFFICIENT_BALANCE";
    if (error.includes("slippage")) return "SLIPPAGE_EXCEEDED";
    if (error.includes("liquidity")) return "INSUFFICIENT_LIQUIDITY";
    
    return null;
  }
  
  if (error instanceof Error) {
    // Check error message
    return extractErrorCode(error.message);
  }
  
  // Check if it's an error object with code
  if (typeof error === "object" && error !== null) {
    const err = error as { code?: string; error?: { code?: string }; message?: string };
    if (err.code) return err.code;
    if (err.error?.code) return err.error.code;
    if (err.message) return extractErrorCode(err.message);
  }
  
  return null;
}

/**
 * Get user-friendly error message from error
 */
export function getUserFriendlyError(error: Error | string | unknown): ErrorCategory {
  const errorCode = extractErrorCode(error);
  
  if (errorCode && ERROR_MAPPINGS[errorCode]) {
    return ERROR_MAPPINGS[errorCode];
  }
  
  // Default fallback
  return {
    category: "system_error",
    userMessage: typeof error === "string" 
      ? error 
      : error instanceof Error 
        ? error.message 
        : "An unexpected error occurred. Please try again.",
    recoveryAction: "Please try again. If the problem persists, contact support.",
    supportContact: true,
  };
}

/**
 * Get error icon based on category
 */
export function getErrorIcon(category: ErrorCategory["category"]): string {
  switch (category) {
    case "security_error":
      return "🔒";
    case "user_error":
      return "⚠️";
    case "network_error":
      return "🌐";
    case "system_error":
      return "🔧";
    default:
      return "❌";
  }
}

/**
 * Format error for display
 */
export function formatError(error: Error | string | unknown): {
  message: string;
  category: ErrorCategory["category"];
  recoveryAction?: string;
  supportContact?: boolean;
  icon: string;
} {
  const errorInfo = getUserFriendlyError(error);
  
  return {
    message: errorInfo.userMessage,
    category: errorInfo.category,
    recoveryAction: errorInfo.recoveryAction,
    supportContact: errorInfo.supportContact,
    icon: getErrorIcon(errorInfo.category),
  };
}
