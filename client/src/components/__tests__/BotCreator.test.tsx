/**
 * BotCreator Component Tests
 * Tests the bot creation form and validation
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderWithProviders } from "@/test/testUtils";
import { BotCreator } from "../BotCreator";

// Mock API
vi.mock("@/hooks/useApi", () => ({
  useCreateBot: () => ({
    mutate: vi.fn(),
    isLoading: false,
    error: null,
  }),
  useStrategies: () => ({
    data: [
      { id: "1", name: "Momentum", description: "Momentum strategy" },
      { id: "2", name: "Mean Reversion", description: "Mean reversion strategy" },
    ],
    isLoading: false,
  }),
  useMarkets: () => ({
    data: [
      { symbol: "BTC/USD", base: "BTC", quote: "USD" },
      { symbol: "ETH/USD", base: "ETH", quote: "USD" },
    ],
    isLoading: false,
  }),
}));

// Mock auth
vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    isAuthenticated: true,
    user: { id: "1", email: "test@example.com" },
  }),
}));

vi.mock("@/contexts/TradingModeContext", () => ({
  useTradingMode: () => ({
    mode: "paper",
    isRealMoney: false,
  }),
}));

describe("BotCreator", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
  });

  it("renders bot creation form", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <BotCreator />
      </QueryClientProvider>
    );

    expect(screen.getByText(/create.*bot/i)).toBeInTheDocument();
  });

  it("shows validation errors for empty form", async () => {
    renderWithProviders(<BotCreator />);
    
    // Click button to open dialog and wait for it to appear
    await userEvent.click(screen.getByRole("button", { name: /create.*trading.*bot/i }));
    await screen.findByLabelText(/bot name/i);
    
    // The submit button inside the dialog has aria-label "Create trading bot"
    const submitBtn = await screen.findByRole("button", { name: /create.*trading.*bot/i });
    
    // Sometimes userEvent.click doesn't trigger the form submit in tests
    // so we'll use fireEvent as a fallback if needed, but let's try click first
    // but ensure we wait for the validation messages specifically
    await userEvent.click(submitBtn);

    await waitFor(() => {
      // Look for any text indicating a requirement or error
      // using a more flexible matcher function
      const hasError = screen.queryByText((content) => {
        return /required|invalid|must be/i.test(content);
      });
      expect(hasError).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it("allows filling bot creation form", async () => {
    renderWithProviders(<BotCreator />);
    
    // Click button to open dialog
    await userEvent.click(screen.getByRole("button", { name: /create.*trading.*bot/i }));

    const nameInput = screen.getByLabelText(/bot name/i);
    await userEvent.type(nameInput, "My Test Bot");

    expect(nameInput).toHaveValue("My Test Bot");
  });
});
