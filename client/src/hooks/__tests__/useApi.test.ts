import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
// Note: Import actual hooks from useApi
// import { useBots, usePortfolio, useTrades } from '../useApi';
import { mockData } from '@/test/testUtils';

// Mock fetch
global.fetch = vi.fn();

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
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
    it('should fetch bots successfully', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ bots: [mockData.bot] }),
      });

      const { result } = renderHook(() => useBots(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual([mockData.bot]);
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
    it('should fetch portfolio successfully', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData.portfolio,
      });

      const { result } = renderHook(() => usePortfolio('paper'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockData.portfolio);
    });
  });

  describe('useTrades', () => {
    it('should fetch trades successfully', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ trades: [mockData.trade] }),
      });

      const { result } = renderHook(() => useTrades(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual([mockData.trade]);
    });
  });
});

