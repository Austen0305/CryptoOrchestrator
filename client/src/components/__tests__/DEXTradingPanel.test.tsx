/**
 * DEXTradingPanel Component Tests
 * Tests DEX swap functionality and price impact warnings
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { DEXTradingPanel } from "../DEXTradingPanel";

// Mock API
vi.mock("@/hooks/useDEXTrading", () => ({
  useDEXSwap: () => ({
    mutate: vi.fn(),
    isLoading: false,
    error: null,
  }),
  useDEXQuote: () => ({
    data: {
      price: 50000,
      priceImpact: 0.005, // 0.5% - below threshold
      estimatedGas: "0.001",
    },
    isLoading: false,
  }),
}));

// Mock auth
vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    isAuthenticated: true,
    user: { id: "1" },
  }),
}));

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

    expect(screen.getByText(/swap|trade/i)).toBeInTheDocument();
  });

  it("shows price impact warning when impact is high", () => {
    // Mock high price impact
    vi.mock("@/hooks/useDEXTrading", () => ({
      useDEXQuote: () => ({
        data: {
          price: 50000,
          priceImpact: 0.02, // 2% - above 1% threshold
        },
        isLoading: false,
      }),
    }));

    render(
      <QueryClientProvider client={queryClient}>
        <DEXTradingPanel />
      </QueryClientProvider>
    );

    expect(screen.getByText(/price impact|warning/i)).toBeInTheDocument();
  });
});
