import ky from 'ky';
import { z } from 'zod';

// Base API configuration
const api = ky.create({
  prefixUrl: import.meta.env.VITE_API_URL || '/api',
  retry: {
    limit: 2,
    methods: ['get', 'put', 'head', 'delete', 'options', 'trace'],
    statusCodes: [408, 413, 429, 500, 502, 503, 504],
  },
  timeout: 10000,
  hooks: {
    beforeRequest: [
      (request) => {
        // CSRF handling or Auth headers if needed (though HTTPOnly cookies are preferred 2026)
      },
    ],
  },
});

// Generic DAL response wrapper
export type DalResponse<T> = {
  data: T;
  error?: string;
};

// Strict Typed Data Access Layer
// Functions here should return strict Zod-parsed data or throw
export const dal = {
  /**
   * Fetch portfolio summary.
   * Uses Zod for runtime validation of the financial response.
   */
  getPortfolio: async () => {
    // Define schema locally or import from shared
    const schema = z.object({
        totalBalance: z.number(),
        allocations: z.record(z.string(), z.number()),
        // Add more fields as per 2026 spec
    });
    
    const json = await api.get('portfolio/summary').json();
    return schema.parse(json);
  },

  /**
   * Execute a trade.
   * This ensures strictly typed payloads are sent.
   */
  executeTrade: async (payload: { symbol: string; amount: string; side: 'buy' | 'sell' }) => {
    return api.post('trading/execute', { json: payload }).json();
  }
};
