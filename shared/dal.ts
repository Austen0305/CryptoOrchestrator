import { z } from 'zod';

// Configurable Adapter Interface (since Web uses ky, Native uses fetch/axios)
export interface HttpAdapter {
  get: <T>(url: string) => Promise<T>;
  post: <T>(url: string, body: any) => Promise<T>;
}

// Default Schema Definitions (Cross-Platform)
export const PortfolioSchema = z.object({
  totalBalance: z.number(),
  allocations: z.record(z.string(), z.number()),
  lastUpdated: z.string().datetime().optional(),
});

export type Portfolio = z.infer<typeof PortfolioSchema>;

export const TradeSchema = z.object({
  symbol: z.string(),
  amount: z.string(),
  side: z.enum(['buy', 'sell']),
});

export type TradePayload = z.infer<typeof TradeSchema>;

// The Shared DAL Class
export class SharedDAL {
  constructor(private adapter: HttpAdapter) {}

  async getPortfolio(): Promise<Portfolio> {
    const json = await this.adapter.get('portfolio/summary');
    return PortfolioSchema.parse(json);
  }

  async executeTrade(payload: TradePayload): Promise<any> {
    const validPayload = TradeSchema.parse(payload);
    return this.adapter.post('trading/execute', validPayload);
  }

  async createTrade(data: any): Promise<any> {
    return this.adapter.post('trading/execute', data);
  }

  async getDexQuote(params: any): Promise<any> {
    // Construct query string manually or assume adapter handles it?
    // Native fetch adapter doesn't handle query params automatically in get(url).
    // We should probably append params.
    const queryString = new URLSearchParams(params as Record<string, string>).toString();
    return this.adapter.get(`dex/quote?${queryString}`);
  }

  async executeDexSwap(data: any): Promise<any> {
    return this.adapter.post('dex/swap', data);
  }

  async startBot(botId: string): Promise<any> {
    return this.adapter.post(`bots/${botId}/start`, {});
  }

  async stopBot(botId: string): Promise<any> {
    return this.adapter.post(`bots/${botId}/stop`, {});
  }

  async get<T>(url: string): Promise<T> {
    return this.adapter.get<T>(url);
  }

  async post<T>(url: string, body: any): Promise<T> {
    return this.adapter.post<T>(url, body);
  }
}
