/**
 * DEXTradingPanel Component Tests
 * Tests DEX swap functionality and price impact warnings
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { DEXTradingPanel } from "../DEXTradingPanel";

vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    isAuthenticated: true,
    user: { id: "1" },
  }),
}));

vi.mock("@/hooks/useWeb3Wallet", () => ({
  useWeb3Wallet: () => ({
    address: "0x123",
    isConnected: true,
  }),
}));

vi.mock("@/hooks/useDEXTrading", () => {
  return {
    useDEXSwap: vi.fn(() => ({
      mutate: vi.fn(),
      isLoading: false,
      error: null,
    })),
    useDEXQuote: vi.fn(() => ({
      mutateAsync: vi.fn(),
      data: {
        price: 50000,
        priceImpact: 0.005,
        estimatedGas: "0.001",
      },
      isLoading: false,
    })),
    useSupportedChains: vi.fn(() => ({
      data: [{ chain_id: 1, name: "Ethereum", symbol: "ETH" }],
    })),
  };
});

describe("DEXTradingPanel", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
  });

  it("renders DEX trading interface", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <DEXTradingPanel />
      </QueryClientProvider>
    );

    expect(screen.getByText(/DEX Trading/i)).toBeInTheDocument();
  });

  it("shows price impact warning when impact is high", () => {
    // Mock high price impact
    // Mock high price impact
    const { useDEXQuote } = await import("@/hooks/useDEXTrading");
    vi.mocked(useDEXQuote).mockReturnValue({
      mutateAsync: vi.fn(),
      data: {
        price: 50000,
        priceImpact: 0.02, // 2% - above 1% threshold
        estimatedGas: "0.001",
      },
      isLoading: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <DEXTradingPanel />
      </QueryClientProvider>
    );

    expect(screen.getByText(/price impact|warning/i)).toBeInTheDocument();
  });
});
