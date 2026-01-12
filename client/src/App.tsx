import { Switch, Route, useLocation } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
// React Query Devtools - commented out due to missing dependency
// Install with: npm install @tanstack/react-query-devtools --legacy-peer-deps
// Then uncomment: import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { ThemeProvider } from "@/components/ThemeProvider";
import { EnhancedErrorBoundary } from "@/components/EnhancedErrorBoundary";
import { AccessibilityProvider } from "@/components/AccessibilityProvider";
import { TradingModeProvider } from "@/contexts/TradingModeContext";
import { AuthProvider, useAuth } from "@/hooks/useAuth";
import { AppSidebar } from "@/components/AppSidebar";
import { TradingHeader } from "@/components/TradingHeader";
import { CommandPalette } from "@/components/CommandPalette";
import { KeyboardShortcutsModal } from "@/components/KeyboardShortcutsModal";
import { MobileMenu } from "@/components/MobileMenu";
import React, { Suspense, useEffect, useLayoutEffect, useState } from "react";
import { NotificationLiveRegion } from "@/components/NotificationLiveRegion";
const PerformanceMonitor = React.lazy(() =>
  import("@/components/PerformanceMonitor").then((m) => ({ default: m.PerformanceMonitor }))
);
import { useWebSocket } from "@/hooks/useWebSocket";
import { usePortfolio } from "@/hooks/useApi";
import { useExchangeStatus } from "@/hooks/useExchange";
import { useTokenRefresh } from "@/hooks/useTokenRefresh";
import { useTranslation } from "react-i18next";
import { OfflineBanner } from "@/components/OfflineBanner";
import { OfflineIndicator } from "@/components/OfflineIndicator";
import { CookieConsentBanner } from "@/components/CookieConsentBanner";
import type { Portfolio } from "@shared/types/api";
// Wagmi imports for Web3 wallet connections
import { WagmiProvider } from "wagmi";
import { wagmiConfig } from "@/lib/wagmiConfig";

// Lazy load all pages for better performance
const Landing = React.lazy(() => import("@/pages/Landing"));
const Login = React.lazy(() => import("@/pages/Login"));
const Register = React.lazy(() => import("@/pages/Register"));
const ForgotPassword = React.lazy(() => import("@/pages/ForgotPassword"));
const ResetPassword = React.lazy(() => import("@/pages/ResetPassword"));
const Dashboard = React.lazy(() => import("@/pages/Dashboard"));
const Bots = React.lazy(() => import("@/pages/Bots"));
const Markets = React.lazy(() => import("@/pages/Markets"));
const Analytics = React.lazy(() => import("@/pages/Analytics"));
const Strategies = React.lazy(() => import("@/pages/Strategies"));
const Licensing = React.lazy(() => import("@/pages/Licensing"));
const Billing = React.lazy(() => import("@/pages/Billing"));
const RiskManagement = React.lazy(() => import("@/pages/RiskManagement"));
const Settings = React.lazy(() => import("@/pages/Settings"));
const Wallet = React.lazy(() => import("@/components/Wallet").then((m) => ({ default: m.Wallet })));
const Staking = React.lazy(() =>
  import("@/components/Staking").then((m) => ({ default: m.Staking }))
);
const NotFound = React.lazy(() => import("@/pages/not-found"));
const TradingBots = React.lazy(() => import("@/pages/TradingBots"));
const DEXTrading = React.lazy(() => import("@/pages/DEXTrading"));
const Wallets = React.lazy(() => import("@/pages/Wallets"));
const Marketplace = React.lazy(() =>
  import("@/components/Marketplace").then((m) => ({ default: m.Marketplace }))
);
const TraderProfile = React.lazy(() =>
  import("@/components/TraderProfile").then((m) => ({ default: m.TraderProfile }))
);
const IndicatorMarketplace = React.lazy(() =>
  import("@/components/IndicatorMarketplace").then((m) => ({ default: m.IndicatorMarketplace }))
);
const AdvancedChartingTerminal = React.lazy(() =>
  import("@/components/AdvancedChartingTerminal").then((m) => ({ default: m.AdvancedChartingTerminal }))
);
const AdminAnalytics = React.lazy(() => import("@/pages/AdminAnalytics"));
const DeveloperAnalytics = React.lazy(() => import("@/pages/DeveloperAnalytics"));
const ProviderAnalytics = React.lazy(() => import("@/pages/ProviderAnalytics"));
const SLADashboard = React.lazy(() => import("@/pages/SLADashboard"));
const DashboardBuilder = React.lazy(() => import("@/pages/DashboardBuilder"));
const TraceVisualization = React.lazy(() => import("@/pages/TraceVisualization"));
const TreasuryDashboard = React.lazy(() => import("@/pages/TreasuryDashboard"));
const TaxReporting = React.lazy(() => import("@/pages/TaxReporting"));

// Loading component for lazy-loaded routes
import { OptimizedLoading } from "@/components/OptimizedLoading";

function PageLoader() {
  return <OptimizedLoading message="Loading page..." variant="spinner" size="md" />;
}

// Protected route component that redirects to landing if not authenticated
function ProtectedRoute({ component: Component, ...rest }: { component: React.ComponentType; [key: string]: any }) {
  const { isAuthenticated, isLoading } = useAuth();
  const [, setLocation] = useLocation();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      setLocation("/");
    }
  }, [isAuthenticated, isLoading, setLocation]);

  if (isLoading) {
    return <PageLoader />;
  }

  if (!isAuthenticated) {
    return null; // Will redirect in useEffect
  }

  return <Component />;
}

function Router() {
  // Initialize WebSocket connection only when authenticated
  // Note: useWebSocket hook must be called unconditionally per React rules
  useWebSocket();

  return (
    <Suspense fallback={<PageLoader />}>
      <Switch>
        {/* Public routes - accessible without login */}
        <Route path="/login" component={Login} />
        <Route path="/register" component={Register} />
        <Route path="/forgot-password" component={ForgotPassword} />
        <Route path="/reset-password" component={ResetPassword} />
        <Route path="/home" component={Landing} />
        <Route path="/" component={Landing} />

        {/* Protected routes - Redirect if not authenticated */}
        <Route path="/dashboard"><ProtectedRoute component={Dashboard} /></Route>
        <Route path="/bots"><ProtectedRoute component={Bots} /></Route>
        <Route path="/markets"><ProtectedRoute component={Markets} /></Route>
        <Route path="/analytics"><ProtectedRoute component={Analytics} /></Route>
        <Route path="/strategies"><ProtectedRoute component={Strategies} /></Route>
        <Route path="/licensing"><ProtectedRoute component={Licensing} /></Route>
        <Route path="/billing"><ProtectedRoute component={Billing} /></Route>
        <Route path="/risk"><ProtectedRoute component={RiskManagement} /></Route>
        <Route path="/settings"><ProtectedRoute component={Settings} /></Route>
        <Route path="/wallet"><ProtectedRoute component={Wallet} /></Route>
        <Route path="/staking"><ProtectedRoute component={Staking} /></Route>
        <Route path="/trading-bots"><ProtectedRoute component={TradingBots} /></Route>
        <Route path="/dex-trading"><ProtectedRoute component={DEXTrading} /></Route>
        <Route path="/wallets"><ProtectedRoute component={Wallets} /></Route>
        <Route path="/marketplace"><ProtectedRoute component={Marketplace} /></Route>
        <Route path="/marketplace/trader/:traderId"><ProtectedRoute component={TraderProfile} /></Route>
        <Route path="/indicators"><ProtectedRoute component={IndicatorMarketplace} /></Route>
        <Route path="/charting"><ProtectedRoute component={AdvancedChartingTerminal} /></Route>
        <Route path="/admin/analytics"><ProtectedRoute component={AdminAnalytics} /></Route>
        <Route path="/developer/analytics"><ProtectedRoute component={DeveloperAnalytics} /></Route>
        <Route path="/provider-analytics/:providerId?"><ProtectedRoute component={ProviderAnalytics} /></Route>
        <Route path="/sla-dashboard"><ProtectedRoute component={SLADashboard} /></Route>
        <Route path="/dashboard-builder"><ProtectedRoute component={DashboardBuilder} /></Route>
        <Route path="/traces"><ProtectedRoute component={TraceVisualization} /></Route>
        <Route path="/treasury"><ProtectedRoute component={TreasuryDashboard} /></Route>
        <Route path="/treasury/:walletId"><ProtectedRoute component={TreasuryDashboard} /></Route>
        <Route path="/tax-reporting"><ProtectedRoute component={TaxReporting} /></Route>
        <Route component={NotFound} />
      </Switch>
    </Suspense>
  );
}

function AppContent() {
  const { data: portfolio } = usePortfolio("paper") as { data: Portfolio | undefined };
  const { isConnected } = useExchangeStatus();
  const { i18n } = useTranslation();
  const { isAuthenticated } = useAuth();
  const [shortcutsModalOpen, setShortcutsModalOpen] = useState(false);

  // Automatically refresh tokens before expiration
  useTokenRefresh();

  // Listen for keyboard shortcuts modal open event
  useEffect(() => {
    const handleOpenShortcutsModal = () => {
      setShortcutsModalOpen(true);
    };
    window.addEventListener("open-keyboard-shortcuts-modal", handleOpenShortcutsModal);
    return () => {
      window.removeEventListener("open-keyboard-shortcuts-modal", handleOpenShortcutsModal);
    };
  }, []);

  // Manage landing-page body classes based on auth state
  useLayoutEffect(() => {
    const html = document.documentElement;
    const body = document.body;
    const root = document.getElementById("root");

    if (!isAuthenticated) {
      body.classList.add("landing-page-active");
      html.classList.add("landing-page-active");
      root?.classList.add("landing-page-active");
    } else {
      body.classList.remove("landing-page-active");
      html.classList.remove("landing-page-active");
      root?.classList.remove("landing-page-active");
    }

    return () => {
      body.classList.remove("landing-page-active");
      html.classList.remove("landing-page-active");
      root?.classList.remove("landing-page-active");
    };
  }, [isAuthenticated]);

  // If not authenticated, show landing page without sidebar/tabs
  // Use body scroll for landing page to avoid scroll reset issues
  if (!isAuthenticated) {
    return (
      <div
        className={`landing-page-container w-full bg-background text-foreground ${i18n.language === "ar" ? "rtl" : ""}`}
      >
        <Router />
        <NotificationLiveRegion />
      </div>
    );
  }

  // Authenticated users see the full app with sidebar and tabs
  return (
    <div
      className={`flex flex-col md:flex-row h-screen w-full bg-background text-foreground ${i18n.language === "ar" ? "rtl" : ""}`}
    >
      {/* Accessibility: Skip to content */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-primary text-primary-foreground px-4 py-2 rounded-md z-50 font-medium shadow-lg focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
        aria-label="Skip to main content"
      >
        Skip to content
      </a>
      {/* Mobile header */}
      <header className="md:hidden sticky top-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border/50 flex-shrink-0 shadow-sm">
        <div className="flex items-center justify-between p-3 md:p-4">
          <SidebarTrigger
            data-testid="button-sidebar-toggle"
            className="rounded-md hover:bg-accent/50 transition-colors"
          />
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold bg-gradient-to-r from-foreground to-foreground/80 bg-clip-text text-transparent">
              CryptoOrchestrator
            </span>
            <span
              className={`status-indicator w-2 h-2 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"}`}
            />
          </div>
        </div>
      </header>

      {/* Desktop sidebar */}
      <aside className="hidden md:flex border-r flex-shrink-0 h-full">
        <AppSidebar />
      </aside>

      {/* Main content */}
      <div className="flex flex-col flex-1 min-w-0 min-h-0 overflow-hidden">
        <OfflineBanner />
        <TradingHeader balance={portfolio?.totalBalance || 100000} connected={isConnected} />

        {/* Status bar */}
        <div className="hidden md:flex items-center justify-between px-4 md:px-6 py-2.5 border-b border-border/50 text-sm flex-shrink-0 bg-background/95 backdrop-blur-sm">
          <div className="flex items-center gap-4 md:gap-6">
            <SidebarTrigger
              data-testid="button-sidebar-toggle"
              className="rounded-md hover:bg-accent/50 transition-colors"
            />
            <span className="flex items-center gap-1.5 font-medium">
              <span
                className={`status-indicator w-2 h-2 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"}`}
              />
              {isConnected ? "Exchange Connected" : "Disconnected"}
            </span>
            <span className="flex items-center gap-1.5 font-medium text-muted-foreground">
              <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
              ML Engine Active
            </span>
          </div>
          <span className="text-muted-foreground font-medium text-xs md:text-sm">
            {new Date().toLocaleString()}
          </span>
        </div>

        {/* Page content - scrollable main area only */}
        <main
          id="main-content"
          className="flex-1 overflow-y-auto overflow-x-hidden px-4 md:px-6 lg:px-8 py-4 md:py-6 lg:py-8 bg-muted/5 min-h-0 pb-16 lg:pb-8"
        >
          <div className="max-w-7xl mx-auto w-full space-y-4 md:space-y-6">
            <Router />
          </div>
          <NotificationLiveRegion />
        </main>
      </div>
      {/* Mobile Navigation - Bottom bar for mobile devices */}
      <MobileMenu />
      <KeyboardShortcutsModal open={shortcutsModalOpen} onOpenChange={setShortcutsModalOpen} />
      {/* Cookie Consent Banner */}
      <CookieConsentBanner />
    </div>
  );
}

export default function App() {
  // Sidebar CSS variables moved to global stylesheet or can be applied via class
  const sidebarClass = "sidebar-vars"; // CSS vars applied via class

  return (
    <WagmiProvider config={wagmiConfig}>
      <QueryClientProvider client={queryClient}>
        <EnhancedErrorBoundary showDetails={import.meta.env.DEV}>
          <AuthProvider>
            <AccessibilityProvider>
              <TradingModeProvider>
                <TooltipProvider>
                  <ThemeProvider defaultTheme="dark">
                    <SidebarProvider className={`${sidebarClass} h-full w-full flex flex-col`}>
                      <AppContent />
                      <CommandPalette />
                      <OfflineIndicator />
                      <Suspense fallback={<div className="text-xs px-2 py-1">Loading perf…</div>}>
                        <PerformanceMonitor />
                      </Suspense>
                    </SidebarProvider>
                    <Toaster />
                  </ThemeProvider>
                </TooltipProvider>
              </TradingModeProvider>
            </AccessibilityProvider>
          </AuthProvider>
        </EnhancedErrorBoundary>
        {/* React Query DevTools - Only in development - Disabled until @tanstack/react-query-devtools is installed */}
        {/* {import.meta.env.DEV && ReactQueryDevtools && (
          <ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-left" />
        )} */}
      </QueryClientProvider>
    </WagmiProvider>
  );
}
