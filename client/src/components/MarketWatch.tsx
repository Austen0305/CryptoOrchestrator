import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { TrendingUp, TrendingDown, Activity, RefreshCw, Search, Star } from "lucide-react";
import { useMarketTickers, useMarketSummary, useMarkets } from "@/hooks/useMarkets";
import { cn } from "@/lib/utils";
import { formatCurrency, formatPercentage, formatLargeNumber } from "@/lib/formatters";

export function MarketWatch() {
  const { data: tickers, isLoading: tickersLoading } = useMarketTickers();
  const { data: summary } = useMarketSummary();
  const { data: markets } = useMarkets();
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"price" | "change" | "volume">("volume");

  // Mock tickers data - in production, this would come from the API
  const mockTickers = [
    { symbol: "BTC/USD", price: 47350, change24h: 4.76, volume24h: 2400000000, high24h: 47800, low24h: 46800 },
    { symbol: "ETH/USD", price: 2920, change24h: 2.1, volume24h: 1200000000, high24h: 2950, low24h: 2880 },
    { symbol: "SOL/USD", price: 142, change24h: -0.5, volume24h: 450000000, high24h: 145, low24h: 140 },
    { symbol: "ADA/USD", price: 0.58, change24h: 3.21, volume24h: 320000000, high24h: 0.60, low24h: 0.56 },
    { symbol: "DOT/USD", price: 7.23, change24h: -2.14, volume24h: 180000000, high24h: 7.50, low24h: 7.10 },
    { symbol: "MATIC/USD", price: 0.92, change24h: 5.67, volume24h: 280000000, high24h: 0.95, low24h: 0.90 },
    { symbol: "LINK/USD", price: 14.82, change24h: -3.45, volume24h: 220000000, high24h: 15.20, low24h: 14.50 },
    { symbol: "UNI/USD", price: 6.45, change24h: 7.23, volume24h: 190000000, high24h: 6.70, low24h: 6.30 },
  ];

  const tickersData = tickers || mockTickers;

  const filteredAndSorted = tickersData
    .filter((ticker: any) =>
      ticker.symbol.toLowerCase().includes(searchQuery.toLowerCase())
    )
    .sort((a: any, b: any) => {
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

  const topGainers = [...tickersData]
    .filter((t: any) => t.change24h > 0)
    .sort((a: any, b: any) => b.change24h - a.change24h)
    .slice(0, 5);

  const topLosers = [...tickersData]
    .filter((t: any) => t.change24h < 0)
    .sort((a: any, b: any) => a.change24h - b.change24h)
    .slice(0, 5);

  const topVolume = [...tickersData]
    .sort((a: any, b: any) => b.volume24h - a.volume24h)
    .slice(0, 5);

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
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
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
                      <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                        Loading market data...
                      </TableCell>
                    </TableRow>
                  ) : filteredAndSorted.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                        No markets found
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredAndSorted.map((ticker: any) => (
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
                  {topGainers.map((ticker: any) => (
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
                  {topLosers.map((ticker: any) => (
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
                  {topVolume.map((ticker: any) => (
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

