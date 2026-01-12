import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Star, Search, TrendingUp, TrendingDown, Download } from "lucide-react";
import { OptimizedSearch } from "@/components/OptimizedSearch";
import { useState, useMemo, useCallback } from "react";
import { useToast } from "@/hooks/use-toast";
import { exportToCSV, exportWithNotification } from "@/lib/export";
import { usePagination } from "@/hooks/usePagination";
import { Pagination } from "@/components/Pagination";
import { useDebounce } from "@/hooks/useDebounce";

interface Market {
  pair: string;
  price: number;
  change24h: number;
  volume24h: number;
  marketCap?: number;
  isFavorite?: boolean;
}

interface MarketDataTableProps {
  markets: Market[];
  onPairSelect?: (pair: string) => void;
}

export const MarketDataTable = React.memo(function MarketDataTable({ markets, onPairSelect }: MarketDataTableProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const debouncedSearchQuery = useDebounce(searchQuery, 300);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const { toast } = useToast();

  const toggleFavorite = useCallback((pair: string) => {
    setFavorites((prevFavorites) => {
      const newFavorites = new Set(prevFavorites);
      if (newFavorites.has(pair)) {
        newFavorites.delete(pair);
      } else {
        newFavorites.add(pair);
      }
      return newFavorites;
    });
  }, []);

  const filteredMarkets = useMemo(() => 
    markets.filter((m) =>
      m.pair.toLowerCase().includes(debouncedSearchQuery.toLowerCase())
    ),
    [markets, debouncedSearchQuery]
  );

  // Pagination
  const pagination = usePagination({
    initialPage: 1,
    initialPageSize: 20,
    totalItems: filteredMarkets.length,
  });

  const paginatedMarkets = useMemo(() => {
    return filteredMarkets.slice(pagination.startIndex, pagination.endIndex);
  }, [filteredMarkets, pagination.startIndex, pagination.endIndex]);

  const handleExportCSV = useCallback(() => {
    const rows = filteredMarkets.map((m) => ({
      Pair: m.pair,
      Price: m.price,
      Change24h: m.change24h,
      Volume24h: m.volume24h,
    }));
    exportWithNotification(() => exportToCSV(rows, { filename: `markets-${Date.now()}.csv` }), toast, 'Markets exported to CSV');
  }, [filteredMarkets, toast]);

  return (
    <Card className="glass-premium border-border/50 shadow-2xl overflow-hidden">
      <CardHeader className="border-b border-primary/10 bg-gradient-to-r from-primary/5 to-transparent">
        <div className="flex items-center justify-between gap-4">
          <CardTitle className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent font-black tracking-tight">
            Market Discovery
          </CardTitle>
          <div className="flex items-center gap-2">
            <div className="relative flex-1 max-w-sm">
              <OptimizedSearch
                value={searchQuery}
                onChange={setSearchQuery}
                placeholder="Search assets..."
                className="w-full"
              />
            </div>
            <Button variant="outline" size="sm" onClick={handleExportCSV} className="border-primary/20 hover:bg-primary/10 transition-colors">
              <Download className="h-4 w-4 mr-1" /> Export
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto modern-scrollbar">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border/50 text-[10px] md:text-xs text-muted-foreground uppercase tracking-wider font-black bg-muted/30">
                <th className="text-left p-4">Pair</th>
                <th className="text-right p-4">Price</th>
                <th className="text-right p-4">24h Change</th>
                <th className="text-right p-4">24h Volume</th>
                <th className="text-center p-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/30">
              {paginatedMarkets.map((market) => {
                const isPositive = market.change24h >= 0;
                return (
                  <tr
                    key={market.pair}
                    className="group transition-colors hover:bg-primary/5 cursor-pointer"
                    data-testid={`row-market-${market.pair}`}
                    onClick={() => onPairSelect?.(market.pair)}
                  >
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 hover:bg-primary/20"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleFavorite(market.pair);
                          }}
                          data-testid={`button-favorite-${market.pair}`}
                        >
                          <Star
                            className={`h-4 w-4 transition-all ${
                              favorites.has(market.pair)
                                ? "fill-yellow-500 text-yellow-500 scale-125"
                                : "text-muted-foreground/50 group-hover:text-muted-foreground"
                            }`}
                          />
                        </Button>
                        <span className="font-bold text-foreground group-hover:text-primary transition-colors">{market.pair}</span>
                      </div>
                    </td>
                    <td className="p-4 text-right font-mono font-bold text-foreground" data-testid={`text-price-${market.pair}`}>
                      ${market.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="p-4 text-right">
                      <div className={cn(
                        "inline-flex items-center px-2.5 py-1 rounded-full text-xs font-black",
                        isPositive ? "bg-trading-profit/20 text-trading-profit border border-trading-profit/30" : "bg-trading-loss/20 text-trading-loss border border-trading-loss/30"
                      )}>
                        {isPositive ? (
                          <TrendingUp className="w-3 h-3 mr-1" />
                        ) : (
                          <TrendingDown className="w-3 h-3 mr-1" />
                        )}
                        {isPositive ? "+" : ""}
                        {market.change24h.toFixed(2)}%
                      </div>
                    </td>
                    <td className="p-4 text-right font-mono text-xs font-medium text-muted-foreground">
                      ${(market.volume24h / 1000000).toFixed(2)}M
                    </td>
                    <td className="p-4 text-center">
                      <Button size="sm" className="font-bold shadow-glow border-none" data-testid={`button-trade-${market.pair}`}>
                        Trade
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        {filteredMarkets.length > pagination.pageSize && (
          <div className="p-4 border-t border-border/50 bg-muted/10">
            <Pagination
              page={pagination.page}
              pageSize={pagination.pageSize}
              totalPages={pagination.totalPages}
              totalItems={pagination.totalItems}
              onPageChange={pagination.goToPage}
              onPageSizeChange={pagination.setPageSize}
              pageSizeOptions={[10, 20, 50, 100]}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
});
