import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Star, StarOff, Search, TrendingUp, TrendingDown, Plus, X } from "lucide-react";
import { useWatchlist, useMarkets, useAddToWatchlist, useRemoveFromWatchlist, useSearchTradingPairs } from "@/hooks/useMarkets";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import { formatCurrency, formatPercentage, formatNumber, formatLargeNumber } from "@/lib/formatters";

export function Watchlist() {
  const { isAuthenticated } = useAuth();
  const { data: watchlist, isLoading: watchlistLoading } = useWatchlist();
  const { data: markets } = useMarkets();
  const [searchQuery, setSearchQuery] = useState("");
  const { data: searchResults } = useSearchTradingPairs(searchQuery);
  const addToWatchlist = useAddToWatchlist();
  const removeFromWatchlist = useRemoveFromWatchlist();

  // Mock data - in production, this would come from the API
  const mockWatchlist = [
    { symbol: "BTC/USD", price: 47350, change24h: 4.76, volume24h: 2400000000, favorite: true },
    { symbol: "ETH/USD", price: 2920, change24h: 2.1, volume24h: 1200000000, favorite: true },
    { symbol: "SOL/USD", price: 142, change24h: -0.5, volume24h: 450000000, favorite: true },
    { symbol: "ADA/USD", price: 0.58, change24h: 3.21, volume24h: 320000000, favorite: false },
  ];

  const watchlistData = watchlist || mockWatchlist;
  const filteredWatchlist = searchQuery
    ? watchlistData.filter((item: any) =>
        item.symbol.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : watchlistData;

  const handleToggleFavorite = async (symbol: string, isFavorite: boolean) => {
    if (isFavorite) {
      await removeFromWatchlist.mutateAsync(symbol);
    } else {
      await addToWatchlist.mutateAsync(symbol);
    }
  };

  if (!isAuthenticated) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Watchlist</CardTitle>
          <CardDescription>Please log in to manage your watchlist</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Star className="h-5 w-5 text-yellow-500" />
              Watchlist
            </CardTitle>
            <CardDescription>
              Track your favorite trading pairs
            </CardDescription>
          </div>
          <Button variant="outline" size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Add Pair
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search trading pairs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8"
          />
        </div>

        {/* Watchlist Table */}
        {watchlistLoading ? (
          <div className="text-center py-8 text-muted-foreground">
            Loading watchlist...
          </div>
        ) : filteredWatchlist.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Star className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No pairs in your watchlist yet</p>
            <p className="text-sm">Add trading pairs to track them here</p>
          </div>
        ) : (
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Price</TableHead>
                  <TableHead>24h Change</TableHead>
                  <TableHead>24h Volume</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredWatchlist.map((item: any) => (
                  <TableRow key={item.symbol}>
                    <TableCell className="font-medium">{item.symbol}</TableCell>
                    <TableCell>{formatCurrency(item.price)}</TableCell>
                    <TableCell>
                      <div className={cn(
                        "flex items-center gap-1 font-medium",
                        item.change24h >= 0 ? "text-green-500" : "text-red-500"
                      )}>
                        {item.change24h >= 0 ? (
                          <TrendingUp className="h-4 w-4" />
                        ) : (
                          <TrendingDown className="h-4 w-4" />
                        )}
                        {formatPercentage(item.change24h)}
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      ${formatNumber(item.volume24h / 1000000, 1)}M
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleFavorite(item.symbol, item.favorite)}
                        >
                          {item.favorite ? (
                            <Star className="h-4 w-4 fill-yellow-500 text-yellow-500" />
                          ) : (
                            <StarOff className="h-4 w-4" />
                          )}
                        </Button>
                        <Button variant="ghost" size="sm">
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}

        {/* Search Results */}
        {searchQuery && searchResults && searchResults.length > 0 && (
          <div className="rounded-md border bg-muted/50 p-4">
            <div className="font-medium mb-2">Search Results</div>
            <div className="space-y-2">
              {searchResults.slice(0, 5).map((item: any) => (
                <div
                  key={item.symbol}
                  className="flex items-center justify-between p-2 rounded-md border hover:bg-background cursor-pointer"
                  onClick={() => {
                    addToWatchlist.mutate(item.symbol);
                    setSearchQuery("");
                  }}
                >
                  <div>
                    <div className="font-medium">{item.symbol}</div>
                    <div className="text-sm text-muted-foreground">
                      {item.exchange || "Multiple exchanges"}
                    </div>
                  </div>
                  <Button variant="outline" size="sm">
                    <Plus className="h-4 w-4 mr-1" />
                    Add
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

