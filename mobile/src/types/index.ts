/**
 * Type definitions for CryptoOrchestrator Mobile
 */

export interface Portfolio {
  user_id: string;
  total_value_usd: number;
  assets: Asset[];
  performance_24h: number;
  performance_7d: number;
  performance_30d: number;
}

export interface Asset {
  symbol: string;
  name: string;
  amount: number;
  value_usd: number;
  price_usd: number;
  allocation_percent: number;
  change_24h: number;
}

export interface Trade {
  id: string;
  symbol: string;
  type: 'buy' | 'sell';
  amount: number;
  price: number;
  total: number;
  timestamp: string;
  status: 'pending' | 'completed' | 'failed';
}

export interface MarketData {
  symbol: string;
  price: number;
  volume_24h: number;
  change_24h: number;
  high_24h: number;
  low_24h: number;
  market_cap: number;
  timestamp: string;
}

export interface RebalanceAnalysis {
  current_allocation: Record<string, number>;
  target_allocation: Record<string, number>;
  trades_required: RebalanceTrade[];
  estimated_cost: number;
  expected_return: number;
  risk_score: number;
}

export interface RebalanceTrade {
  symbol: string;
  action: 'buy' | 'sell';
  amount: number;
  value_usd: number;
}

export interface ArbitrageOpportunity {
  id: string;
  symbol: string;
  buy_exchange: string;
  sell_exchange: string;
  buy_price: number;
  sell_price: number;
  profit_percent: number;
  profit_usd: number;
  volume_available: number;
  timestamp: string;
}

export interface Signal {
  id: string;
  provider: string;
  symbol: string;
  type: 'buy' | 'sell' | 'hold';
  confidence: number;
  target_price: number;
  stop_loss: number;
  timeframe: string;
  timestamp: string;
}

export interface BiometricCredentials {
  username: string;
  password: string;
  biometricEnabled: boolean;
}

export interface ChartDataPoint {
  timestamp: number;
  value: number;
}
