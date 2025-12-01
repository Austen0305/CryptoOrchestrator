import { MarketDataTable } from "@/components/MarketDataTable";
import { MarketWatch } from "@/components/MarketWatch";
import { Watchlist } from "@/components/Watchlist";
import { AdvancedMarketAnalysis } from "@/components/AdvancedMarketAnalysis";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useState, useMemo } from "react";
import { useMarkets } from "@/hooks/useApi";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";
import { TrendingUp } from "lucide-react";

export default function Markets() {
  const [selectedPair, setSelectedPair] = useState<string>("BTC/USD");
  const { data: marketsData, isLoading: marketsLoading, error: marketsError, refetch: refetchMarkets } = useMarkets();
  
  // Transform TradingPair data to Market format expected by MarketDataTable
  const markets = useMemo(() => {
    if (!marketsData) return [];
    // Handle both TradingPair schema (camelCase) and API response (snake_case)
    return marketsData.map((pair: { symbol?: string; pair?: string; current_price?: number; currentPrice?: number; price?: number; change_24h?: number; change24h?: number; volume_24h?: number; volume24h?: number }) => ({
      pair: pair.symbol || pair.pair || "",
      price: pair.current_price || pair.currentPrice || pair.price || 0,
      change24h: pair.change_24h || pair.change24h || 0,
      volume24h: pair.volume_24h || pair.volume24h || 0,
    }));
  }, [marketsData]);

  return (
    <div className="space-y-6 w-full">
      <div>
        <h1 className="text-3xl font-bold">Markets</h1>
        <p className="text-muted-foreground mt-1">
          Browse and trade cryptocurrency pairs
        </p>
      </div>

      <Tabs defaultValue="watch" className="space-y-4">
        <TabsList>
          <TabsTrigger value="watch">Market Watch</TabsTrigger>
          <TabsTrigger value="watchlist">Watchlist</TabsTrigger>
          <TabsTrigger value="all">All Markets</TabsTrigger>
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
              <LoadingSkeleton variant="table" count={10} className="h-16" />
            </div>
          ) : marketsError ? (
            <ErrorRetry
              title="Failed to load markets"
              message={marketsError instanceof Error ? marketsError.message : "Unable to fetch markets data. Please try again."}
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
