/**
 * Wallet Component Tests
 * Tests wallet balance display and transaction history
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Wallet } from "../Wallet";

// Mock API
vi.mock("@/hooks/useWallet", () => ({
  useWallet: () => ({
    data: {
      address: "0x1234...5678",
      balance: "1000.0",
      chain: "ethereum",
    },
    isLoading: false,
  }),
  useWalletTransactions: () => ({
    data: [
      {
        id: "1",
        type: "deposit",
        amount: "100",
        timestamp: new Date().toISOString(),
      },
    ],
    isLoading: false,
  }),
  useDeposit: () => ({ mutate: vi.fn() }),
  useWithdraw: () => ({ mutate: vi.fn() }),
  useTransfer: () => ({ mutate: vi.fn() }),
}));

// Mock auth
vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    isAuthenticated: true,
    user: { id: "1" },
  }),
}));

describe("Wallet", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
  });

  it("renders wallet balance", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Wallet />
      </QueryClientProvider>
    );

    expect(screen.getAllByText(/Wallet Balance/i)[0]).toBeInTheDocument();
  });

  it("displays transaction history", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Wallet />
      </QueryClientProvider>
    );

    expect(screen.getAllByText(/Transaction History/i)[0]).toBeInTheDocument();
  });
});
