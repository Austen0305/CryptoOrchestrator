import { apiRequest } from "./queryClient";
import type { BotConfig, InsertBotConfig } from "../../../shared/schema";

// Bot API functions
export const botApi = {
  getBots: () => apiRequest("/api/bots", { method: "GET" }).then((res) => res),
  getBot: (id: string) =>
    apiRequest(`/api/bots/${id}`, { method: "GET" }).then((res) => res),
  createBot: (bot: InsertBotConfig) =>
    apiRequest("/api/bots", { method: "POST", body: bot }).then((res) => res),
  updateBot: (id: string, updates: Partial<BotConfig>) =>
    apiRequest(`/api/bots/${id}`, { method: "PATCH", body: updates }).then((res) => res),
  deleteBot: (id: string) =>
    apiRequest(`/api/bots/${id}`, { method: "DELETE" }).then((res) => res),
  startBot: (id: string) =>
    apiRequest(`/api/bots/${id}/start`, { method: "POST" }).then((res) => res),
  stopBot: (id: string) =>
    apiRequest(`/api/bots/${id}/stop`, { method: "POST" }).then((res) => res),
  getBotModel: (id: string) =>
    apiRequest(`/api/bots/${id}/model`, { method: "GET" }).then((res) => res),
  getBotPerformance: (id: string) =>
    apiRequest(`/api/bots/${id}/performance`, { method: "GET" }).then((res) => res),
};

// Trade API functions
export const tradeApi = {
  getTrades: (botId?: string, mode?: "paper" | "real" | "live") => {
    const params = new URLSearchParams();
    if (botId) params.append("botId", botId);
    if (mode) {
      // Normalize "live" to "real" for backend compatibility
      const normalizedMode = mode === "live" ? "real" : mode;
      params.append("mode", normalizedMode);
    }
    const query = params.toString() ? `?${params.toString()}` : "";
    return apiRequest(`/api/trades${query}`, {
      method: "GET",
    }).then((res) => res);
  },
  createTrade: (trade: any) =>
    apiRequest("/api/trades", {
      method: "POST",
      body: trade,
    }).then((res) => res),
};

// Portfolio API functions
export const portfolioApi = {
  getPortfolio: (mode: "paper" | "real" | "live") => {
    // Normalize "live" to "real" for backend compatibility
    const normalizedMode = mode === "live" ? "real" : mode;
    return apiRequest(`/api/portfolio/${normalizedMode}`, {
      method: "GET",
    }).then((res) => res);
  },
};

// Market API functions
export const marketApi = {
  getMarkets: () =>
    apiRequest("/api/markets", { method: "GET" }).then((res) => res),
  getOHLCV: (pair: string, timeframe = "1h", limit = 100) =>
    apiRequest(`/api/markets/${pair}/ohlcv?timeframe=${timeframe}&limit=${limit}`, { method: "GET" }).then((res) => res),
  getOrderBook: (pair: string) =>
    apiRequest(`/api/markets/${pair}/orderbook`, { method: "GET" }).then((res) => res),
};

// Fee API functions
export const feeApi = {
  getFees: (volumeUSD = 0) =>
    apiRequest(`/api/fees?volumeUSD=${volumeUSD}`, { method: "GET" }).then((res) => res),
  calculateFees: (data: { amount: number; price: number; side: "buy" | "sell"; isMaker?: boolean; volumeUSD?: number }) =>
    apiRequest("/api/fees/calculate", { method: "POST", body: data }).then((res) => res),
};

// Status API functions
export const statusApi = {
  getStatus: () =>
    apiRequest("/api/status", { method: "GET" }).then((res) => res),
};

// Activity API functions
export const activityApi = {
  getRecentActivity: (limit = 10) =>
    apiRequest(`/api/activity/recent?limit=${limit}`, { method: "GET" }).then((res) => res),
};

// Performance API functions
export const performanceApi = {
  getSummary: (mode?: "paper" | "real" | "live") => {
    const params = mode ? `?mode=${mode === "live" ? "real" : mode}` : "";
    return apiRequest(`/api/performance/summary${params}`, { method: "GET" }).then((res) => res);
  },
  getAdvanced: (mode?: "paper" | "real" | "live", days: number = 30) => {
    const params = new URLSearchParams();
    if (mode) params.append("mode", mode === "live" ? "real" : mode);
    params.append("days", String(days));
    return apiRequest(`/api/performance/advanced?${params.toString()}`, { method: "GET" }).then((res) => res);
  },
  getDailyPnL: (mode?: "paper" | "real" | "live", days: number = 30) => {
    const params = new URLSearchParams();
    if (mode) params.append("mode", mode === "live" ? "real" : mode);
    params.append("days", String(days));
    return apiRequest(`/api/performance/daily-pnl?${params.toString()}`, { method: "GET" }).then((res) => res);
  },
  getDrawdown: (mode?: "paper" | "real" | "live", days: number = 30) => {
    const params = new URLSearchParams();
    if (mode) params.append("mode", mode === "live" ? "real" : mode);
    params.append("days", String(days));
    return apiRequest(`/api/performance/drawdown?${params.toString()}`, { method: "GET" }).then((res) => res);
  },
};

// Integrations API
export const integrationsApi = {
  status: () => apiRequest('/api/integrations/status', { method: 'GET' }).then((r) => r),
  predict: (payload: any) => apiRequest('/api/integrations/predict', { method: 'POST', body: payload }).then((r) => r),
  backtest: (payload: any) => apiRequest('/api/integrations/backtest', { method: 'POST', body: payload }).then((r) => r),
  ping: () => apiRequest('/api/integrations/ping', { method: 'GET' }).then((r) => r),
  startAll: () => apiRequest('/api/integrations/start', { method: 'POST' }).then((r) => r),
  stopAll: () => apiRequest('/api/integrations/stop', { method: 'POST' }).then((r) => r),
};

// Preferences API (mounted at /api/preferences)
export const preferencesApi = {
  get: () => apiRequest('/api/preferences/', { method: 'GET' }).then(r => r),
  update: (updates: any) => apiRequest('/api/preferences/', { method: 'PUT', body: updates }).then(r => r),
  reset: () => apiRequest('/api/preferences/reset', { method: 'POST' }).then(r => r),
  updateTheme: (theme: string) => apiRequest('/api/preferences/theme', { method: 'PATCH', body: theme }).then(r => r),
};

// Notifications API (mounted at /api/notifications)
export const notificationsApi = {
  list: (params: { limit?: number; offset?: number; unread_only?: boolean } = {}) => {
    const qs = new URLSearchParams();
    if (params.limit) qs.append('limit', String(params.limit));
    if (params.offset) qs.append('offset', String(params.offset));
    if (params.unread_only) qs.append('unread_only', 'true');
    const query = qs.toString() ? `?${qs.toString()}` : '';
    return apiRequest(`/api/notifications/${query}`, { method: 'GET' }).then(r => r);
  },
  markRead: (id: number) => apiRequest(`/api/notifications/${id}/read`, { method: 'PATCH' }).then(r => r),
  markAllRead: () => apiRequest('/api/notifications/read-all', { method: 'PATCH' }).then(r => r),
  delete: (id: number) => apiRequest(`/api/notifications/${id}`, { method: 'DELETE' }).then(r => r),
  stats: () => apiRequest('/api/notifications/stats', { method: 'GET' }).then(r => r),
  unreadCount: () => apiRequest('/api/notifications/unread-count', { method: 'GET' }).then(r => r),
};

// Recommendations API (mounted at /api/recommendations)
export const recommendationsApi = {
  get: () => apiRequest('/api/recommendations/', { method: 'GET' }).then(r => r),
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
  return apiRequest('/api/risk-scenarios/simulate', { method: 'POST', body }).then(r => r);
}

// Grid Trading API
export const gridTradingApi = {
  getGridBots: (skip = 0, limit = 100) =>
    apiRequest(`/api/grid-bots?skip=${skip}&limit=${limit}`, { method: "GET" }).then((res) => res),
  getGridBot: (id: string) =>
    apiRequest(`/api/grid-bots/${id}`, { method: "GET" }).then((res) => res),
  createGridBot: (bot: any) =>
    apiRequest("/api/grid-bots", { method: "POST", body: bot }).then((res) => res),
  startGridBot: (id: string) =>
    apiRequest(`/api/grid-bots/${id}/start`, { method: "POST" }).then((res) => res),
  stopGridBot: (id: string) =>
    apiRequest(`/api/grid-bots/${id}/stop`, { method: "POST" }).then((res) => res),
  deleteGridBot: (id: string) =>
    apiRequest(`/api/grid-bots/${id}`, { method: "DELETE" }).then((res) => res),
};

// DCA Trading API
export const dcaTradingApi = {
  getDCABots: (skip = 0, limit = 100) =>
    apiRequest(`/api/dca-bots?skip=${skip}&limit=${limit}`, { method: "GET" }).then((res) => res),
  getDCABot: (id: string) =>
    apiRequest(`/api/dca-bots/${id}`, { method: "GET" }).then((res) => res),
  createDCABot: (bot: any) =>
    apiRequest("/api/dca-bots", { method: "POST", body: bot }).then((res) => res),
  startDCABot: (id: string) =>
    apiRequest(`/api/dca-bots/${id}/start`, { method: "POST" }).then((res) => res),
  stopDCABot: (id: string) =>
    apiRequest(`/api/dca-bots/${id}/stop`, { method: "POST" }).then((res) => res),
  deleteDCABot: (id: string) =>
    apiRequest(`/api/dca-bots/${id}`, { method: "DELETE" }).then((res) => res),
};

// Infinity Grid API
export const infinityGridApi = {
  getInfinityGrids: (skip = 0, limit = 100) =>
    apiRequest(`/api/infinity-grids?skip=${skip}&limit=${limit}`, { method: "GET" }).then((res) => res),
  getInfinityGrid: (id: string) =>
    apiRequest(`/api/infinity-grids/${id}`, { method: "GET" }).then((res) => res),
  createInfinityGrid: (bot: any) =>
    apiRequest("/api/infinity-grids", { method: "POST", body: bot }).then((res) => res),
  startInfinityGrid: (id: string) =>
    apiRequest(`/api/infinity-grids/${id}/start`, { method: "POST" }).then((res) => res),
  stopInfinityGrid: (id: string) =>
    apiRequest(`/api/infinity-grids/${id}/stop`, { method: "POST" }).then((res) => res),
  deleteInfinityGrid: (id: string) =>
    apiRequest(`/api/infinity-grids/${id}`, { method: "DELETE" }).then((res) => res),
};

// Trailing Bot API
export const trailingBotApi = {
  getTrailingBots: (skip = 0, limit = 100) =>
    apiRequest(`/api/trailing-bots?skip=${skip}&limit=${limit}`, { method: "GET" }).then((res) => res),
  getTrailingBot: (id: string) =>
    apiRequest(`/api/trailing-bots/${id}`, { method: "GET" }).then((res) => res),
  createTrailingBot: (bot: any) =>
    apiRequest("/api/trailing-bots", { method: "POST", body: bot }).then((res) => res),
  startTrailingBot: (id: string) =>
    apiRequest(`/api/trailing-bots/${id}/start`, { method: "POST" }).then((res) => res),
  stopTrailingBot: (id: string) =>
    apiRequest(`/api/trailing-bots/${id}/stop`, { method: "POST" }).then((res) => res),
  deleteTrailingBot: (id: string) =>
    apiRequest(`/api/trailing-bots/${id}`, { method: "DELETE" }).then((res) => res),
};

// Futures Trading API
export const futuresTradingApi = {
  getFuturesPositions: (skip = 0, limit = 100, openOnly = false) => {
    const params = new URLSearchParams();
    params.append("skip", String(skip));
    params.append("limit", String(limit));
    if (openOnly) params.append("open_only", "true");
    return apiRequest(`/api/futures/positions?${params.toString()}`, { method: "GET" }).then((res) => res);
  },
  getFuturesPosition: (id: string) =>
    apiRequest(`/api/futures/positions/${id}`, { method: "GET" }).then((res) => res),
  createFuturesPosition: (position: any) =>
    apiRequest("/api/futures/positions", { method: "POST", body: position }).then((res) => res),
  closeFuturesPosition: (id: string, closePrice?: number) => {
    const params = closePrice ? `?close_price=${closePrice}` : "";
    return apiRequest(`/api/futures/positions/${id}/close${params}`, { method: "POST" }).then((res) => res);
  },
  updatePositionPnl: (id: string) =>
    apiRequest(`/api/futures/positions/${id}/update-pnl`, { method: "POST" }).then((res) => res),
};

