/**
 * Shared API Response Types
 * Common interfaces used across the application for API responses
 */

// Base API Response
export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Market Data Types
export interface MarketData {
  symbol: string;
  price: number;
  volume: number;
  change24h: number;
  high24h: number;
  low24h: number;
  marketCap?: number;
  timestamp: string;
}

export interface OHLCV {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// Indicator Types
export interface Indicator {
  name: string;
  value: number | string;
  signal?: 'buy' | 'sell' | 'neutral';
  timestamp?: string;
}

export interface TechnicalIndicators {
  rsi?: Indicator;
  macd?: Indicator;
  ema?: Indicator;
  sma?: Indicator;
  bollinger_bands?: Indicator;
  [key: string]: Indicator | undefined;
}

// Trading Bot Types
export interface Bot {
  id: string;
  name: string;
  strategy: string;
  status: 'active' | 'inactive' | 'paused';
  profitLoss: number;
  trades: number;
  createdAt: string;
  updatedAt: string;
}

// Trade Types
export interface Trade {
  id: string;
  botId?: string;
  symbol: string;
  side: 'buy' | 'sell';
  amount: number;
  price: number;
  total: number;
  status: 'pending' | 'completed' | 'failed' | 'cancelled';
  timestamp: string;
}

// Stats Types
export interface Stats {
  total: number;
  active?: number;
  inactive?: number;
  pending?: number;
  completed?: number;
  failed?: number;
  [key: string]: number | undefined;
}

export interface ArbitrageStats {
  opportunities: number;
  profit: number;
  volume: number;
  successRate: number;
  timestamp: string;
}

// Pagination
export interface PaginatedResponse<T> extends APIResponse<T> {
  page: number;
  perPage: number;
  total: number;
  totalPages: number;
}

// Error Response
export interface APIError {
  code: string;
  message: string;
  details?: any;
}

// Market Analysis Types
export interface MarketAnalysisData {
  historical_data?: OHLCV[];
  recommendation?: 'buy' | 'sell' | 'hold';
  confidence?: number;
  current_price?: number;
  signals?: {
    bullish: number;
    bearish: number;
    neutral: number;
  };
  summary?: string;
  indicators?: {
    rsi?: number;
    macd?: number;
    ema?: number;
    sma?: number;
    bollinger_upper?: number;
    bollinger_middle?: number;
    bollinger_lower?: number;
    stochastic_k?: number;
    stochastic_d?: number;
    [key: string]: number | undefined;
  };
}

// User Profile Types
export interface UserProfile {
  id: string;
  username: string;
  email: string;
  totalBalance?: number;
  mfaEnabled?: boolean;
  createdAt: string;
  updatedAt: string;
}

// Portfolio Types
export interface Portfolio {
  totalBalance?: number;
  available?: number;
  locked?: number;
  positions?: any[];
  [key: string]: any;
}
