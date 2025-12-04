// Types enforced; temporary ts-nocheck removed.
import { PortfolioCard } from "@/components/PortfolioCard";
import { PriceChart } from "@/components/PriceChart";
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

export default function Dashboard() {
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
  const ohlcvArray = ohlcvData?.data || (Array.isArray(ohlcvData) ? ohlcvData : []);
  
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
    <div className="space-y-4 md:space-y-6 w-full">
      {/* Real-time indicator */}
      {isRealTime && (
        <div className="flex items-center gap-2 text-sm text-green-500 bg-green-500/10 border border-green-500/20 px-4 py-2.5 rounded-lg shadow-sm">
          <div className="status-indicator h-2 w-2 bg-green-500 rounded-full"></div>
          <span className="font-medium">Live portfolio updates enabled</span>
        </div>
      )}
      
      {/* Enhanced Quick Stats */}
      <QuickStats
        totalValue={portfolio?.totalBalance || 0}
        change24h={portfolio?.profitLoss24h || 0}
        activeBots={status?.runningBots ?? runningBots ?? 0}
        totalTrades={trades?.length || 0}
      />

      {/* Trading Safety Status and Exchange Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        <TradingSafetyStatus />
        <ExchangeStatusIndicator />
      </div>

      {/* Recent Activity and Performance Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        <RecentActivity 
          activities={recentActivity || []} 
          maxItems={5}
        />
        {performanceSummary && (
          <PerformanceSummary
            winRate={performanceSummary.winRate || 0}
            avgProfit={performanceSummary.avgProfit || 0}
            totalProfit={performanceSummary.totalProfit || 0}
            bestTrade={performanceSummary.bestTrade || 0}
            worstTrade={performanceSummary.worstTrade || 0}
          />
        )}
      </div>

      {/* Main Trading Interface - Responsive layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 md:gap-8">
        {/* Chart Section - Takes more space on larger screens */}
        <div className="lg:col-span-8 space-y-6 md:space-y-8">
          <div className="h-[400px] md:h-[500px] lg:h-[600px] rounded-2xl border-2 border-card-border/70 bg-card shadow-2xl overflow-hidden" style={{ borderWidth: '2px' }}>
            <PriceChart
              pair="BTC/USD"
              currentPrice={47350}
              change24h={4.76}
              data={chartData}
            />
          </div>
          
          {/* Trading Recommendations - Full width on mobile, shown below chart */}
          <div className="lg:hidden">
            <TradingRecommendations />
          </div>
        </div>

        {/* Trading Controls - Side panel on desktop, bottom panel on mobile */}
        <div className="lg:col-span-4 space-y-4 md:space-y-6">
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
      <Suspense fallback={<div className="text-xs text-muted-foreground">Loading risk metrics…</div>}>
        <RiskSummary />
      </Suspense>

      {/* Risk Scenario Simulator */}
      <Suspense fallback={<div className="text-xs text-muted-foreground">Loading scenario simulator…</div>}>
        <RiskScenarioPanel />
      </Suspense>

      {/* Multi-Horizon VaR & ES */}
      <Suspense fallback={<div className="text-xs text-muted-foreground">Loading multi-horizon risk…</div>}>
        <MultiHorizonRiskPanel />
      </Suspense>

      {/* Trade History - Always full width */}
      <Card className="border-card-border shadow-md">
        <TradeHistory trades={trades || []} />
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
      {predictMutation.isSuccess && predictMutation.data && (
        <div className="mt-3 p-3 bg-muted rounded-lg border border-border">
          <pre className="text-xs max-h-48 overflow-auto font-mono">{JSON.stringify(predictMutation.data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
