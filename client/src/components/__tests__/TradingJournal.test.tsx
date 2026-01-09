import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { TradingJournal } from "../TradingJournal";
import * as useApi from "@/hooks/useApi";

// Mock the hooks
vi.mock("@/hooks/useApi", () => ({
  useTrades: vi.fn(),
}));

// Mock toast
vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

// Mock date-fns
vi.mock("date-fns", () => ({
  format: (date: Date, formatStr: string) => {
    if (formatStr === "yyyy-MM-dd") {
      return date.toISOString().split("T")[0];
    }
    return date.toString();
  },
}));

describe("TradingJournal", () => {
  let queryClient: QueryClient;
  let mockTrades: any[];

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    mockTrades = [
      {
        id: "trade-1",
        timestamp: new Date("2025-01-01").toISOString(),
        pair: "BTC/USD",
        side: "buy",
        price: 50000,
        amount: 0.1,
        fee: 5,
        pnl: 100,
        pnlPercent: 2,
        botId: "bot-1",
        comment: "Test trade",
      },
      {
        id: "trade-2",
        timestamp: new Date("2025-01-02").toISOString(),
        pair: "ETH/USD",
        side: "sell",
        price: 3000,
        amount: 1,
        fee: 3,
        pnl: -50,
        pnlPercent: -1.67,
        botId: "bot-2",
        comment: "Another trade",
      },
    ];

    vi.mocked(useApi.useTrades).mockReturnValue({
      data: mockTrades,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as any);
  });

  it("renders trading journal with trade list", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <TradingJournal />
      </QueryClientProvider>
    );

    expect(screen.getByText(/trading journal/i)).toBeInTheDocument();
    expect(screen.getByText("BTC/USD")).toBeInTheDocument();
    expect(screen.getByText("ETH/USD")).toBeInTheDocument();
  });

  it("filters trades by search term", async () => {
    const user = userEvent.setup();
    render(
      <QueryClientProvider client={queryClient}>
        <TradingJournal />
      </QueryClientProvider>
    );

    const searchInput = screen.getByPlaceholderText(/search/i);
    await user.type(searchInput, "BTC");

    await waitFor(() => {
      expect(screen.getByText("BTC/USD")).toBeInTheDocument();
      expect(screen.queryByText("ETH/USD")).not.toBeInTheDocument();
    });
  });

  it("filters trades by strategy", async () => {
    const user = userEvent.setup();
    render(
      <QueryClientProvider client={queryClient}>
        <TradingJournal />
      </QueryClientProvider>
    );

    // Find the strategy filter trigger by its text content
    const trigger = screen.getByText("All Strategies").closest("button");
    if (!trigger) throw new Error("Could not find strategy filter trigger");
    await user.click(trigger);
    const option = await screen.findByText("bot-1");
    // Shadcn select option requires finding the item in the portal
    await user.click(option);

    await waitFor(() => {
      expect(screen.getByText("BTC/USD")).toBeInTheDocument();
      expect(screen.queryByText("ETH/USD")).not.toBeInTheDocument();
    });
  });

  it("shows loading state", () => {
    vi.mocked(useApi.useTrades).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    } as any);

    render(
      <QueryClientProvider client={queryClient}>
        <TradingJournal />
      </QueryClientProvider>
    );

    expect(screen.getByLabelText(/loading/i)).toBeInTheDocument();
  });

  it("shows empty state when no trades", () => {
    vi.mocked(useApi.useTrades).mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    render(
      <QueryClientProvider client={queryClient}>
        <TradingJournal />
      </QueryClientProvider>
    );

    expect(screen.getByText(/no trades/i)).toBeInTheDocument();
  });

  it("displays trade details correctly", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <TradingJournal />
      </QueryClientProvider>
    );

    // Check that trade data is displayed
    expect(screen.getByText("BTC/USD")).toBeInTheDocument();
    expect(screen.getByText("ETH/USD")).toBeInTheDocument();
    expect(screen.getByText(/buy/i)).toBeInTheDocument();
    expect(screen.getByText(/sell/i)).toBeInTheDocument();
  });
});
