/**
 * Validation Utilities
 * Centralized validation functions and schemas
 */

import { z } from 'zod';

/**
 * Common validation schemas
 */
export const validationSchemas = {
  /**
   * Email validation
   */
  email: z.string().email('Invalid email address').min(1, 'Email is required'),

  /**
   * Password validation
   */
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number')
    .regex(/[^A-Za-z0-9]/, 'Password must contain at least one special character'),

  /**
   * Trading pair validation
   */
  tradingPair: z.string().regex(/^[A-Z0-9]+\/[A-Z0-9]+$/, 'Invalid trading pair format (e.g., BTC/USD)'),

  /**
   * Amount validation (positive number)
   */
  amount: z.number().positive('Amount must be positive').min(0.0001, 'Amount must be at least 0.0001'),

  /**
   * Price validation (positive number)
   */
  price: z.number().positive('Price must be positive').min(0.01, 'Price must be at least 0.01'),

  /**
   * Percentage validation (0-100)
   */
  percentage: z.number().min(0, 'Percentage cannot be negative').max(100, 'Percentage cannot exceed 100'),

  /**
   * Stop loss validation (0.1-50%)
   */
  stopLoss: z.number().min(0.1, 'Stop loss must be at least 0.1%').max(50, 'Stop loss cannot exceed 50%'),

  /**
   * Take profit validation (0.1-100%)
   */
  takeProfit: z.number().min(0.1, 'Take profit must be at least 0.1%').max(100, 'Take profit cannot exceed 100%'),

  /**
   * Risk per trade validation (0.1-10%)
   */
  riskPerTrade: z.number().min(0.1, 'Risk per trade must be at least 0.1%').max(10, 'Risk per trade cannot exceed 10%'),
};

/**
 * Order validation schema
 */
export const orderSchema = z.object({
  pair: validationSchemas.tradingPair,
  side: z.enum(['buy', 'sell']),
  type: z.enum(['market', 'limit', 'stop', 'stop-limit', 'take-profit', 'trailing-stop']),
  amount: validationSchemas.amount,
  price: validationSchemas.price.optional(),
  stop: validationSchemas.price.optional(),
  take_profit: validationSchemas.price.optional(),
  trailing_stop_percent: validationSchemas.percentage.optional(),
  time_in_force: z.enum(['GTC', 'IOC', 'FOK']).optional(),
}).refine((data) => {
  // Limit orders require price
  if ((data.type === 'limit' || data.type === 'stop-limit' || data.type === 'take-profit') && !data.price) {
    return false;
  }
  return true;
}, {
  message: 'Price is required for limit, stop-limit, and take-profit orders',
  path: ['price'],
}).refine((data) => {
  // Stop orders require stop price
  if ((data.type === 'stop' || data.type === 'stop-limit') && !data.stop) {
    return false;
  }
  return true;
}, {
  message: 'Stop price is required for stop and stop-limit orders',
  path: ['stop'],
}).refine((data) => {
  // Trailing stop requires percentage
  if (data.type === 'trailing-stop' && !data.trailing_stop_percent) {
    return false;
  }
  return true;
}, {
  message: 'Trailing stop percentage is required for trailing-stop orders',
  path: ['trailing_stop_percent'],
});

/**
 * Bot configuration validation schema
 */
export const botConfigSchema = z.object({
  name: z.string().min(1, 'Bot name is required').max(100, 'Bot name cannot exceed 100 characters'),
  strategy: z.string().min(1, 'Strategy is required'),
  tradingPair: validationSchemas.tradingPair,
  maxPositionSize: validationSchemas.amount,
  stopLoss: validationSchemas.stopLoss,
  takeProfit: validationSchemas.takeProfit,
  riskPerTrade: validationSchemas.riskPerTrade,
});

/**
 * Strategy configuration validation schema
 */
export const strategyConfigSchema = z.object({
  name: z.string().min(1, 'Strategy name is required').max(100, 'Strategy name cannot exceed 100 characters'),
  description: z.string().max(500, 'Description cannot exceed 500 characters').optional(),
  strategy_type: z.enum(['rsi', 'macd', 'breakout', 'lstm', 'transformer', 'custom'], {
    errorMap: () => ({ message: 'Invalid strategy type' }),
  }),
  category: z.enum(['technical', 'ml', 'hybrid'], {
    errorMap: () => ({ message: 'Invalid category' }),
  }),
  config: z.object({
    stop_loss_pct: validationSchemas.stopLoss.optional(),
    take_profit_pct: validationSchemas.takeProfit.optional(),
    position_size_pct: validationSchemas.percentage.optional(),
    timeframe: z.enum(['1m', '5m', '15m', '1h', '4h', '1d']).optional(),
    rsi_period: z.number().int().min(2).max(100).optional(),
    oversold_threshold: z.number().int().min(0).max(100).optional(),
    overbought_threshold: z.number().int().min(0).max(100).optional(),
  }).passthrough(), // Allow additional config fields
});

/**
 * Validate order data
 */
export function validateOrder(data: unknown): { valid: boolean; errors?: z.ZodError } {
  try {
    orderSchema.parse(data);
    return { valid: true };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { valid: false, errors: error };
    }
    return { valid: false, errors: new z.ZodError([]) };
  }
}

/**
 * Validate bot configuration
 */
export function validateBotConfig(data: unknown): { valid: boolean; errors?: z.ZodError } {
  try {
    botConfigSchema.parse(data);
    return { valid: true };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { valid: false, errors: error };
    }
    return { valid: false, errors: new z.ZodError([]) };
  }
}

/**
 * Validate strategy configuration
 */
export function validateStrategyConfig(data: unknown): { valid: boolean; errors?: z.ZodError } {
  try {
    strategyConfigSchema.parse(data);
    return { valid: true };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { valid: false, errors: error };
    }
    return { valid: false, errors: new z.ZodError([]) };
  }
}

/**
 * Format validation errors for display
 */
export function formatValidationErrors(errors: z.ZodError): Record<string, string> {
  const formatted: Record<string, string> = {};
  errors.errors.forEach((error) => {
    const path = error.path.join('.');
    formatted[path] = error.message;
  });
  return formatted;
}
