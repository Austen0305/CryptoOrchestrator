import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import { useBots, usePortfolio, useTrades } from '../useApi';
import { mockData } from '@/test/testUtils';

// Mock useAuth
vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    token: 'test-token',
    isAuthenticated: true,
    user: { id: '1', email: 'test@example.com' },
  }),
}));

// Mock usePortfolioWebSocket
vi.mock('@/hooks/usePortfolioWebSocket', () => ({
  usePortfolioWebSocket: () => ({
    isConnected: false,
    portfolio: null,
  }),
}));

// Mock fetch
vi.stubGlobal('fetch', vi.fn());

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
        gcTime: 0
      },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useApi hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useBots', () => {
  it("should fetch bots successfully", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ data: [mockData.bot] }),
    } as any);

    const { result } = renderHook(() => useBots(), { wrapper: createWrapper() });

      await waitFor(() => {
        if (result.current.isError) console.error(result.current.error);
        expect(result.current.isSuccess).toBe(true);
      }, { timeout: 3000 });

      expect(result.current.data).toBeInstanceOf(Array);
      expect(result.current.data).toContainEqual(expect.objectContaining({ name: mockData.bot.name }));
    });

    it('should handle fetch error', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => useBots(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });
    });
  });

  describe('usePortfolio', () => {
    it("should fetch portfolio successfully", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ data: mockData.portfolio }),
    } as any);

    const { result } = renderHook(() => usePortfolio("paper"), { wrapper: createWrapper() });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockData.portfolio);
    });
  });

  describe('useTrades', () => {
  it("should fetch trades successfully", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ data: [mockData.trade] }),
    } as any);

    const { result } = renderHook(() => useTrades(), { wrapper: createWrapper() });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      }, { timeout: 3000 });

      expect(result.current.data).toBeInstanceOf(Array);
      expect(result.current.data).toContainEqual(expect.objectContaining({ id: mockData.trade.id }));
    });
  });
});
