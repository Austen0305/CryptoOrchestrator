import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Staking } from "../Staking";
import * as useStaking from "@/hooks/useStaking";

// Mock the hooks
vi.mock("@/hooks/useStaking", () => ({
  useStaking: vi.fn(),
  useStakingOptions: vi.fn(),
  useStakeAssets: vi.fn(),
  useUnstakeAssets: vi.fn(),
}));

// Mock toast
vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

describe("Staking", () => {
  let queryClient: QueryClient;
  let mockStaking: any;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    mockStaking = {
      data: {
        stakingPositions: [],
        stakingOptions: [
          { id: "option-1", name: "ETH Staking", apy: 5.5, minAmount: 0.1 },
          { id: "option-2", name: "BTC Staking", apy: 4.2, minAmount: 0.01 },
        ],
      },
      isLoading: false,
      error: null,
    };

    vi.mocked(useStaking.useStaking).mockReturnValue(mockStaking);
  });

  it("renders staking interface", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Staking />
      </QueryClientProvider>
    );

    expect(screen.getByText(/staking/i)).toBeInTheDocument();
  });

  it("displays staking options", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Staking />
      </QueryClientProvider>
    );

    expect(screen.getByText(/ETH Staking/i)).toBeInTheDocument();
    expect(screen.getByText(/BTC Staking/i)).toBeInTheDocument();
  });

  it("shows APY for staking options", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Staking />
      </QueryClientProvider>
    );

    expect(screen.getByText(/5.5%/i)).toBeInTheDocument();
    expect(screen.getByText(/4.2%/i)).toBeInTheDocument();
  });

  it("shows loading state", () => {
    vi.mocked(useStaking.useStaking).mockReturnValue({
      ...mockStaking,
      isLoading: true,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <Staking />
      </QueryClientProvider>
    );

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("shows empty state when no staking options", () => {
    vi.mocked(useStaking.useStaking).mockReturnValue({
      data: {
        stakingPositions: [],
        stakingOptions: [],
      },
      isLoading: false,
      error: null,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <Staking />
      </QueryClientProvider>
    );

    expect(screen.getByText(/no staking options/i)).toBeInTheDocument();
  });
});
