import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { renderWithProviders, mockData } from "@/test/testUtils";
import { BotControlPanel } from "../BotControlPanel";

// Mock the hooks
vi.mock("@/hooks/useApi", () => ({
  useBots: () => ({
    data: [{ ...mockData.bot, profitLoss: 100, totalTrades: 10 }],
    isLoading: false,
    error: null,
  }),
  useStatus: () => ({
    data: {
      krakenConnected: true,
      runningBots: 1,
    },
  }),
  useStartBot: () => ({
    mutateAsync: vi.fn().mockResolvedValue({}),
    isPending: false,
  }),
  useStopBot: () => ({
    mutateAsync: vi.fn().mockResolvedValue({}),
    isPending: false,
  }),
  useIntegrationsStatus: () => ({
    data: true,
    isLoading: false,
  }),
  useStartIntegrations: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
  useStopIntegrations: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
}));

vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    isAuthenticated: true,
    user: { id: "1" },
    token: "mock-token",
  }),
}));

vi.mock("@/hooks/useBotStatus", () => ({
  useBotStatus: () => ({
    runningBots: 1,
  }),
}));

const mockBots = [{ ...mockData.bot, profitLoss: 100, totalTrades: 10, status: "running" }];

describe("BotControlPanel", () => {
  it("should render bot list", () => {
    renderWithProviders(<BotControlPanel bots={[mockData.bot]} />);

    expect(screen.getByText(mockData.bot.name)).toBeInTheDocument();
  });

  it("should have start/stop buttons", () => {
    renderWithProviders(<BotControlPanel bots={mockBots} />);

    expect(screen.getByTestId(`switch-bot-${mockBots[0].id}`)).toBeInTheDocument();
  });
});
