// Types enforced; temporary ts-nocheck removed.
import { PortfolioCard } from "@/components/PortfolioCard";
import { PriceChart } from "@/components/PriceChart";
import { OrderEntryPanel } from "@/components/OrderEntryPanel";
import { OrderBook } from "@/components/OrderBook";
import { TradeHistory } from "@/components/TradeHistory";
import { TradingRecommendations } from "@/components/TradingRecommendations";
import React, { Suspense } from 'react';
const RiskSummary = React.lazy(() => import('@/components/RiskSummary').then(m => ({ default: m.RiskSummary })));
const RiskScenarioPanel = React.lazy(() => import('@/components/RiskScenarioPanel').then(m => ({ default: m.RiskScenarioPanel })));
const MultiHorizonRiskPanel = React.lazy(() => import('@/components/MultiHorizonRiskPanel').then(m => ({ default: m.MultiHorizonRiskPanel })));
import { usePortfolio, useTrades, useStatus } from "@/hooks/useApi";
import { useBotStatus } from "@/hooks/useBotStatus";
import { useState } from 'react';
import { generateOhlcv } from '@/lib/ohlcv';
import { useAuth } from '@/hooks/useAuth';
import { Wallet, TrendingUp, Activity, DollarSign, Loader2 } from "lucide-react";

export default function Dashboard() {
  const { data: portfolio, isLoading: portfolioLoading } = usePortfolio("paper");
  const { data: trades, isLoading: tradesLoading } = useTrades();
  const { data: status } = useStatus();
  const { runningBots } = useBotStatus();

  const chartData = [
    { time: "00:00", price: 45200 },
    { time: "04:00", price: 45800 },
    { time: "08:00", price: 45300 },
    { time: "12:00", price: 46200 },
    { time: "16:00", price: 46800 },
    { time: "20:00", price: 47100 },
    { time: "24:00", price: 47350 },
  ];

  const mockBids = [
    { price: 47340, amount: 0.5234, total: 24765 },
    { price: 47335, amount: 1.2341, total: 58405 },
    { price: 47330, amount: 0.8921, total: 42207 },
    { price: 47325, amount: 2.1234, total: 100489 },
    { price: 47320, amount: 0.4567, total: 21608 },
  ];

  const mockAsks = [
    { price: 47355, amount: 0.6234, total: 29521 },
    { price: 47360, amount: 1.4321, total: 67828 },
    { price: 47365, amount: 0.7821, total: 37039 },
    { price: 47370, amount: 2.3421, total: 110952 },
    { price: 47375, amount: 0.5421, total: 25682 },
  ];

  if (portfolioLoading || tradesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading dashboard...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Portfolio Summary Cards - Grid layout that adapts to screen size */}
      <div className="grid grid-cols-2 sm:grid-cols-2 xl:grid-cols-4 gap-3 md:gap-4">
        <PortfolioCard
          title="Total Balance"
          value={portfolio ? `$${portfolio.totalBalance.toLocaleString()}` : "$0"}
          change={portfolio?.profitLoss24h || 0}
          icon={Wallet}
          className="min-w-[140px]"
        />
        <PortfolioCard
          title="24h P&L"
          value={portfolio ? `$${portfolio.profitLoss24h.toLocaleString()}` : "$0"}
          change={portfolio?.profitLoss24h || 0}
          icon={TrendingUp}
          className="min-w-[140px]"
        />
        <PortfolioCard
          title="Active Bots"
          value={(status?.runningBots ?? runningBots ?? 0).toString()}
          icon={Activity}
          subtitle={status?.krakenConnected ? "Kraken Connected" : "Kraken Disconnected"}
          className="min-w-[140px]"
        />
        <PortfolioCard
          title="Total P&L"
          value={portfolio ? `$${portfolio.profitLossTotal.toLocaleString()}` : "$0"}
          change={portfolio?.profitLossTotal || 0}
          icon={DollarSign}
          className="min-w-[140px]"
        />
      </div>

      {/* Main Trading Interface - Responsive layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Chart Section - Takes more space on larger screens */}
        <div className="lg:col-span-8 space-y-4">
          <div className="h-[400px] md:h-[600px] rounded-lg border bg-card">
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
        <div className="lg:col-span-4 space-y-4">
          <OrderEntryPanel />
          {/* Quick Predict integration panel */}
          <div className="rounded-lg border bg-card p-4">
            <h3 className="font-semibold mb-2">Quick Predict (Freqtrade + Jesse)</h3>
            <PredictPanel />
          </div>
          <div className="rounded-lg border bg-card overflow-hidden">
            <OrderBook bids={mockBids} asks={mockAsks} spread={15} />
          </div>
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
      <div className="rounded-lg border bg-card overflow-hidden">
        <TradeHistory trades={trades || []} />
      </div>
    </div>
  );
}

function PredictPanel() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const { isAuthenticated } = useAuth();

  // Minimal synthetic sample OHLCV data for predict endpoint
  const sampleData = generateOhlcv(60, 47350, 60_000);

  async function callPredict() {
    if (!isAuthenticated) {
      setResult({ error: 'You must be logged in to run predictions.' });
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const token = localStorage.getItem('auth_token');
      const resp = await fetch('/api/integrations/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ symbol: 'BTC/USDT', timeframe: '1h', data: sampleData })
      });
      if (!resp.ok) {
        const text = await resp.text();
        setResult({ error: `Request failed (${resp.status}): ${text}` });
        return;
      }
      const data = await resp.json();
      setResult(data);
    } catch (e) {
      setResult({ error: String(e) });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <button onClick={callPredict} className="btn mr-2" disabled={loading || !isAuthenticated}>
        {loading ? 'Predicting…' : !isAuthenticated ? 'Login to Predict' : 'Predict'}
      </button>
      {result && (
        <pre className="mt-2 text-sm max-h-48 overflow-auto bg-muted p-2 rounded">{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
}
