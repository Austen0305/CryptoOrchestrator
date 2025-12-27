import React, { useState, useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Star, StarOff, Search, TrendingUp, TrendingDown, Plus, X } from "lucide-react";
import { useWatchlist, useAddToWatchlist, useRemoveFromWatchlist, useSearchTradingPairs } from "@/hooks/useMarkets";
import { useDebounce } from "@/hooks/useDebounce";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import { formatCurrency, formatPercentage, formatNumber, formatLargeNumber } from "@/lib/formatters";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { EmptyState } from "@/components/EmptyState";
import { ErrorRetry } from "@/components/ErrorRetry";
import type { TradingPair } from "@shared/schema";

export function Watchlist() {
  const { isAuthenticated } = useAuth();
  const { data: watchlist, isLoading: watchlistLoading, error: watchlistError, refetch: refetchWatchlist } = useWatchlist();
  // Type assertion for React Query error (known limitation with unknown type)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const watchlistErrorTyped: Error | null | undefined = watchlistError as any;
  const [searchQuery, setSearchQuery] = useState("");
  const debouncedSearchQuery = useDebounce(searchQuery, 300); // Debounce search input
  const { data: searchResults, error: searchError } = useSearchTradingPairs(debouncedSearchQuery);
  // Type assertion for search results (React Query returns unknown)
  const typedSearchResults: TradingPair[] | undefined = Array.isArray(searchResults) ? searchResults : undefined;
  const addToWatchlist = useAddToWatchlist();
  const removeFromWatchlist = useRemoveFromWatchlist();

  // Use real API data with fallback to empty array
  const watchlistData: TradingPair[] = Array.isArray(watchlist) ? watchlist : [];
  const filteredWatchlist = useMemo(() => 
    debouncedSearchQuery
      ? watchlistData.filter((item) =>
          item.symbol.toLowerCase().includes(debouncedSearchQuery.toLowerCase())
        )
      : watchlistData,
    [watchlistData, debouncedSearchQuery]
  );


  // Type guard for error - check if error exists
  const hasWatchlistError = watchlistErrorTyped !== null && watchlistErrorTyped !== undefined;

  const handleToggleFavorite = async (symbol: string, isFavorite: boolean) => {
    if (isFavorite) {
      await removeFromWatchlist.mutateAsync(symbol);
    } else {
      await addToWatchlist.mutateAsync(symbol);
    }
  };

  const renderWatchlistContent = (): React.ReactNode => {
    if (watchlistLoading) {
      return <LoadingSkeleton count={5} className="h-12 w-full" />;
    }
    if (watchlistErrorTyped !== null && watchlistErrorTyped !== undefined) {
      const errorMessage: string = watchlistErrorTyped instanceof Error 
        ? watchlistErrorTyped.message 
        : String(watchlistErrorTyped || "Unknown error");
      return (
        <ErrorRetry
          title="Failed to load watchlist"
          message={errorMessage}
          onRetry={() => refetchWatchlist()}
          error={watchlistErrorTyped instanceof Error ? watchlistErrorTyped : undefined}
        />
      );
    }
    if (filteredWatchlist.length === 0) {
      return (
        <EmptyState
          icon={Star}
          title="No pairs in your watchlist"
          description={searchQuery ? "No pairs match your search. Try a different query." : "Add trading pairs to track them here"}
        />
      );
    }
    return (
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
            {filteredWatchlist.map((item) => (
              <TableRow key={item.symbol}>
                <TableCell className="font-medium">{item.symbol}</TableCell>
                <TableCell>{formatCurrency(item.currentPrice)}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    {item.change24h >= 0 ? (
                      <TrendingUp className="h-4 w-4 text-green-500" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-red-500" />
                    )}
                    <span className={cn(item.change24h >= 0 ? "text-green-500" : "text-red-500")}>
                      {formatPercentage(item.change24h)}
                    </span>
                  </div>
                </TableCell>
                <TableCell>{formatLargeNumber(item.volume24h)}</TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleToggleFavorite(item.symbol, true)}
                  >
                    <StarOff className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
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
        {renderWatchlistContent()}

        {/* Search Results */}
        {searchQuery && typedSearchResults && typedSearchResults.length > 0 && (
          <div className="rounded-md border bg-muted/50 p-4">
            <div className="font-medium mb-2">Search Results</div>
            <div className="space-y-2">
              {typedSearchResults.slice(0, 5).map((item: TradingPair) => (
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
                      {item.baseAsset}/{item.quoteAsset}
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

