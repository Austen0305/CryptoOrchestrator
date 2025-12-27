// Types enforced; temporary ts-nocheck removed.
import { PortfolioCard } from "@/components/PortfolioCard";
import { PriceChart } from "@/components/PriceChart";
import { EnhancedPriceChart } from "@/components/EnhancedPriceChart";
import { OrderEntryPanel } from "@/components/OrderEntryPanel";
import { OrderBook } from "@/components/OrderBook";
import { TradeHistory } from "@/components/TradeHistory";
import { TradingRecommendations } from "@/components/TradingRecommendations";
import { TradingJournal } from "@/components/TradingJournal";
import { PortfolioPieChart } from "@/components/PortfolioPieChart";
import { AITradingAssistant } from "@/components/AITradingAssistant";
import { ProfitCalendar } from "@/components/ProfitCalendar";
import { PriceAlerts } from "@/components/PriceAlerts";
import { SentimentAnalysis } from "@/components/SentimentAnalysis";
import { ArbitrageDashboard } from "@/components/ArbitrageDashboard";
import { ExchangeStatusIndicator } from "@/components/ExchangeStatusIndicator";
import { DashboardSkeleton } from "@/components/LoadingSkeletons";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { EmptyState } from "@/components/EmptyState";
import { TradingSafetyStatus } from "@/components/TradingSafetyStatus";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import React, { Suspense } from 'react';
const RiskSummary = React.lazy(() => import('@/components/RiskSummary').then(m => ({ default: m.RiskSummary })));
const RiskScenarioPanel = React.lazy(() => import('@/components/RiskScenarioPanel').then(m => ({ default: m.RiskScenarioPanel })));
const MultiHorizonRiskPanel = React.lazy(() => import('@/components/MultiHorizonRiskPanel').then(m => ({ default: m.MultiHorizonRiskPanel })));
import { usePortfolio, useTrades, useStatus, useRecentActivity, usePerformanceSummary } from "@/hooks/useApi";
import type { Portfolio, Trade } from "@shared/schema";
import { useBotStatus } from "@/hooks/useBotStatus";
import { useState } from 'react';
import { generateOhlcv } from '@/lib/ohlcv';
import { useAuth } from '@/hooks/useAuth';
import { useTradingMode } from "@/contexts/TradingModeContext";
import { TradingModeSwitcher } from "@/components/TradingModeSwitcher";
import { Wallet, TrendingUp, Activity, DollarSign, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { useOrderBook } from "@/hooks/useOrderBook";
import { useQuery, useMutation } from "@tanstack/react-query";
import { marketApi, integrationsApi } from "@/lib/api";
import { QuickStats, RecentActivity, PerformanceSummary } from "@/components/DashboardEnhancements";
import { EnhancedErrorBoundary } from "@/components/EnhancedErrorBoundary";
import logger from "@/lib/logger";

function DashboardContent() {
  const { mode, isRealMoney, isPaperTrading } = useTradingMode();
  const { data: portfolio, isLoading: portfolioLoading, isRealTime } = usePortfolio(mode);
  const { data: trades, isLoading: tradesLoading } = useTrades(undefined, mode);
  const { data: status } = useStatus();
  const { runningBots } = useBotStatus();
  const { data: recentActivity, isLoading: activityLoading } = useRecentActivity(10);
  const { data: performanceSummary, isLoading: performanceLoading } = usePerformanceSummary(mode);

  // Default trading pair - can be made configurable
  const [selectedPair] = useState("BTC/USD");
  
  // Fetch real order book data
  const { data: orderBook, isLoading: orderBookLoading } = useOrderBook(selectedPair, true, 1000);
  
  // Fetch OHLCV data for chart
  const { data: ohlcvData } = useQuery({
    queryKey: ["ohlcv", selectedPair, "1h"],
    queryFn: () => marketApi.getOHLCV(selectedPair, "1h", 100),
    enabled: !!selectedPair,
    refetchInterval: 60000, // Refresh every minute
  });
  
  // Transform OHLCV to chart format or use fallback
  interface OhlcvCandle {
    timestamp?: string;
    close?: number;
    [index: number]: number | undefined;
  }

  // OHLCV API returns { pair, timeframe, data: [...] }, so we need to access .data
  const ohlcvArray = (ohlcvData && typeof ohlcvData === 'object' && 'data' in ohlcvData && Array.isArray(ohlcvData.data)) 
    ? ohlcvData.data 
    : (Array.isArray(ohlcvData) ? ohlcvData : []);
  
  const chartData = ohlcvArray?.map((candle: OhlcvCandle | number[]) => {
    if (Array.isArray(candle)) {
      // Array format: [timestamp, open, high, low, close, volume]
      return {
        time: new Date((candle[0] || 0) * 1000).toLocaleTimeString(),
        price: candle[4] || 0,
      };
    } else {
      // Object format
      return {
        time: new Date(candle.timestamp || Date.now()).toLocaleTimeString(),
        price: candle.close || 0,
      };
    }
  }) || generateOhlcv(24, 47350, 60_000).map((candle: { timestamp: string; close: number }) => ({
    time: new Date(candle.timestamp).toLocaleTimeString(),
    price: candle.close,
  }));

  if (portfolioLoading || tradesLoading) {
    return (
      <div className="space-y-6 w-full">
        <DashboardSkeleton />
      </div>
    );
  }

  return (
    <div className="space-y-4 md:space-y-6 w-full animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold" data-testid="dashboard">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Overview of your blockchain trading activity and portfolio
        </p>
      </div>
      
      {/* Real-time indicator */}
      {isRealTime && (
        <div className="flex items-center gap-2 text-sm text-green-500 bg-green-500/10 border border-green-500/20 px-4 py-2.5 rounded-lg shadow-sm animate-pulse-glow">
          <div className="status-indicator h-2 w-2 bg-green-500 rounded-full"></div>
          <span className="font-medium">Live portfolio updates enabled</span>
        </div>
      )}
      
      {/* Enhanced Quick Stats */}
      <QuickStats
        totalValue={(portfolio as Portfolio | undefined)?.totalBalance || 0}
        change24h={(portfolio as Portfolio | undefined)?.profitLoss24h || 0}
        activeBots={status?.runningBots ?? runningBots ?? 0}
        totalTrades={(trades && Array.isArray(trades) ? trades.length : 0)}
      />

      {/* Trading Mode Switcher */}
      <div className="flex justify-center w-full">
        <div className="w-full sm:w-auto">
          <TradingModeSwitcher />
        </div>
      </div>

      {/* Trading Safety Status and Exchange Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        <TradingSafetyStatus />
        <ExchangeStatusIndicator />
      </div>

      {/* Recent Activity and Performance Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        <RecentActivity 
          activities={(recentActivity && Array.isArray(recentActivity) 
            ? recentActivity.map(activity => ({
                id: activity.id || '',
                type: (activity.type as "trade" | "bot" | "alert" | "system") || "system",
                message: (activity as { message?: string; description?: string }).message || (activity as { description?: string }).description || '',
                timestamp: activity.timestamp || '',
                status: (activity as { status?: "success" | "warning" | "error" }).status,
              }))
            : [])} 
          maxItems={5}
        />
        {performanceSummary && typeof performanceSummary === 'object' ? (
          <PerformanceSummary
            winRate={((performanceSummary as { winRate?: number }).winRate ?? 0) as number}
            avgProfit={((performanceSummary as { avgProfit?: number }).avgProfit ?? 0) as number}
            totalProfit={((performanceSummary as { totalProfit?: number }).totalProfit ?? 0) as number}
            bestTrade={((performanceSummary as { bestTrade?: number }).bestTrade ?? 0) as number}
            worstTrade={((performanceSummary as { worstTrade?: number }).worstTrade ?? 0) as number}
          />
        ) : null}
      </div>

      {/* Main Trading Interface - Responsive layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 md:gap-6 lg:gap-8">
        {/* Chart Section - Takes more space on larger screens */}
        <div className="lg:col-span-8 space-y-4 md:space-y-6 lg:space-y-8">
          <div className="h-[300px] sm:h-[400px] md:h-[500px] lg:h-[600px] rounded-xl md:rounded-2xl border-2 border-card-border/70 bg-card shadow-xl md:shadow-2xl overflow-hidden glass-premium hover-lift">
            {/* Use EnhancedPriceChart if available, fallback to PriceChart */}
            {typeof window !== 'undefined' && (window as typeof window & { __USE_ENHANCED_CHART?: boolean }).__USE_ENHANCED_CHART !== false ? (
              <EnhancedPriceChart
                pair="BTC/USD"
                currentPrice={47350}
                change24h={4.76}
                data={chartData}
                live={true}
              />
            ) : (
              <PriceChart
                pair="BTC/USD"
                currentPrice={47350}
                change24h={4.76}
                data={chartData}
              />
            )}
          </div>
          
          {/* Trading Recommendations - Full width on mobile, shown below chart */}
          <div className="lg:hidden">
            <TradingRecommendations />
          </div>
        </div>

        {/* Trading Controls - Side panel on desktop, bottom panel on mobile */}
        <div className="lg:col-span-4 space-y-4 md:space-y-6 pb-16 lg:pb-0">
          <OrderEntryPanel />
          {/* Quick Predict integration panel */}
          <Card className="border-card-border">
            <CardHeader>
              <CardTitle className="text-base font-semibold">Quick Predict (Freqtrade + Jesse)</CardTitle>
            </CardHeader>
            <CardContent>
              <PredictPanel />
            </CardContent>
          </Card>
          <Card className="border-card-border overflow-hidden">
            {orderBookLoading ? (
              <div className="p-4">
                <LoadingSkeleton variant="chart" className="h-[200px]" />
              </div>
            ) : orderBook ? (
              <OrderBook 
                bids={orderBook.bids} 
                asks={orderBook.asks} 
                spread={orderBook.spread} 
              />
            ) : (
              <div className="p-4">
                <EmptyState
                  icon={Activity}
                  title="No order book data available"
                  description="Order book data will appear here once market data is loaded."
                />
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Trading Recommendations - Shown on desktop */}
      <div className="hidden lg:block">
        <TradingRecommendations />
      </div>

      {/* Risk Summary (lazy loaded) */}
      <Suspense fallback={<LoadingSkeleton variant="card" className="h-64" />}>
        <RiskSummary />
      </Suspense>

      {/* Risk Scenario Simulator */}
      <Suspense fallback={<LoadingSkeleton variant="card" className="h-64" />}>
        <RiskScenarioPanel />
      </Suspense>

      {/* Multi-Horizon VaR & ES */}
      <Suspense fallback={<LoadingSkeleton variant="card" className="h-64" />}>
        <MultiHorizonRiskPanel />
      </Suspense>

      {/* Trade History - Always full width */}
      <Card className="border-card-border shadow-md">
        <TradeHistory trades={(trades && Array.isArray(trades) ? trades.map((t: any) => ({
          id: t.id || '',
          pair: t.pair || '',
          type: t.type || 'market',
          side: t.side || 'buy',
          amount: t.amount || 0,
          price: t.price || 0,
          total: t.total || (t.amount || 0) * (t.price || 0),
          timestamp: t.timestamp || t.executed_at || new Date().toISOString(),
          status: t.status || 'completed',
          mode: t.mode || mode,
          exchange: t.exchange,
          pnl: t.pnl,
        })) : [])} />
      </Card>

      {/* New Features Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        {/* Trading Journal */}
        <TradingJournal />
        
        {/* Portfolio Pie Chart */}
        <PortfolioPieChart />
      </div>

      {/* AI Assistant and Profit Calendar */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        {/* AI Trading Assistant */}
        <div className="h-[500px] md:h-[600px]">
          <AITradingAssistant />
        </div>
        
        {/* Profit Calendar */}
        <ProfitCalendar />
      </div>

      {/* Price Alerts and Sentiment Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        <PriceAlerts />
        <SentimentAnalysis symbol="BTC" autoRefresh={true} />
      </div>

      {/* Arbitrage Dashboard */}
      <div>
        <ArbitrageDashboard />
      </div>
    </div>
  );
}

function PredictPanel() {
  const { isAuthenticated } = useAuth();
  const { toast } = useToast();

  // Minimal synthetic sample OHLCV data for predict endpoint
  const sampleData = generateOhlcv(60, 47350, 60_000);

  const predictMutation = useMutation({
    mutationFn: async () => {
      if (!isAuthenticated) {
        throw new Error('You must be logged in to run predictions.');
      }
      return await integrationsApi.predict({
        symbol: 'BTC/USDT',
        timeframe: '1h',
        data: sampleData
      });
    },
    onSuccess: (data) => {
      toast({
        title: 'Prediction complete',
        description: 'Ensemble prediction generated successfully.',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Prediction failed',
        description: error.message || 'Failed to generate prediction. Please try again.',
        variant: 'destructive',
      });
    },
  });

  return (
    <div className="space-y-3">
      <Button 
        onClick={() => predictMutation.mutate()} 
        disabled={predictMutation.isPending || !isAuthenticated}
        className="w-full font-semibold"
        variant={isAuthenticated ? "default" : "secondary"}
      >
        {predictMutation.isPending ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Predicting…
          </>
        ) : !isAuthenticated ? (
          'Login to Predict'
        ) : (
          'Run Prediction'
        )}
      </Button>
      {predictMutation.isError && (
        <div className="mt-3 p-3 bg-destructive/10 rounded-lg border border-destructive/50">
          <p className="text-sm text-destructive">
            {predictMutation.error instanceof Error ? predictMutation.error.message : 'Failed to generate prediction'}
          </p>
        </div>
      )}
      {predictMutation.isSuccess && predictMutation.data ? (
        <div className="mt-3 p-3 bg-muted rounded-lg border border-border">
          <pre className="text-xs max-h-48 overflow-auto font-mono">{JSON.stringify(predictMutation.data as Record<string, unknown>, null, 2)}</pre>
        </div>
      ) : null}
    </div>
  );
}

export default function Dashboard() {
  return (
    <EnhancedErrorBoundary
      onError={(error, errorInfo) => {
        logger.error("Dashboard error", { error, errorInfo });
        // Error reporting would go here (Sentry, etc.)
      }}
    >
      <DashboardContent />
    </EnhancedErrorBoundary>
  );
}
