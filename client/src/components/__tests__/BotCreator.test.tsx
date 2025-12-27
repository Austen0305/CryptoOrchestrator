/**
 * BotCreator Component Tests
 * Tests the bot creation form and validation
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
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
    const user = userEvent.setup();
    render(
      <QueryClientProvider client={queryClient}>
        <BotCreator />
      </QueryClientProvider>
    );

    const submitButton = screen.getByRole("button", { name: /create|submit/i });
    await user.click(submitButton);

    // Should show validation errors
    await waitFor(() => {
      expect(screen.getByText(/name.*required/i)).toBeInTheDocument();
    });
  });

  it("allows filling bot creation form", async () => {
    const user = userEvent.setup();
    render(
      <QueryClientProvider client={queryClient}>
        <BotCreator />
      </QueryClientProvider>
    );

    const nameInput = screen.getByLabelText(/name/i);
    await user.type(nameInput, "Test Bot");

    expect(nameInput).toHaveValue("Test Bot");
  });
});
