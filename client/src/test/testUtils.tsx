/**
 * Testing Utilities
 * Common utilities for React component testing
 */

import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@/components/ThemeProvider';
import { ErrorBoundary } from '@/components/ErrorBoundary';

/**
 * Create a test QueryClient with default options
 */
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

/**
 * Custom render function with all providers
 */
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient;
}

export function renderWithProviders(
  ui: ReactElement,
  { queryClient = createTestQueryClient(), ...renderOptions }: CustomRenderOptions = {}
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <ErrorBoundary>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider attribute="class" defaultTheme="dark">
            {children}
          </ThemeProvider>
        </QueryClientProvider>
      </ErrorBoundary>
    );
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
    queryClient,
  };
}

/**
 * Wait for async state updates
 */
export const waitForAsync = () => new Promise((resolve) => setTimeout(resolve, 0));

/**
 * Mock API response
 */
export function mockApiResponse<T>(data: T, delay = 0) {
  return new Promise<T>((resolve) => {
    setTimeout(() => resolve(data), delay);
  });
}

/**
 * Mock API error
 */
export function mockApiError(message = 'API Error', status = 500) {
  return Promise.reject({
    message,
    status,
    response: {
      data: { error: message },
      status,
    },
  });
}

/**
 * Generate mock data
 */
export const mockData = {
  portfolio: {
    totalValue: 10000,
    totalCost: 9500,
    profit: 500,
    profitPercent: 5.26,
    holdings: [
      { symbol: 'BTC', amount: 0.5, value: 22500, cost: 22000 },
      { symbol: 'ETH', amount: 5, value: 7500, cost: 7000 },
    ],
  },
  
  bot: {
    id: 'test-bot-1',
    name: 'Test Bot',
    status: 'active',
    strategy: 'simple_ma',
    tradingPair: 'BTC/USD',
    profit: 100,
    profitPercent: 2.5,
    tradesCount: 10,
    winRate: 60,
  },
  
  trade: {
    id: 'trade-1',
    symbol: 'BTC/USD',
    side: 'buy',
    amount: 0.1,
    price: 45000,
    timestamp: new Date().toISOString(),
    pnl: 50,
  },
  
  market: {
    pair: 'BTC/USD',
    price: 45000,
    change24h: 2.5,
    volume24h: 1000000,
    high24h: 46000,
    low24h: 44000,
  },
};

// Re-export everything from testing library
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';

