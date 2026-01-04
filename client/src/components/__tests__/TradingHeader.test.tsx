/**
 * TradingHeader Component Tests
 * Tests header rendering, authentication states, and user interactions
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { TradingHeader } from "../TradingHeader";

// Mock auth hook
const mockLogout = vi.fn();
const mockUseAuth = vi.fn();

vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock toast hook
const mockToast = vi.fn();
vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

// Mock AuthModal
vi.mock("../AuthModal", () => ({
  AuthModal: ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => (
    isOpen ? <div data-testid="auth-modal">Auth Modal</div> : null
  ),
}));

// Mock NotificationCenter
vi.mock("../NotificationCenter", () => ({
  NotificationCenter: () => <div data-testid="notification-center">Notifications</div>,
}));

// Mock ThemeToggle
vi.mock("../ThemeToggle", () => ({
  ThemeToggle: () => <button data-testid="theme-toggle">Theme</button>,
}));

describe("TradingHeader", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    
    // Reset mocks
    vi.clearAllMocks();
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      user: null,
      logout: mockLogout,
    });
  });

  afterEach(() => {
    // Clean up event listeners
    window.removeEventListener("auth:expired", () => {});
  });

  it("renders header with logo and connection badge", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <TradingHeader balance={1000} connected={true} />
      </QueryClientProvider>
    );

    expect(screen.getByText("CryptoML")).toBeInTheDocument();
    expect(screen.getByTestId("badge-connection")).toBeInTheDocument();
  });

  it("displays connected state correctly", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <TradingHeader balance={1000} connected={true} />
      </QueryClientProvider>
    );

    const badge = screen.getByTestId("badge-connection");
    expect(badge).toHaveTextContent("Connected");
  });

  it("displays disconnected state correctly", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <TradingHeader balance={1000} connected={false} />
      </QueryClientProvider>
    );

    const badge = screen.getByTestId("badge-connection");
    expect(badge).toHaveTextContent("Disconnected");
  });

  it("displays balance correctly", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <TradingHeader balance={1234.56} connected={true} />
      </QueryClientProvider>
    );

    const balance = screen.getByTestId("text-balance");
    expect(balance).toHaveTextContent("$1,234.56");
  });

  it("formats large balances correctly", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <TradingHeader balance={1234567.89} connected={true} />
      </QueryClientProvider>
    );

    const balance = screen.getByTestId("text-balance");
    expect(balance).toHaveTextContent("$1,234,567.89");
  });

  it("shows login button when not authenticated", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      user: null,
      logout: mockLogout,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <TradingHeader balance={1000} connected={true} />
      </QueryClientProvider>
    );

    expect(screen.getByTestId("button-login")).toBeInTheDocument();
    expect(screen.queryByTestId("button-logout")).not.toBeInTheDocument();
  });

  it("shows logout button when authenticated", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { id: "1", username: "testuser" },
      logout: mockLogout,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <TradingHeader balance={1000} connected={true} />
      </QueryClientProvider>
    );

    expect(screen.getByTestId("button-logout")).toBeInTheDocument();
    expect(screen.queryByTestId("button-login")).not.toBeInTheDocument();
  });

  it("shows username when authenticated", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { id: "1", username: "testuser" },
      logout: mockLogout,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <TradingHeader balance={1000} connected={true} />
      </QueryClientProvider>
    );

    expect(screen.getByText("testuser")).toBeInTheDocument();
  });

  it("shows notification center when authenticated", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { id: "1", username: "testuser" },
      logout: mockLogout,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <TradingHeader balance={1000} connected={true} />
      </QueryClientProvider>
    );

    expect(screen.getByTestId("notification-center")).toBeInTheDocument();
  });

  it("does not show notification center when not authenticated", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      user: null,
      logout: mockLogout,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <TradingHeader balance={1000} connected={true} />
      </QueryClientProvider>
    );

    expect(screen.queryByTestId("notification-center")).not.toBeInTheDocument();
  });

  it("opens auth modal when login button is clicked", async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      user: null,
      logout: mockLogout,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <TradingHeader balance={1000} connected={true} />
      </QueryClientProvider>
    );

    const loginButton = screen.getByTestId("button-login");
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByTestId("auth-modal")).toBeInTheDocument();
    });
  });

  it("calls logout when logout button is clicked", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { id: "1", username: "testuser" },
      logout: mockLogout,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <TradingHeader balance={1000} connected={true} />
      </QueryClientProvider>
    );

    const logoutButton = screen.getByTestId("button-logout");
    fireEvent.click(logoutButton);

    expect(mockLogout).toHaveBeenCalledTimes(1);
  });

  it("shows settings button", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <TradingHeader balance={1000} connected={true} />
      </QueryClientProvider>
    );

    expect(screen.getByTestId("button-settings")).toBeInTheDocument();
  });

  it("shows theme toggle", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <TradingHeader balance={1000} connected={true} />
      </QueryClientProvider>
    );

    expect(screen.getByTestId("theme-toggle")).toBeInTheDocument();
  });

  it("opens auth modal on auth:expired event", async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      user: null,
      logout: mockLogout,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <TradingHeader balance={1000} connected={true} />
      </QueryClientProvider>
    );

    // Dispatch auth:expired event
    globalThis.dispatchEvent(new Event("auth:expired"));

    await waitFor(() => {
      expect(screen.getByTestId("auth-modal")).toBeInTheDocument();
    });

    expect(mockToast).toHaveBeenCalledWith({
      title: "Session expired",
      description: "Please log in again to continue.",
      variant: "destructive",
    });
  });

  it("closes auth modal when user becomes authenticated", async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      user: null,
      logout: mockLogout,
    });

    const { rerender } = render(
      <QueryClientProvider client={queryClient}>
        <TradingHeader balance={1000} connected={true} />
      </QueryClientProvider>
    );

    // Open modal
    const loginButton = screen.getByTestId("button-login");
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByTestId("auth-modal")).toBeInTheDocument();
    });

    // User becomes authenticated
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { id: "1", username: "testuser" },
      logout: mockLogout,
    });

    rerender(
      <QueryClientProvider client={queryClient}>
        <TradingHeader balance={1000} connected={true} />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.queryByTestId("auth-modal")).not.toBeInTheDocument();
    });
  });

  it("handles zero balance correctly", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <TradingHeader balance={0} connected={true} />
      </QueryClientProvider>
    );

    const balance = screen.getByTestId("text-balance");
    expect(balance).toHaveTextContent("$0");
  });

  it("handles negative balance correctly", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <TradingHeader balance={-100} connected={true} />
      </QueryClientProvider>
    );

    const balance = screen.getByTestId("text-balance");
    expect(balance).toHaveTextContent("-$100");
  });
});
