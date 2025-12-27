import React, { useState, useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { TrendingUp, TrendingDown, Activity, RefreshCw, Search, Star } from "lucide-react";
import { useMarketTickers, useMarketSummary } from "@/hooks/useMarkets";
import { cn } from "@/lib/utils";
import { formatCurrency, formatPercentage, formatLargeNumber } from "@/lib/formatters";
import { useDebounce } from "@/hooks/useDebounce";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { EmptyState } from "@/components/EmptyState";
import { ErrorRetry } from "@/components/ErrorRetry";

interface TickerData {
  symbol: string;
  price: number;
  change24h: number;
  volume24h: number;
  high24h: number;
  low24h: number;
}

interface ApiTicker {
  symbol?: string;
  pair?: string;
  last_price?: number;
  price?: number;
  current_price?: number;
  change_24h?: number;
  change24h?: number;
  volume_24h?: number;
  volume24h?: number;
  high_24h?: number;
  high24h?: number;
  low_24h?: number;
  low24h?: number;
  [key: string]: unknown; // Allow additional fields from API
}

export function MarketWatch() {
  const { data: tickers, isLoading: tickersLoading, error: tickersError, refetch: refetchTickers } = useMarketTickers();
  const { data: summary } = useMarketSummary();
  const [searchQuery, setSearchQuery] = useState("");
  const debouncedSearchQuery = useDebounce(searchQuery, 300);
  const [sortBy, setSortBy] = useState<"price" | "change" | "volume">("volume");

  // Transform ticker data from API to expected format
  const tickersData = useMemo((): TickerData[] => {
    if (!tickers || !Array.isArray(tickers)) return [];
    return tickers.map((ticker: ApiTicker) => ({
      symbol: ticker.symbol || ticker.pair || "",
      price: ticker.last_price || ticker.price || ticker.current_price || 0,
      change24h: ticker.change_24h || ticker.change24h || 0,
      volume24h: ticker.volume_24h || ticker.volume24h || 0,
      high24h: ticker.high_24h || ticker.high24h || 0,
      low24h: ticker.low_24h || ticker.low24h || 0,
    }));
  }, [tickers]);

  const filteredAndSorted = useMemo(() => {
    return tickersData
      .filter((ticker) =>
        ticker.symbol.toLowerCase().includes(debouncedSearchQuery.toLowerCase())
      )
      .sort((a, b) => {
        switch (sortBy) {
          case "price":
            return b.price - a.price;
          case "change":
            return b.change24h - a.change24h;
          case "volume":
            return b.volume24h - a.volume24h;
          default:
            return 0;
        }
      });
  }, [tickersData, debouncedSearchQuery, sortBy]);

  const topGainers = useMemo(() => {
    return [...tickersData]
      .filter((t) => t.change24h > 0)
      .sort((a, b) => b.change24h - a.change24h)
      .slice(0, 5);
  }, [tickersData]);

  const topLosers = useMemo(() => {
    return [...tickersData]
      .filter((t) => t.change24h < 0)
      .sort((a, b) => a.change24h - b.change24h)
      .slice(0, 5);
  }, [tickersData]);

  const topVolume = useMemo(() => {
    return [...tickersData]
      .sort((a, b) => b.volume24h - a.volume24h)
      .slice(0, 5);
  }, [tickersData]);

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Market Watch
            </CardTitle>
            <CardDescription>
              Real-time market data and price movements
            </CardDescription>
          </div>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => refetchTickers()}
            disabled={tickersLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${tickersLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <Tabs defaultValue="all" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="all">All Markets</TabsTrigger>
            <TabsTrigger value="gainers">Top Gainers</TabsTrigger>
            <TabsTrigger value="losers">Top Losers</TabsTrigger>
            <TabsTrigger value="volume">Top Volume</TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="space-y-4">
            {/* Search and Sort */}
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search markets..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8"
                />
              </div>
              <Button
                variant={sortBy === "volume" ? "default" : "outline"}
                size="sm"
                onClick={() => setSortBy("volume")}
              >
                Volume
              </Button>
              <Button
                variant={sortBy === "change" ? "default" : "outline"}
                size="sm"
                onClick={() => setSortBy("change")}
              >
                Change
              </Button>
              <Button
                variant={sortBy === "price" ? "default" : "outline"}
                size="sm"
                onClick={() => setSortBy("price")}
              >
                Price
              </Button>
            </div>

            {/* Markets Table */}
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead>24h Change</TableHead>
                    <TableHead>24h High</TableHead>
                    <TableHead>24h Low</TableHead>
                    <TableHead>24h Volume</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tickersLoading ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8">
                        <LoadingSkeleton count={5} className="h-12 w-full" />
                      </TableCell>
                    </TableRow>
                  ) : tickersError ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8">
                        <ErrorRetry
                          title="Failed to load market data"
                          message={tickersError instanceof Error ? tickersError.message : "Unable to fetch market data. Please try again."}
                          onRetry={() => refetchTickers()}
                          error={tickersError as Error}
                        />
                      </TableCell>
                    </TableRow>
                  ) : filteredAndSorted.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8">
                        <EmptyState
                          icon={Search}
                          title="No markets found"
                          description={searchQuery ? "Try adjusting your search query" : "No market data available at the moment"}
                        />
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredAndSorted.map((ticker) => (
                      <TableRow key={ticker.symbol} className="hover:bg-muted/50 cursor-pointer">
                        <TableCell className="font-medium">{ticker.symbol}</TableCell>
                        <TableCell>{formatCurrency(ticker.price)}</TableCell>
                        <TableCell>
                          <div className={cn(
                            "flex items-center gap-1 font-medium",
                            ticker.change24h >= 0 ? "text-green-500" : "text-red-500"
                          )}>
                            {ticker.change24h >= 0 ? (
                              <TrendingUp className="h-4 w-4" />
                            ) : (
                              <TrendingDown className="h-4 w-4" />
                            )}
                            {formatPercentage(ticker.change24h)}
                          </div>
                        </TableCell>
                        <TableCell className="text-green-500">
                          {formatCurrency(ticker.high24h)}
                        </TableCell>
                        <TableCell className="text-red-500">
                          {formatCurrency(ticker.low24h)}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          ${formatLargeNumber(ticker.volume24h)}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </TabsContent>

          <TabsContent value="gainers" className="space-y-4">
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead>24h Change</TableHead>
                    <TableHead>Volume</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {topGainers.map((ticker) => (
                    <TableRow key={ticker.symbol}>
                      <TableCell className="font-medium">{ticker.symbol}</TableCell>
                      <TableCell>{formatCurrency(ticker.price)}</TableCell>
                      <TableCell>
                        <Badge variant="default" className="bg-green-500">
                          <TrendingUp className="h-3 w-3 mr-1" />
                          {formatPercentage(ticker.change24h)}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        ${formatLargeNumber(ticker.volume24h)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </TabsContent>

          <TabsContent value="losers" className="space-y-4">
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead>24h Change</TableHead>
                    <TableHead>Volume</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {topLosers.map((ticker) => (
                    <TableRow key={ticker.symbol}>
                      <TableCell className="font-medium">{ticker.symbol}</TableCell>
                      <TableCell>{formatCurrency(ticker.price)}</TableCell>
                      <TableCell>
                        <Badge variant="destructive">
                          <TrendingDown className="h-3 w-3 mr-1" />
                          {formatPercentage(ticker.change24h)}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        ${formatLargeNumber(ticker.volume24h)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </TabsContent>

          <TabsContent value="volume" className="space-y-4">
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead>24h Change</TableHead>
                    <TableHead>24h Volume</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {topVolume.map((ticker) => (
                    <TableRow key={ticker.symbol}>
                      <TableCell className="font-medium">{ticker.symbol}</TableCell>
                      <TableCell>{formatCurrency(ticker.price)}</TableCell>
                      <TableCell>
                        <div className={cn(
                          "flex items-center gap-1 font-medium",
                          ticker.change24h >= 0 ? "text-green-500" : "text-red-500"
                        )}>
                          {ticker.change24h >= 0 ? (
                            <TrendingUp className="h-4 w-4" />
                          ) : (
                            <TrendingDown className="h-4 w-4" />
                          )}
                          {formatPercentage(ticker.change24h)}
                        </div>
                      </TableCell>
                      <TableCell className="font-medium">
                        ${formatLargeNumber(ticker.volume24h)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

