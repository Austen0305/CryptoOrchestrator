import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { ThemeProvider } from "@/components/ThemeProvider";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { AccessibilityProvider } from "@/components/AccessibilityProvider";
import { TradingModeProvider } from "@/contexts/TradingModeContext";
import { AppSidebar } from "@/components/AppSidebar";
import { TradingHeader } from "@/components/TradingHeader";
import { CommandPalette } from "@/components/CommandPalette";
import React, { Suspense } from 'react';
import { NotificationLiveRegion } from '@/components/NotificationLiveRegion';
const PerformanceMonitor = React.lazy(() => import('@/components/PerformanceMonitor').then(m => ({ default: m.PerformanceMonitor })));
import { useWebSocket } from "@/hooks/useWebSocket";
import { usePortfolio } from "@/hooks/useApi";
import { useExchangeStatus } from "@/hooks/useExchange";
import { useTranslation } from "react-i18next";
import { OfflineBanner } from "@/components/OfflineBanner";

// Lazy load all pages for better performance
const Login = React.lazy(() => import("@/pages/Login"));
const Register = React.lazy(() => import("@/pages/Register"));
const ForgotPassword = React.lazy(() => import("@/pages/ForgotPassword"));
const Dashboard = React.lazy(() => import("@/pages/Dashboard"));
const Bots = React.lazy(() => import("@/pages/Bots"));
const Markets = React.lazy(() => import("@/pages/Markets"));
const Analytics = React.lazy(() => import("@/pages/Analytics"));
const Strategies = React.lazy(() => import("@/pages/Strategies"));
const Licensing = React.lazy(() => import("@/pages/Licensing"));
const Billing = React.lazy(() => import("@/pages/Billing"));
const RiskManagement = React.lazy(() => import("@/pages/RiskManagement"));
const Settings = React.lazy(() => import("@/pages/Settings"));
const NotFound = React.lazy(() => import("@/pages/not-found"));

// Loading component for lazy-loaded routes
function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="flex flex-col items-center gap-2">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        <p className="text-sm text-muted-foreground">Loading...</p>
      </div>
    </div>
  );
}

function Router() {
  // Initialize WebSocket connection
  useWebSocket();

  return (
    <Suspense fallback={<PageLoader />}>
      <Switch>
        <Route path="/login" component={Login} />
        <Route path="/register" component={Register} />
        <Route path="/forgot-password" component={ForgotPassword} />
        <Route path="/" component={Dashboard} />
        <Route path="/dashboard" component={Dashboard} />
        <Route path="/bots" component={Bots} />
        <Route path="/markets" component={Markets} />
        <Route path="/analytics" component={Analytics} />
        <Route path="/strategies" component={Strategies} />
        <Route path="/licensing" component={Licensing} />
        <Route path="/billing" component={Billing} />
        <Route path="/risk" component={RiskManagement} />
        <Route path="/settings" component={Settings} />
        <Route component={NotFound} />
      </Switch>
    </Suspense>
  );
}

function AppContent() {
  const { data: portfolio } = usePortfolio("paper");
  const { isConnected } = useExchangeStatus();
  const { i18n } = useTranslation();

  return (
    <div className={`flex flex-col md:flex-row h-screen w-full bg-background text-foreground ${i18n.language === 'ar' ? 'rtl' : ''}`}>
      {/* Accessibility: Skip to content */}
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 bg-primary text-primary-foreground px-3 py-1 rounded">
        Skip to content
      </a>
      {/* Mobile header */}
      <header className="md:hidden sticky top-0 z-50 bg-background/80 backdrop-blur border-b">
        <div className="flex items-center justify-between p-3">
          <SidebarTrigger data-testid="button-sidebar-toggle" />
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">CryptoOrchestrator</span>
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          </div>
        </div>
      </header>

      {/* Desktop sidebar */}
      <aside className="hidden md:flex border-r">
        <AppSidebar />
      </aside>

      {/* Main content */}
      <div className="flex flex-col flex-1 min-h-0">
        <OfflineBanner />
        <TradingHeader
          balance={portfolio?.totalBalance || 100000}
          connected={isConnected}
        />

        {/* Status bar */}
        <div className="hidden md:flex items-center justify-between px-4 py-2 border-b text-sm">
          <div className="flex items-center gap-4">
            <SidebarTrigger data-testid="button-sidebar-toggle" />
            <span className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              {isConnected ? 'Exchange Connected' : 'Disconnected'}
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-blue-500" />
              ML Engine Active
            </span>
          </div>
          <span className="text-muted-foreground">
            {new Date().toLocaleString()}
          </span>
        </div>

        {/* Page content */}
        <main id="main-content" className="flex-1 overflow-auto p-4 md:p-6 bg-muted/10">
          <Router />
          <NotificationLiveRegion />
        </main>
      </div>
    </div>
  );
}

export default function App() {
  // Sidebar CSS variables moved to global stylesheet or can be applied via class
  const sidebarClass = "sidebar-vars"; // CSS vars applied via class

  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <AccessibilityProvider>
          <TradingModeProvider>
            <TooltipProvider>
              <ThemeProvider attribute="class" defaultTheme="dark">
                <SidebarProvider className={sidebarClass}>
                  <AppContent />
                  <CommandPalette />
                  <Suspense fallback={<div className="text-xs px-2 py-1">Loading perf…</div>}>
                    <PerformanceMonitor />
                  </Suspense>
                </SidebarProvider>
                <Toaster />
              </ThemeProvider>
            </TooltipProvider>
          </TradingModeProvider>
        </AccessibilityProvider>
      </ErrorBoundary>
      {/* React Query DevTools - Only in development */}
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-left" />}
    </QueryClientProvider>
  );
}
