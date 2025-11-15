import { apiRequest } from "./queryClient";
import type { BotConfig, InsertBotConfig } from "../../../shared/schema";

// Bot API functions
export const botApi = {
  getBots: () => apiRequest("GET", "/api/bots").then((res) => res.json()),
  getBot: (id: string) =>
    apiRequest("GET", `/api/bots/${id}`).then((res) => res.json()),
  createBot: (bot: InsertBotConfig) =>
    apiRequest("POST", "/api/bots", bot).then((res) => res.json()),
  updateBot: (id: string, updates: Partial<BotConfig>) =>
    apiRequest("PATCH", `/api/bots/${id}`, updates).then((res) => res.json()),
  deleteBot: (id: string) =>
    apiRequest("DELETE", `/api/bots/${id}`).then((res) => res.json()),
  startBot: (id: string) =>
    apiRequest("POST", `/api/bots/${id}/start`).then((res) => res.json()),
  stopBot: (id: string) =>
    apiRequest("POST", `/api/bots/${id}/stop`).then((res) => res.json()),
  getBotModel: (id: string) =>
    apiRequest("GET", `/api/bots/${id}/model`).then((res) => res.json()),
  getBotPerformance: (id: string) =>
    apiRequest("GET", `/api/bots/${id}/performance`).then((res) => res.json()),
};

// Trade API functions
export const tradeApi = {
  getTrades: (botId?: string, mode?: "paper" | "live") => {
    const params = new URLSearchParams();
    if (botId) params.append("botId", botId);
    if (mode) params.append("mode", mode);
    const query = params.toString() ? `?${params.toString()}` : "";
    return apiRequest("GET", `/api/trades${query}`).then((res) => res.json());
  },
  createTrade: (trade: any) =>
    apiRequest("POST", "/api/trades", trade).then((res) => res.json()),
};

// Portfolio API functions
export const portfolioApi = {
  getPortfolio: (mode: "paper" | "live") =>
    apiRequest("GET", `/api/portfolio/${mode}`).then((res) => res.json()),
};

// Market API functions
export const marketApi = {
  getMarkets: () =>
    apiRequest("GET", "/api/markets").then((res) => res.json()),
  getOHLCV: (pair: string, timeframe = "1h", limit = 100) =>
    apiRequest("GET", `/api/markets/${pair}/ohlcv?timeframe=${timeframe}&limit=${limit}`).then((res) => res.json()),
  getOrderBook: (pair: string) =>
    apiRequest("GET", `/api/markets/${pair}/orderbook`).then((res) => res.json()),
};

// Fee API functions
export const feeApi = {
  getFees: (volumeUSD = 0) =>
    apiRequest("GET", `/api/fees?volumeUSD=${volumeUSD}`).then((res) => res.json()),
  calculateFees: (data: { amount: number; price: number; side: "buy" | "sell"; isMaker?: boolean; volumeUSD?: number }) =>
    apiRequest("POST", "/api/fees/calculate", data).then((res) => res.json()),
};

// Status API functions
export const statusApi = {
  getStatus: () =>
    apiRequest("GET", "/api/status").then((res) => res.json()),
};

// Integrations API
export const integrationsApi = {
  status: () => apiRequest('GET', '/api/integrations/status').then((r) => r.json()),
  predict: (payload: any) => apiRequest('POST', '/api/integrations/predict', payload).then((r) => r.json()),
  backtest: (payload: any) => apiRequest('POST', '/api/integrations/backtest', payload).then((r) => r.json()),
  ping: () => apiRequest('GET', '/api/integrations/ping').then((r) => r.json()),
  startAll: () => apiRequest('POST', '/api/integrations/start').then((r) => r.json()),
  stopAll: () => apiRequest('POST', '/api/integrations/stop').then((r) => r.json()),
};

// Preferences API (mounted at /api/preferences)
export const preferencesApi = {
  get: () => apiRequest('GET', '/api/preferences/').then(r => r.json()),
  update: (updates: any) => apiRequest('PUT', '/api/preferences/', updates).then(r => r.json()),
  reset: () => apiRequest('POST', '/api/preferences/reset').then(r => r.json()),
  updateTheme: (theme: string) => apiRequest('PATCH', '/api/preferences/theme', theme).then(r => r.json()),
};

// Notifications API (mounted at /api/notifications)
export const notificationsApi = {
  list: (params: { limit?: number; offset?: number; unread_only?: boolean } = {}) => {
    const qs = new URLSearchParams();
    if (params.limit) qs.append('limit', String(params.limit));
    if (params.offset) qs.append('offset', String(params.offset));
    if (params.unread_only) qs.append('unread_only', 'true');
    const query = qs.toString() ? `?${qs.toString()}` : '';
    return apiRequest('GET', `/api/notifications/${query}`).then(r => r.json());
  },
  markRead: (id: number) => apiRequest('PATCH', `/api/notifications/${id}/read`).then(r => r.json()),
  markAllRead: () => apiRequest('PATCH', '/api/notifications/read-all').then(r => r.json()),
  delete: (id: number) => apiRequest('DELETE', `/api/notifications/${id}`).then(r => r.json()),
  stats: () => apiRequest('GET', '/api/notifications/stats').then(r => r.json()),
  unreadCount: () => apiRequest('GET', '/api/notifications/unread-count').then(r => r.json()),
};

// Recommendations API (mounted at /api/recommendations)
export const recommendationsApi = {
  get: () => apiRequest('GET', '/api/recommendations/').then(r => r.json()),
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
  return apiRequest('POST', `/api/risk-scenarios/simulate`, body).then(r => r.json());
}

