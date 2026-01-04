import { MarketDataTable } from "@/components/MarketDataTable";
import { MarketWatch } from "@/components/MarketWatch";
import { Watchlist } from "@/components/Watchlist";
import { AdvancedMarketAnalysis } from "@/components/AdvancedMarketAnalysis";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useState, useMemo } from "react";
import { useMarkets } from "@/hooks/useApi";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { OptimizedLoading } from "@/components/OptimizedLoading";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";
import { TrendingUp } from "lucide-react";

export default function Markets() {
  const [selectedPair, setSelectedPair] = useState<string>("BTC/USD");
  const { data: marketsData, isLoading: marketsLoading, error: marketsError, refetch: refetchMarkets } = useMarkets();
  
  // Transform TradingPair data to Market format expected by MarketDataTable
  const markets = useMemo(() => {
    if (!marketsData || !Array.isArray(marketsData)) return [];
    // Handle both TradingPair schema (camelCase) and API response (snake_case)
    return marketsData.map((pair: { symbol?: string; pair?: string; current_price?: number; currentPrice?: number; price?: number; change_24h?: number; change24h?: number; volume_24h?: number; volume24h?: number }) => ({
      pair: pair.symbol || pair.pair || "",
      price: pair.current_price || pair.currentPrice || pair.price || 0,
      change24h: pair.change_24h || pair.change24h || 0,
      volume24h: pair.volume_24h || pair.volume24h || 0,
    }));
  }, [marketsData]);

  return (
    <div className="space-y-6 w-full animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold" data-testid="markets-page">Markets</h1>
        <p className="text-muted-foreground mt-1">
          Browse and trade cryptocurrency pairs on blockchain via DEX aggregators
        </p>
      </div>

      <Tabs defaultValue="watch" className="space-y-4">
        <TabsList className="w-full sm:w-auto grid grid-cols-3 sm:inline-flex">
          <TabsTrigger value="watch" className="text-xs sm:text-sm">Market Watch</TabsTrigger>
          <TabsTrigger value="watchlist" className="text-xs sm:text-sm">Watchlist</TabsTrigger>
          <TabsTrigger value="all" className="text-xs sm:text-sm">All Markets</TabsTrigger>
        </TabsList>

        <TabsContent value="watch">
          <MarketWatch />
        </TabsContent>

        <TabsContent value="watchlist">
          <Watchlist />
        </TabsContent>

        <TabsContent value="all">
          {marketsLoading ? (
            <div className="space-y-4">
              <OptimizedLoading variant="skeleton" />
            </div>
          ) : marketsError ? (
            <ErrorRetry
              title="Failed to load markets"
              onRetry={() => refetchMarkets()}
              error={marketsError as Error}
            />
          ) : !markets || markets.length === 0 ? (
            <EmptyState
              icon={TrendingUp}
              title="No markets available"
              description="No trading pairs are currently available. Please try again later."
            />
          ) : (
            <MarketDataTable 
              markets={markets}
              onPairSelect={(pair) => setSelectedPair(pair)}
            />
          )}
        </TabsContent>
      </Tabs>

      {/* Advanced Market Analysis */}
      <div className="mt-6">
        <AdvancedMarketAnalysis pair={selectedPair} />
      </div>
    </div>
  );
}
