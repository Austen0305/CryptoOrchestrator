import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CopyTrading } from "../CopyTrading";
import * as useCopyTrading from "@/hooks/useCopyTrading";

// Mock the hooks
vi.mock("@/hooks/useCopyTrading", () => ({
  useCopyTrading: vi.fn(),
  useFollowTrader: vi.fn(),
  useUnfollowTrader: vi.fn(),
  useCopyTradingStats: vi.fn(),
  useFollowedTraders: vi.fn(),
}));

// Mock toast
vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

describe("CopyTrading", () => {
  let queryClient: QueryClient;
  let mockCopyTrading: any;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    mockCopyTrading = {
      data: {
        followedTraders: [],
        availableTraders: [
          { id: "trader-1", username: "Trader1", performance: { winRate: 65, totalTrades: 100 } },
          { id: "trader-2", username: "Trader2", performance: { winRate: 70, totalTrades: 150 } },
        ],
      },
      isLoading: false,
      error: null,
    };

    vi.mocked(useCopyTrading.useCopyTrading).mockReturnValue(mockCopyTrading);
    vi.mocked(useCopyTrading.useFollowedTraders).mockReturnValue({
        data: {
          traders: [
            { trader_id: 1, username: "Trader1", allocation_percentage: 50, status: "active" },
            { trader_id: 2, username: "Trader2", allocation_percentage: 25, status: "active" },
          ]
        },
        isLoading: false,
        error: null,
    } as any);
    vi.mocked(useCopyTrading.useCopyTradingStats).mockReturnValue({
        data: { totalProfit: 100, winRate: 60 },
        isLoading: false,
        error: null,
    } as any);
    vi.mocked(useCopyTrading.useFollowTrader).mockReturnValue({
        mutate: vi.fn(),
        isLoading: false,
    } as any);
    vi.mocked(useCopyTrading.useUnfollowTrader).mockReturnValue({
        mutate: vi.fn(),
        isLoading: false,
    } as any);
  });

  it("renders copy trading interface", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <CopyTrading />
      </QueryClientProvider>
    );

    expect(screen.getByText(/copy trading/i)).toBeInTheDocument();
  });

  it("displays available traders", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <CopyTrading />
      </QueryClientProvider>
    );

    expect(screen.getByText("Trader1")).toBeInTheDocument();
    expect(screen.getByText("Trader2")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    vi.mocked(useCopyTrading.useFollowedTraders).mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
    } as any);
    
    render(
      <QueryClientProvider client={queryClient}>
        <CopyTrading />
      </QueryClientProvider>
    );

    // Look for Skeleton or similar loading indicator
    expect(document.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("shows empty state when no traders available", () => {
    vi.mocked(useCopyTrading.useFollowedTraders).mockReturnValue({
        data: { traders: [] },
        isLoading: false,
        error: null,
    } as any);
    
    render(
      <QueryClientProvider client={queryClient}>
        <CopyTrading />
      </QueryClientProvider>
    );

    expect(screen.getByText(/no followed traders yet/i)).toBeInTheDocument();
  });
});
