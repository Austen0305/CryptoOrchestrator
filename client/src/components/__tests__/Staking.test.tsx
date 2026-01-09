import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Staking } from "../Staking";
import * as useStaking from "@/hooks/useStaking";

// Mock the hooks
vi.mock("@/hooks/useStaking", () => ({
  useStakingOptions: vi.fn(),
  useStakeAssets: vi.fn(),
  useUnstakeAssets: vi.fn(),
  useMyStakes: vi.fn(),
  useStake: vi.fn(),
  useUnstake: vi.fn(),
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
          { id: "option-1", asset: "ETH", apy: 5.5, min_amount: 0.1, description: "Ethereum Staking" },
          { id: "option-2", asset: "BTC", apy: 4.2, min_amount: 0.01, description: "Bitcoin Staking" },
        ],
      },
      isLoading: false,
      error: null,
    };

    vi.mocked(useStaking.useStakingOptions).mockReturnValue({
        data: { options: mockStaking.data.stakingOptions },
        isLoading: false,
        isSuccess: true,
        status: 'success',
        error: null,
    } as any);
    vi.mocked(useStaking.useMyStakes).mockReturnValue({
        data: { stakes: [] },
        isLoading: false,
        isSuccess: true,
        status: 'success',
        error: null,
    } as any);
    vi.mocked(useStaking.useStake).mockReturnValue({
        mutate: vi.fn(),
        mutateAsync: vi.fn().mockResolvedValue({}),
        isPending: false,
        isSuccess: false,
        status: 'idle',
    } as any);
    vi.mocked(useStaking.useUnstake).mockReturnValue({
        mutate: vi.fn(),
        mutateAsync: vi.fn().mockResolvedValue({}),
        isPending: false,
        isSuccess: false,
        status: 'idle',
    } as any);
  });

  it("renders staking interface", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Staking />
      </QueryClientProvider>
    );

    expect(screen.getByText(/staking rewards/i)).toBeInTheDocument();
  });

  it("displays staking options", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Staking />
      </QueryClientProvider>
    );

    expect(screen.getAllByText(/ETH/)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/BTC/)[0]).toBeInTheDocument();
  });

  it("shows APY for staking options", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Staking />
      </QueryClientProvider>
    );

    expect(screen.getByText(/5\.50%/i)).toBeInTheDocument();
    expect(screen.getByText(/4\.20%/i)).toBeInTheDocument();
  });

  it("shows loading state", () => {
    vi.mocked(useStaking.useStakingOptions).mockReturnValue({
        data: undefined,
        isLoading: true,
        isSuccess: false,
        status: 'pending',
        error: null,
    } as any);

    render(
      <QueryClientProvider client={queryClient}>
        <Staking />
      </QueryClientProvider>
    );

    // Look for the animate-pulse class container
    const skeleton = document.querySelector('.animate-pulse');
    expect(skeleton).toBeInTheDocument();
  });

  it("shows empty state when no staking options", () => {
    vi.mocked(useStaking.useStakingOptions).mockReturnValue({
        data: { options: [] },
        isLoading: false,
        isSuccess: true,
        status: 'success',
        error: null,
    } as any);

    render(
      <QueryClientProvider client={queryClient}>
        <Staking />
      </QueryClientProvider>
    );

    expect(screen.getByText(/no.*options/i)).toBeInTheDocument();
  });
});
