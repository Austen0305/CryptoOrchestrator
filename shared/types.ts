// Add to existing schema.ts file

export interface RateLimitInfo {
  remaining: number;
  reset: number;
}

export interface OrderParameters {
  symbol: string;
  type: 'market' | 'limit';
  side: 'buy' | 'sell';
  amount: number;
  price?: number;
}

export interface OrderResult {
  success: boolean;
  orderId: string;
  executedPrice: number;
  executedAmount: number;
  status: string;
  error?: string;
}

export interface SystemHealth {
  isHealthy: boolean;
  lastCheck: number;
  errors: string[];
  warnings: string[];
  apiQuota: RateLimitInfo;
  metrics: {
    latency: number;
    successRate: number;
    errorRate: number;
  };
}

// User Preferences types
export type Theme = "light" | "dark" | "system";

export interface UserPreferences {
  userId: string;
  theme: Theme;
  notifications: {
    trade_executed: boolean;
    bot_status_change: boolean;
    market_alert: boolean;
    system: boolean;
  };
  uiSettings: {
    compact_mode: boolean;
    auto_refresh: boolean;
    refresh_interval: number;
    default_chart_period: string;
    language: string;
  };
  tradingSettings: {
    default_order_type: string;
    confirm_orders: boolean;
    show_fees: boolean;
  };
  createdAt: number;
  updatedAt: number;
}

export interface UpdatePreferencesData {
  theme?: Theme;
  notifications?: Partial<UserPreferences['notifications']>;
  uiSettings?: Partial<UserPreferences['uiSettings']>;
  tradingSettings?: Partial<UserPreferences['tradingSettings']>;
}

// Trading Bot Types
export interface TradingBot {
  id: number;
  name: string;
  strategy: string;
  status: 'active' | 'stopped' | 'paused' | 'error';
  pair: string;
  balance: number;
  profit: number;
  trades: number;
  created_at: string;
  updated_at: string;
  config?: {
    stopLoss?: number;
    takeProfit?: number;
    maxPosition?: number;
    [key: string]: any;
  };
}