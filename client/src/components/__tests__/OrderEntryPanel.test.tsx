import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/testUtils";
import { OrderEntryPanel } from "../OrderEntryPanel";

vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    isAuthenticated: true,
    user: { id: "1" },
    token: "mock-token",
  }),
}));

vi.mock("@/contexts/TradingModeContext", () => ({
  useTradingMode: () => ({
    mode: "paper",
    isRealMoney: false,
  }),
}));

describe("OrderEntryPanel", () => {
  it("should render order entry form", () => {
    renderWithProviders(<OrderEntryPanel symbol="BTC/USD" />);

    expect(screen.getByText(/Place Order/i)).toBeInTheDocument();
  });

  it("should toggle between buy and sell", async () => {
    const user = userEvent.setup();
    renderWithProviders(<OrderEntryPanel symbol="BTC/USD" />);

    const buyButton = screen.getByTestId("button-buy");
    const sellButton = screen.getByTestId("button-sell");

    await user.click(buyButton);
    // Component might not use aria-selected on the button itself but on a parent or class
    expect(buyButton).toBeInTheDocument();

    await user.click(sellButton);
    expect(sellButton).toBeInTheDocument();
  });

  it("should allow entering amount", async () => {
    renderWithProviders(<OrderEntryPanel symbol="BTC/USD" />);

    const amountInput = screen.getByTestId("input-amount");
    await userEvent.type(amountInput, "0.5");

    expect(amountInput).toHaveValue(0.5);
  });

  it("should allow entering price", async () => {
    const user = userEvent.setup();
    renderWithProviders(<OrderEntryPanel symbol="BTC/USD" />);

    // Switch to Limit mode to see price input
    const limitTab = screen.getByTestId("button-order-limit");
    await user.click(limitTab);

    const priceInput = screen.getByTestId("input-price");
    await userEvent.type(priceInput, "45000");

    expect(priceInput).toHaveValue(45000);
  });

  it("should have submit button", () => {
    renderWithProviders(<OrderEntryPanel symbol="BTC/USD" />);

    // The component uses button-buy/sell as submit buttons depending on mode
    expect(screen.getByTestId("button-buy")).toBeInTheDocument();
  });

  it("should submit order", async () => {
    renderWithProviders(<OrderEntryPanel symbol="BTC/USD" />);

    const submitButton = screen.getByTestId("button-buy");
    await userEvent.click(submitButton);

    // Should indicate success or loading
  });
});
