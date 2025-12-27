/**
 * API response types and error handling
 * Provides type-safe API response structures
 */

/**
 * Standard API error response
 */
export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
  status_code?: number;
}

/**
 * Paginated API response
 */
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore?: boolean;
}

/**
 * Standard API success response wrapper
 */
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

/**
 * Generic error details for API responses
 */
export interface ErrorDetails {
  field?: string;
  message: string;
  code?: string;
}

/**
 * Validation error response
 */
export interface ValidationError {
  errors: ErrorDetails[];
  message: string;
}

/**
 * Type guard for API errors
 */
export function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    typeof (error as ApiError).message === 'string'
  );
}

/**
 * Type guard for validation errors
 */
export function isValidationError(error: unknown): error is ValidationError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'errors' in error &&
    Array.isArray((error as ValidationError).errors)
  );
}

/**
 * Generic request payload type
 * Use for API requests where the structure is dynamic
 */
export type RequestPayload = Record<string, unknown>;

/**
 * Generic bot creation payload
 */
export interface BotCreationPayload extends Record<string, unknown> {
  name: string;
  symbol?: string;
  strategy?: string;
  config?: Record<string, unknown>;
}

/**
 * Trade creation payload
 */
export interface TradeCreationPayload {
  botId?: string;
  pair: string;
  side: 'buy' | 'sell';
  type?: 'market' | 'limit' | 'stop';
  amount: number;
  price?: number;
  mode?: 'paper' | 'real';
  exchange?: string;
}

/**
 * Preferences update payload
 */
export interface PreferencesUpdatePayload extends Record<string, unknown> {
  theme?: string;
  notifications?: Record<string, boolean>;
  uiSettings?: Record<string, unknown>;
  tradingSettings?: Record<string, unknown>;
}

/**
 * Integration predict/backtest payload
 */
export interface IntegrationPayload extends Record<string, unknown> {
  botId?: string;
  symbol?: string;
  strategy?: string;
  config?: Record<string, unknown>;
}
