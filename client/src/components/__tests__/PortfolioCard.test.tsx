import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { renderWithProviders, mockData } from "@/test/testUtils";
import { PortfolioCard } from "../PortfolioCard";

// Mock auth
vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    isAuthenticated: true,
    user: { id: "1" },
    token: "mock-token",
  }),
}));

// Mock the hook
vi.mock("@/hooks/useApi", () => ({
  usePortfolio: () => ({
    data: mockData.portfolio,
    isLoading: false,
    error: null,
  }),
}));

describe("PortfolioCard", () => {
  it("should render portfolio information", () => {
    renderWithProviders(<PortfolioCard title="Total" value="$10,000" icon={() => null} />);

    expect(screen.getByText(/portfolio|total/i)).toBeInTheDocument();
  });

  it("should display total value", () => {
    renderWithProviders(<PortfolioCard title="Total" value="$10,000" icon={() => null} />);

    expect(screen.getByText(/10,000|10000/)).toBeInTheDocument();
  });

  it("should display profit/loss", () => {
    renderWithProviders(<PortfolioCard title="Total" value="$10,000" change={5} icon={() => null} />);

    expect(screen.getByText(/5\.00%/)).toBeInTheDocument();
  });
});
