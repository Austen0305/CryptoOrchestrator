import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrategyEditor } from "../StrategyEditor";
import * as useStrategies from "@/hooks/useStrategies";

// Mock the hooks
vi.mock("@/hooks/useStrategies", () => ({
  useCreateStrategy: vi.fn(),
  useUpdateStrategy: vi.fn(),
}));

// Mock toast
vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
  toast: vi.fn(),
}));

describe("StrategyEditor", () => {
  let queryClient: QueryClient;
  let mockCreateStrategy: ReturnType<typeof useStrategies.useCreateStrategy>;
  let mockUpdateStrategy: ReturnType<typeof useStrategies.useUpdateStrategy>;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    mockCreateStrategy = {
      mutateAsync: vi.fn().mockResolvedValue({ id: "new-strategy-id" }),
      isPending: false,
      isError: false,
      error: null,
    } as any;

    mockUpdateStrategy = {
      mutateAsync: vi.fn().mockResolvedValue({ id: "updated-strategy-id" }),
      isPending: false,
      isError: false,
      error: null,
    } as any;

    vi.mocked(useStrategies.useCreateStrategy).mockReturnValue(mockCreateStrategy);
    vi.mocked(useStrategies.useUpdateStrategy).mockReturnValue(mockUpdateStrategy);
  });

  it("renders strategy editor form", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <StrategyEditor />
      </QueryClientProvider>
    );

    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /save/i })).toBeInTheDocument();
  });

  it("pre-fills form when editing existing strategy", () => {
    const strategy = {
      id: "strategy-1",
      name: "Test Strategy",
      description: "Test Description",
      strategy_type: "momentum",
      category: "technical",
      config: {},
    };

    render(
      <QueryClientProvider client={queryClient}>
        <StrategyEditor strategy={strategy as any} />
      </QueryClientProvider>
    );

    expect(screen.getByDisplayValue("Test Strategy")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Test Description")).toBeInTheDocument();
  });

  it("validates required fields before saving", async () => {
    const user = userEvent.setup();
    render(
      <QueryClientProvider client={queryClient}>
        <StrategyEditor />
      </QueryClientProvider>
    );

    const saveButton = screen.getByRole("button", { name: /save/i });
    await user.click(saveButton);

    // Should show validation error for empty name
    await waitFor(() => {
      expect(screen.getByText(/name.*required/i)).toBeInTheDocument();
    });
  });

  it("calls createStrategy when creating new strategy", async () => {
    const user = userEvent.setup();
    render(
      <QueryClientProvider client={queryClient}>
        <StrategyEditor />
      </QueryClientProvider>
    );

    await user.type(screen.getByLabelText(/name/i), "New Strategy");
    await user.type(screen.getByLabelText(/description/i), "Strategy Description");

    const saveButton = screen.getByRole("button", { name: /save/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockCreateStrategy.mutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "New Strategy",
          description: "Strategy Description",
        })
      );
    });
  });

  it("calls updateStrategy when updating existing strategy", async () => {
    const user = userEvent.setup();
    const strategy = {
      id: "strategy-1",
      name: "Original Name",
      description: "Original Description",
      strategy_type: "momentum",
      category: "technical",
      config: {},
    };

    render(
      <QueryClientProvider client={queryClient}>
        <StrategyEditor strategy={strategy as any} />
      </QueryClientProvider>
    );

    const nameInput = screen.getByDisplayValue("Original Name");
    await user.clear(nameInput);
    await user.type(nameInput, "Updated Name");

    const saveButton = screen.getByRole("button", { name: /save/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockUpdateStrategy.mutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          strategyId: "strategy-1",
          data: expect.objectContaining({
            name: "Updated Name",
          }),
        })
      );
    });
  });
});
