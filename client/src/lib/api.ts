import { apiRequest } from "./queryClient";
import type { BotConfig, InsertBotConfig, Trade, Portfolio, MarketData, Notification } from "../../../shared/schema";
import { normalizeTradingMode } from "./tradingUtils";
import type {
  TradeCreationPayload,
  BotCreationPayload,
  PreferencesUpdatePayload,
  IntegrationPayload,
  RequestPayload,
} from "@/types/api";
import type { UserPreferences } from '@shared/types';

// Bot API functions
export const botApi = {
  getBots: () => apiRequest<BotConfig[]>("/api/bots", { method: "GET" }),
  getBot: (id: string) =>
    apiRequest<BotConfig>(`/api/bots/${id}`, { method: "GET" }),
  createBot: (bot: InsertBotConfig) =>
    apiRequest<BotConfig>("/api/bots", { method: "POST", body: bot }),
  updateBot: (id: string, updates: Partial<BotConfig>) =>
    apiRequest<BotConfig>(`/api/bots/${id}`, { method: "PATCH", body: updates }),
  deleteBot: (id: string) =>
    apiRequest<{ success: boolean }>(`/api/bots/${id}`, { method: "DELETE" }),
  startBot: (id: string) =>
    apiRequest<BotConfig>(`/api/bots/${id}/start`, { method: "POST" }),
  stopBot: (id: string) =>
    apiRequest<BotConfig>(`/api/bots/${id}/stop`, { method: "POST" }),
  getBotModel: (id: string) =>
    apiRequest<Record<string, unknown>>(`/api/bots/${id}/model`, { method: "GET" }),
  getBotPerformance: (id: string) =>
    apiRequest<Record<string, unknown>>(`/api/bots/${id}/performance`, { method: "GET" }),
};

// Trade API functions
export const tradeApi = {
  getTrades: (botId?: string, mode?: "paper" | "real" | "live") => {
    const params = new URLSearchParams();
    if (botId) params.append("botId", botId);
    if (mode) {
      const normalizedMode = normalizeTradingMode(mode);
      params.append("mode", normalizedMode);
    }
    const query = params.toString() ? `?${params.toString()}` : "";
    return apiRequest<Trade[]>(`/api/trades${query}`, {
      method: "GET",
    });
  },
  createTrade: (trade: TradeCreationPayload) =>
    apiRequest<Trade>("/api/trades", {
      method: "POST",
      body: trade,
    }),
};

// Portfolio API functions
export const portfolioApi = {
  getPortfolio: (mode: "paper" | "real" | "live") => {
    // Normalize "live" to "real" for backend compatibility
    const normalizedMode = mode === "live" ? "real" : mode;
    return apiRequest<Portfolio>(`/api/portfolio/${normalizedMode}`, {
      method: "GET",
    });
  },
};

// Market API functions
export const marketApi = {
  getMarkets: () =>
    apiRequest<MarketData[]>("/api/markets", { method: "GET" }),
  getOHLCV: (pair: string, timeframe = "1h", limit = 100) =>
    apiRequest<Array<{ timestamp: number; open: number; high: number; low: number; close: number; volume: number }>>(
      `/api/markets/${pair}/ohlcv?timeframe=${timeframe}&limit=${limit}`, 
      { method: "GET" }
    ),
  getOrderBook: (pair: string) =>
    apiRequest<{ bids: [number, number][]; asks: [number, number][] }>(
      `/api/markets/${pair}/orderbook`, 
      { method: "GET" }
    ),
  getCorrelationMatrix: (symbols: string[], days = 30) => {
    const symbolsParam = symbols.join(",");
    return apiRequest<{ symbols: string[]; matrix: Record<string, Record<string, number>>; calculated_at: string }>(
      `/api/markets/correlation/matrix?symbols=${encodeURIComponent(symbolsParam)}&days=${days}`,
      { method: "GET" }
    );
  },
  getHeatmapData: (symbols: string[], metric: "change_24h" | "volume_24h" | "correlation" = "change_24h", days = 30) => {
    const symbolsParam = symbols.join(",");
    return apiRequest<{ data: Record<string, Record<string, number>>; metric: string; calculated_at: string }>(
      `/api/markets/heatmap/data?symbols=${encodeURIComponent(symbolsParam)}&metric=${metric}&days=${days}`,
      { method: "GET" }
    );
  },
};

// Fee API functions
export const feeApi = {
  getFees: (volumeUSD = 0) =>
    apiRequest<{ maker: number; taker: number; volumeUSD: number }>(`/api/fees?volumeUSD=${volumeUSD}`, { method: "GET" }),
  calculateFees: (data: { amount: number; price: number; side: "buy" | "sell"; isMaker?: boolean; volumeUSD?: number }) =>
    apiRequest<{ fee: number; netAmount: number }>("/api/fees/calculate", { method: "POST", body: data }),
};

// Status API functions
export const statusApi = {
  getStatus: () =>
    apiRequest<{ status: string; timestamp: number }>("/api/status", { method: "GET" }),
};

// Activity API functions
export const activityApi = {
  getRecentActivity: (limit = 10) =>
    apiRequest<Array<{ id: string; type: string; timestamp: string; description: string }>>(`/api/activity/recent?limit=${limit}`, { method: "GET" }),
};

// Performance API functions
export const performanceApi = {
  getSummary: (mode?: "paper" | "real" | "live") => {
    const params = mode ? `?mode=${normalizeTradingMode(mode)}` : "";
    return apiRequest<{ totalReturn: number; sharpeRatio: number; maxDrawdown: number; winRate: number }>(`/api/performance/summary${params}`, { method: "GET" });
  },
};

// Wallet API functions
export interface Wallet {
  wallet_id: number;
  address: string;
  chain_id: number;
  wallet_type: "custodial" | "external";
  label?: string;
  is_verified: boolean;
  is_active: boolean;
  balance?: Record<string, unknown>;
  last_balance_update?: string;
}

export interface WalletBalanceResponse {
  wallet_id: number | null;
  currency: string;
  balance: number;
  available_balance: number;
  locked_balance: number;
  total_deposited: number;
  total_withdrawn: number;
  total_traded: number;
}

export interface WalletTransactionsResponse {
  transactions: Array<{
    id: number;
    type: string;
    status: string;
    amount: number;
    currency: string;
    fee: number;
    net_amount: number;
    description: string | null;
    created_at: string | null;
    processed_at: string | null;
  }>;
}

export const walletApi = {
  getWallets: () => apiRequest<Wallet[]>("/api/wallets", { method: "GET" }),
  createCustodialWallet: (chainId: number) =>
    apiRequest<Wallet>("/api/wallets/custodial", {
      method: "POST",
      body: { chain_id: chainId },
    }),
  registerExternalWallet: (data: { wallet_address: string; chain_id: number; label?: string }) =>
    apiRequest<Wallet>("/api/wallets/external", {
      method: "POST",
      body: data,
    }),
  getDepositAddress: (chainId: number) =>
    apiRequest<{ address: string; chain_id: number }>(`/api/wallets/deposit-address/${chainId}`, {
      method: "GET",
    }),
  getWalletBalance: (walletId: number, tokenAddress?: string) =>
    apiRequest<WalletBalanceResponse>(`/api/wallets/${walletId}/balance${tokenAddress ? `?token_address=${tokenAddress}` : ""}`, {
      method: "GET",
    }),
  refreshBalances: () =>
    apiRequest<{ success: boolean }>("/api/wallets/refresh-balances", {
      method: "POST",
    }),
  getWalletTransactions: (walletId: number, limit: number = 50) =>
    apiRequest<WalletTransactionsResponse>(`/api/wallets/${walletId}/transactions?limit=${limit}`, {
      method: "GET",
    }),
  processWithdrawal: (walletId: number, data: {
    to_address: string;
    amount: string;
    token_address?: string;
    mfa_token?: string;
  }) =>
    apiRequest<{ transaction_hash: string; status: string }>(`/api/wallets/${walletId}/withdraw`, {
      method: "POST",
      body: data,
    }),
};

// Withdrawal API functions
export interface WithdrawalResponse {
  id: string;
  chain_id: number;
  to_address: string;
  amount: string;
  currency: string;
  status: "pending" | "processing" | "completed" | "failed";
  transaction_hash?: string;
  created_at: string;
}

export interface WithdrawalStatusResponse {
  status: "pending" | "processing" | "confirmed" | "failed";
  transaction_hash?: string;
  block_number?: number;
  gas_used?: number;
}

export const withdrawalApi = {
  createWithdrawal: (data: {
    chain_id: number;
    to_address: string;
    amount: string;
    currency: string;
    mfa_token?: string;
  }) =>
    apiRequest<WithdrawalResponse>("/api/withdrawals", {
      method: "POST",
      body: data,
    }),
  getWithdrawalStatus: (chainId: number, txHash: string) =>
    apiRequest<WithdrawalStatusResponse>(`/api/withdrawals/status/${chainId}/${txHash}`, {
      method: "GET",
    }),
  getAdvanced: (mode?: "paper" | "real" | "live", days: number = 30) => {
    const params = new URLSearchParams();
    if (mode) params.append("mode", normalizeTradingMode(mode));
    params.append("days", String(days));
    return apiRequest<Record<string, unknown>>(`/api/performance/advanced?${params.toString()}`, { method: "GET" });
  },
  getDailyPnL: (mode?: "paper" | "real" | "live", days: number = 30) => {
    const params = new URLSearchParams();
    if (mode) params.append("mode", normalizeTradingMode(mode));
    params.append("days", String(days));
    return apiRequest<Array<{ date: string; pnl: number }>>(`/api/performance/daily-pnl?${params.toString()}`, { method: "GET" });
  },
  getDrawdown: (mode?: "paper" | "real" | "live", days: number = 30) => {
    const params = new URLSearchParams();
    if (mode) params.append("mode", normalizeTradingMode(mode));
    params.append("days", String(days));
    return apiRequest<Array<{ date: string; drawdown: number }>>(`/api/performance/drawdown?${params.toString()}`, { method: "GET" });
  },
};

// DEX Trading API functions
export interface DEXQuoteRequest {
  sell_token: string;
  buy_token: string;
  sell_amount?: string;
  buy_amount?: string;
  chain_id?: number;
  slippage_percentage?: number;
  cross_chain?: boolean;
  to_chain_id?: number;
}

export interface DEXSwapRequest {
  sell_token: string;
  buy_token: string;
  sell_amount: string;
  chain_id?: number;
  slippage_percentage?: number;
  custodial?: boolean;
  user_wallet_address?: string;
  signature?: string;
  cross_chain?: boolean;
  to_chain_id?: number;
  idempotency_key: string;
}

export interface SupportedChain {
  chain_id: number;
  name: string;
  symbol: string;
}

export interface DEXQuoteResponse {
  sell_token: string;
  buy_token: string;
  sell_amount: string;
  buy_amount: string;
  price_impact: number;
  gas_estimate: string;
  route: Array<{ dex: string; token_in: string; token_out: string }>;
}

export interface DEXSwapResponse {
  transaction_hash?: string;
  calldata?: string;
  custodial: boolean;
  status: "pending" | "processing" | "completed" | "failed";
  message?: string;
}

export const dexApi = {
  getQuote: (request: DEXQuoteRequest) =>
    apiRequest<DEXQuoteResponse>("/api/dex/quote", {
      method: "POST",
      body: request,
    }),
  
  executeSwap: (request: DEXSwapRequest) =>
    apiRequest<DEXSwapResponse>("/api/dex/swap", {
      method: "POST",
      body: request,
    }),
  
  getSupportedChains: () =>
    apiRequest<SupportedChain[]>("/api/dex/supported-chains", {
      method: "GET",
    }),
};

// Integrations API
export const integrationsApi = {
  status: () => apiRequest<{ status: string; services: Record<string, boolean> }>('/api/integrations/status', { method: 'GET' }),
  predict: (payload: unknown) => apiRequest<{ prediction: string; confidence: number }>('/api/integrations/predict', { method: 'POST', body: payload as string | object }),
  backtest: (payload: unknown) => apiRequest<{ results: Record<string, unknown> }>('/api/integrations/backtest', { method: 'POST', body: payload as string | object }),
  ping: () => apiRequest<{ pong: boolean }>('/api/integrations/ping', { method: 'GET' }),
  startAll: () => apiRequest<{ success: boolean }>('/api/integrations/start', { method: 'POST' }),
  stopAll: () => apiRequest<{ success: boolean }>('/api/integrations/stop', { method: 'POST' }),
};

// Preferences API (mounted at /api/preferences)
export const preferencesApi = {
  get: () => apiRequest<UserPreferences>('/api/preferences/', { method: 'GET' }),
  update: (updates: PreferencesUpdatePayload) => apiRequest<UserPreferences>('/api/preferences/', { method: 'PUT', body: updates }),
  reset: () => apiRequest<UserPreferences>('/api/preferences/reset', { method: 'POST' }),
  updateTheme: (theme: string) => apiRequest<UserPreferences>('/api/preferences/theme', { method: 'PATCH', body: theme }),
};

// Notifications API (mounted at /api/notifications)

export interface NotificationStats {
  total: number;
  unread: number;
  read: number;
}

export const notificationsApi = {
  list: (params: { limit?: number; offset?: number; unread_only?: boolean } = {}) => {
    const qs = new URLSearchParams();
    if (params.limit) qs.append('limit', String(params.limit));
    if (params.offset) qs.append('offset', String(params.offset));
    if (params.unread_only) qs.append('unread_only', 'true');
    const query = qs.toString() ? `?${qs.toString()}` : '';
    return apiRequest<Notification[]>(`/api/notifications/${query}`, { method: 'GET' });
  },
  markRead: (id: number) => apiRequest<Notification>(`/api/notifications/${id}/read`, { method: 'PATCH' }),
  markAllRead: () => apiRequest<{ success: boolean }>('/api/notifications/read-all', { method: 'PATCH' }),
  delete: (id: number) => apiRequest<{ success: boolean }>(`/api/notifications/${id}`, { method: 'DELETE' }),
  stats: () => apiRequest<NotificationStats>('/api/notifications/stats', { method: 'GET' }),
  unreadCount: () => apiRequest<{ count: number }>('/api/notifications/unread-count', { method: 'GET' }),
};

// Recommendations API (mounted at /api/recommendations)
export interface Recommendation {
  id: string;
  type: string;
  symbol?: string;
  action: 'buy' | 'sell' | 'hold';
  confidence: number;
  reason: string;
  timestamp: string;
}

export const recommendationsApi = {
  get: () => apiRequest<Recommendation[]>('/api/recommendations/', { method: 'GET' }),
};

// Risk Scenarios
export interface ScenarioRequest {
  portfolio_value: number;
  baseline_var: number;
  shock_percent: number; // e.g. -0.1 for -10%
  horizon_days?: number;
  correlation_factor?: number;
}

export interface ScenarioResponse {
  portfolio_value: number;
  baseline_var: number;
  shock_percent: number;
  correlation_factor: number;
  horizon_days: number;
  shocked_var: number;
  projected_var: number;
  stress_loss: number;
  horizon_scale: number;
  explanation: string;
}

export async function runRiskScenario(body: ScenarioRequest): Promise<ScenarioResponse> {
  const result = await apiRequest<ScenarioResponse>('/api/risk-scenarios/simulate', { method: 'POST', body });
  return result;
}

// Trading Bot Types (Grid, DCA, Infinity, Trailing)
export interface TradingBotResponse {
  id: string;
  name: string;
  strategy: string;
  status: string;
  mode: string;
  tradingPair: string;
  [key: string]: unknown;
}

// Grid Trading API
export const gridTradingApi = {
  getGridBots: (skip = 0, limit = 100) =>
    apiRequest<TradingBotResponse[]>(`/api/grid-bots?skip=${skip}&limit=${limit}`, { method: "GET" }),
  getGridBot: (id: string) =>
    apiRequest<TradingBotResponse>(`/api/grid-bots/${id}`, { method: "GET" }),
  createGridBot: (bot: Record<string, unknown>) =>
    apiRequest<TradingBotResponse>("/api/grid-bots", { method: "POST", body: bot }),
  startGridBot: (id: string) =>
    apiRequest<TradingBotResponse>(`/api/grid-bots/${id}/start`, { method: "POST" }),
  stopGridBot: (id: string) =>
    apiRequest<TradingBotResponse>(`/api/grid-bots/${id}/stop`, { method: "POST" }),
  deleteGridBot: (id: string) =>
    apiRequest<{ success: boolean }>(`/api/grid-bots/${id}`, { method: "DELETE" }),
};

// DCA Trading API
export const dcaTradingApi = {
  getDCABots: (skip = 0, limit = 100) =>
    apiRequest<TradingBotResponse[]>(`/api/dca-bots?skip=${skip}&limit=${limit}`, { method: "GET" }),
  getDCABot: (id: string) =>
    apiRequest<TradingBotResponse>(`/api/dca-bots/${id}`, { method: "GET" }),
  createDCABot: (bot: BotCreationPayload) =>
    apiRequest<TradingBotResponse>("/api/dca-bots", { method: "POST", body: bot }),
  startDCABot: (id: string) =>
    apiRequest<TradingBotResponse>(`/api/dca-bots/${id}/start`, { method: "POST" }),
  stopDCABot: (id: string) =>
    apiRequest<TradingBotResponse>(`/api/dca-bots/${id}/stop`, { method: "POST" }),
  deleteDCABot: (id: string) =>
    apiRequest<{ success: boolean }>(`/api/dca-bots/${id}`, { method: "DELETE" }),
};

// Infinity Grid API
export const infinityGridApi = {
  getInfinityGrids: (skip = 0, limit = 100) =>
    apiRequest<TradingBotResponse[]>(`/api/infinity-grids?skip=${skip}&limit=${limit}`, { method: "GET" }),
  getInfinityGrid: (id: string) =>
    apiRequest<TradingBotResponse>(`/api/infinity-grids/${id}`, { method: "GET" }),
  createInfinityGrid: (bot: Record<string, unknown>) =>
    apiRequest<TradingBotResponse>("/api/infinity-grids", { method: "POST", body: bot }),
  startInfinityGrid: (id: string) =>
    apiRequest<TradingBotResponse>(`/api/infinity-grids/${id}/start`, { method: "POST" }),
  stopInfinityGrid: (id: string) =>
    apiRequest<TradingBotResponse>(`/api/infinity-grids/${id}/stop`, { method: "POST" }),
  deleteInfinityGrid: (id: string) =>
    apiRequest<{ success: boolean }>(`/api/infinity-grids/${id}`, { method: "DELETE" }),
};

// Trailing Bot API
export const trailingBotApi = {
  getTrailingBots: (skip = 0, limit = 100) =>
    apiRequest<TradingBotResponse[]>(`/api/trailing-bots?skip=${skip}&limit=${limit}`, { method: "GET" }),
  getTrailingBot: (id: string) =>
    apiRequest<TradingBotResponse>(`/api/trailing-bots/${id}`, { method: "GET" }),
  createTrailingBot: (bot: BotCreationPayload) =>
    apiRequest<TradingBotResponse>("/api/trailing-bots", { method: "POST", body: bot }),
  startTrailingBot: (id: string) =>
    apiRequest<TradingBotResponse>(`/api/trailing-bots/${id}/start`, { method: "POST" }),
  stopTrailingBot: (id: string) =>
    apiRequest<TradingBotResponse>(`/api/trailing-bots/${id}/stop`, { method: "POST" }),
  deleteTrailingBot: (id: string) =>
    apiRequest<{ success: boolean }>(`/api/trailing-bots/${id}`, { method: "DELETE" }),
};

// Advanced Orders API functions
export interface AdvancedOrder {
  id: string;
  symbol: string;
  side: "buy" | "sell";
  amount: number;
  status: string;
  type: string;
  [key: string]: unknown;
}

export const advancedOrdersApi = {
  createStopLoss: (data: {
    symbol: string;
    side: "buy" | "sell";
    amount: number;
    stop_price: number;
    limit_price?: number;
    chain_id?: number;
    mode?: "paper" | "real";
  }) =>
    apiRequest<AdvancedOrder>("/api/advanced-orders/stop-loss", {
      method: "POST",
      body: data,
    }),
  
  createTakeProfit: (data: {
    symbol: string;
    side: "buy" | "sell";
    amount: number;
    take_profit_price: number;
    limit_price?: number;
    chain_id?: number;
    mode?: "paper" | "real";
  }) =>
    apiRequest<AdvancedOrder>("/api/advanced-orders/take-profit", {
      method: "POST",
      body: data,
    }),
  
  createTrailingStop: (data: {
    symbol: string;
    side: "buy" | "sell";
    amount: number;
    trailing_stop_percent?: number;
    trailing_stop_amount?: number;
    chain_id?: number;
    mode?: "paper" | "real";
  }) =>
    apiRequest<AdvancedOrder>("/api/advanced-orders/trailing-stop", {
      method: "POST",
      body: data,
    }),
  
  createOCO: (data: {
    symbol: string;
    side: "buy" | "sell";
    amount: number;
    stop_price: number;
    take_profit_price: number;
    chain_id?: number;
    mode?: "paper" | "real";
  }) =>
    apiRequest<AdvancedOrder>("/api/advanced-orders/oco", {
      method: "POST",
      body: data,
    }),
  
  getAdvancedOrders: (symbol?: string, status?: string) => {
    const params = new URLSearchParams();
    if (symbol) params.append("symbol", symbol);
    if (status) params.append("status", status);
    const query = params.toString() ? `?${params.toString()}` : "";
    return apiRequest<AdvancedOrder[]>(`/api/advanced-orders${query}`, {
      method: "GET",
    });
  },
};

// Futures Position Types
export interface FuturesPosition {
  id: string;
  symbol: string;
  side: "long" | "short";
  size: number;
  entry_price: number;
  current_price: number;
  pnl: number;
  pnl_percent: number;
  status: "open" | "closed";
  [key: string]: unknown;
}

export const futuresTradingApi = {
  getFuturesPositions: (skip = 0, limit = 100, openOnly = false) => {
    const params = new URLSearchParams();
    params.append("skip", String(skip));
    params.append("limit", String(limit));
    if (openOnly) params.append("open_only", "true");
    return apiRequest<FuturesPosition[]>(`/api/futures/positions?${params.toString()}`, { method: "GET" });
  },
  getFuturesPosition: (id: string) =>
    apiRequest<FuturesPosition>(`/api/futures/positions/${id}`, { method: "GET" }),
  createFuturesPosition: (position: Record<string, unknown>) =>
    apiRequest<FuturesPosition>("/api/futures/positions", { method: "POST", body: position }),
  closeFuturesPosition: (id: string, closePrice?: number) => {
    const params = closePrice ? `?close_price=${closePrice}` : "";
    return apiRequest<FuturesPosition>(`/api/futures/positions/${id}/close${params}`, { method: "POST" });
  },
  updatePositionPnl: (id: string) =>
    apiRequest<FuturesPosition>(`/api/futures/positions/${id}/update-pnl`, { method: "POST" }),
};

// Webhook Management API
export interface WebhookSubscription {
  id: string;
  url: string;
  events: string[];
  active: boolean;
  created_at: string;
  last_delivery?: string;
  failure_count: number;
}

export interface WebhookDelivery {
  id: string;
  subscription_id: string;
  event_type: string;
  status: "pending" | "success" | "failed" | "retrying";
  attempts: number;
  created_at: string;
  delivered_at?: string;
  error?: string;
}

export const webhookApi = {
  subscribe: (data: {
    url: string;
    events: string[];
    secret?: string;
    max_retries?: number;
    timeout?: number;
  }) =>
    apiRequest<WebhookSubscription>("/api/webhooks/subscribe", {
      method: "POST",
      body: data,
    }),
  unsubscribe: (subscriptionId: string) =>
    apiRequest<{ message: string }>(`/api/webhooks/${subscriptionId}`, {
      method: "DELETE",
    }),
  list: (activeOnly: boolean = true) =>
    apiRequest<WebhookSubscription[]>(`/api/webhooks/?active_only=${activeOnly}`, {
      method: "GET",
    }),
  getStats: () =>
    apiRequest<{
      total_subscriptions: number;
      active_subscriptions: number;
      total_deliveries: number;
      successful_deliveries: number;
      failed_deliveries: number;
      success_rate: number;
    }>("/api/webhooks/stats", { method: "GET" }),
  getDeliveries: (subscriptionId?: string, limit: number = 100) => {
    const params = new URLSearchParams();
    if (subscriptionId) params.append("subscription_id", subscriptionId);
    params.append("limit", String(limit));
    return apiRequest<WebhookDelivery[]>(`/api/webhooks/deliveries?${params.toString()}`, {
      method: "GET",
    });
  },
};

// Feature Flags API
export interface FeatureFlag {
  name: string;
  status: "enabled" | "disabled" | "experimental";
  description: string;
  enabled: boolean;
  enabled_for: string[];
}

export const featureFlagsApi = {
  list: () => apiRequest<FeatureFlag[]>("/api/feature-flags/", { method: "GET" }),
  get: (flagName: string) =>
    apiRequest<FeatureFlag & { metadata: Record<string, unknown> }>(
      `/api/feature-flags/${flagName}`,
      { method: "GET" }
    ),
  enable: (flagName: string) =>
    apiRequest<{ message: string }>(`/api/feature-flags/${flagName}/enable`, {
      method: "POST",
    }),
  disable: (flagName: string) =>
    apiRequest<{ message: string }>(`/api/feature-flags/${flagName}/disable`, {
      method: "POST",
    }),
};

// Error Recovery API
export interface CircuitBreakerState {
  state: "closed" | "open" | "half-open";
  failure_count: number;
  last_failure_time: string | null;
  success_count: number;
}

export const errorRecoveryApi = {
  getCircuitBreakers: () =>
    apiRequest<Record<string, CircuitBreakerState>>("/api/error-recovery/circuit-breakers", {
      method: "GET",
    }),
  getCircuitBreaker: (name: string) =>
    apiRequest<CircuitBreakerState>(`/api/error-recovery/circuit-breakers/${name}`, {
      method: "GET",
    }),
  resetCircuitBreaker: (name: string) =>
    apiRequest<{ message: string }>(`/api/error-recovery/circuit-breakers/${name}/reset`, {
      method: "POST",
    }),
};

// API Analytics API
export interface AnalyticsSummary {
  total_requests: number;
  total_errors: number;
  error_rate: number;
  unique_clients: number;
  unique_endpoints: number;
  popular_endpoints: Array<{
    endpoint: string;
    count: number;
    avg_time_ms: number;
    error_rate: number;
  }>;
  hourly_stats: Array<{
    hour: string;
    requests: number;
    errors: number;
    avg_duration: number;
    endpoints: Record<string, number>;
  }>;
}

export const analyticsApi = {
  getSummary: () =>
    apiRequest<AnalyticsSummary>("/api/analytics/summary", { method: "GET" }),
  getEndpointStats: (endpoint?: string) => {
    const url = endpoint
      ? `/api/analytics/endpoints?endpoint=${encodeURIComponent(endpoint)}`
      : "/api/analytics/endpoints";
    return apiRequest<Record<string, unknown>>(url, { method: "GET" });
  },
  getPopular: (limit: number = 10) =>
    apiRequest<{ popular_endpoints: Array<Record<string, unknown>> }>(
      `/api/analytics/popular?limit=${limit}`,
      { method: "GET" }
    ),
};

// Monitoring API
export interface Alert {
  id: string;
  level: "info" | "warning" | "error" | "critical";
  title: string;
  message: string;
  source: string;
  timestamp: string;
  resolved: boolean;
  resolved_at?: string;
}

export const monitoringApi = {
  getAlerts: (params?: {
    level?: string;
    resolved?: boolean;
    limit?: number;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.level) queryParams.append("level", params.level);
    if (params?.resolved !== undefined) queryParams.append("resolved", String(params.resolved));
    if (params?.limit) queryParams.append("limit", String(params.limit));
    const query = queryParams.toString() ? `?${queryParams.toString()}` : "";
    return apiRequest<Alert[]>(`/api/monitoring/alerts${query}`, { method: "GET" });
  },
  resolveAlert: (alertId: string) =>
    apiRequest<{ message: string }>(`/api/monitoring/alerts/${alertId}/resolve`, {
      method: "POST",
    }),
  getStats: () =>
    apiRequest<{
      total_alerts: number;
      unresolved_alerts: number;
      resolved_alerts: number;
      alert_rules: number;
      notifiers: number;
      metrics_tracked: number;
    }>("/api/monitoring/stats", { method: "GET" }),
};

// Security Audit API
export interface SecurityAuditResult {
  overall_status: "pass" | "fail";
  total_issues: number;
  configuration: {
    status: "pass" | "fail";
    issues: Array<{
      level: "error" | "warning";
      category: string;
      message: string;
      recommendation: string;
    }>;
  };
  secrets: {
    status: "pass" | "fail";
    issues: Array<{
      file: string;
      line: number;
      pattern: string;
      level: "critical";
      message: string;
    }>;
    files_scanned: number;
  };
  dependencies: {
    status: "pass" | "fail";
    issues: Array<{
      level: "warning";
      package: string;
      version: string;
      message: string;
      recommendation: string;
    }>;
  };
  security_headers: {
    status: "pass" | "fail";
    issues: Array<{
      level: "warning";
      category: string;
      message: string;
      recommendation: string;
    }>;
  };
}

export const securityAuditApi = {
  runFullAudit: () =>
    apiRequest<SecurityAuditResult>("/api/security/audit", { method: "GET" }),
  auditConfiguration: () =>
    apiRequest<{ status: string; issues: Array<Record<string, unknown>> }>(
      "/api/security/audit/configuration",
      { method: "GET" }
    ),
  scanSecrets: () =>
    apiRequest<{
      status: string;
      issues: Array<Record<string, unknown>>;
      files_scanned: number;
    }>("/api/security/audit/secrets", { method: "GET" }),
  auditDependencies: () =>
    apiRequest<{ status: string; issues: Array<Record<string, unknown>> }>(
      "/api/security/audit/dependencies",
      { method: "GET" }
    ),
};

// Logging API
export interface LogEntry {
  level: string;
  message: string;
  source: string;
  timestamp: string;
  metadata: Record<string, unknown>;
}

export const loggingApi = {
  getLogs: (params?: {
    level?: string;
    source?: string;
    start_time?: string;
    end_time?: string;
    limit?: number;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.level) queryParams.append("level", params.level);
    if (params?.source) queryParams.append("source", params.source);
    if (params?.start_time) queryParams.append("start_time", params.start_time);
    if (params?.end_time) queryParams.append("end_time", params.end_time);
    if (params?.limit) queryParams.append("limit", String(params.limit));
    const query = queryParams.toString() ? `?${queryParams.toString()}` : "";
    return apiRequest<{ logs: LogEntry[]; count: number }>(`/api/logs/${query}`, {
      method: "GET",
    });
  },
  getStats: () =>
    apiRequest<{
      total_logs: number;
      recent_logs_1h: number;
      by_level: Record<string, number>;
      error_patterns: Record<string, number>;
      top_errors: Array<[string, number]>;
    }>("/api/logs/stats", { method: "GET" }),
  search: (query: string, limit: number = 100) =>
    apiRequest<{ logs: LogEntry[]; count: number; query: string }>(
      `/api/logs/search?query=${encodeURIComponent(query)}&limit=${limit}`,
      { method: "GET" }
    ),
  export: (params?: {
    format?: "json" | "csv" | "txt";
    start_time?: string;
    end_time?: string;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.format) queryParams.append("format", params.format);
    if (params?.start_time) queryParams.append("start_time", params.start_time);
    if (params?.end_time) queryParams.append("end_time", params.end_time);
    const query = queryParams.toString() ? `?${queryParams.toString()}` : "";
    return fetch(`/api/logs/export${query}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("auth_token") || sessionStorage.getItem("auth_token")}`,
      },
    }).then((res) => res.blob());
  },
};

