import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { ThemeProvider } from "@/components/ThemeProvider";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { AppSidebar } from "@/components/AppSidebar";
import { TradingHeader } from "@/components/TradingHeader";
import { CommandPalette } from "@/components/CommandPalette";
import React, { Suspense } from 'react';
import { NotificationLiveRegion } from '@/components/NotificationLiveRegion';
const PerformanceMonitor = React.lazy(() => import('@/components/PerformanceMonitor').then(m => ({ default: m.PerformanceMonitor })));
import { useWebSocket } from "@/hooks/useWebSocket";
import { usePortfolio } from "@/hooks/useApi";
import { useExchangeStatus } from "@/hooks/useExchange";
import NotFound from "@/pages/not-found";
import Dashboard from "@/pages/Dashboard";
import Bots from "@/pages/Bots";
import Markets from "@/pages/Markets";
import Analytics from "@/pages/Analytics";
import RiskManagement from "@/pages/RiskManagement";
import Settings from "@/pages/Settings";
import { useTranslation } from "react-i18next";
import { OfflineBanner } from "@/components/OfflineBanner";

function Router() {
  // Initialize WebSocket connection
  useWebSocket();

  return (
    <Switch>
      <Route path="/" component={Dashboard} />
      <Route path="/bots" component={Bots} />
      <Route path="/markets" component={Markets} />
      <Route path="/analytics" component={Analytics} />
      <Route path="/risk" component={RiskManagement} />
      <Route path="/settings" component={Settings} />
      <Route component={NotFound} />
    </Switch>
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
        <TooltipProvider>
          <ThemeProvider defaultTheme="dark">
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
      </ErrorBoundary>
    </QueryClientProvider>
  );
}
