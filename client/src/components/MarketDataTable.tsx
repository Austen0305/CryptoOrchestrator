import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Star, Search, TrendingUp, TrendingDown, Download } from "lucide-react";
import { useState } from "react";
import { useToast } from "@/hooks/use-toast";
import { exportToCSV, exportWithNotification } from "@/lib/export";

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
}

export function MarketDataTable({ markets }: MarketDataTableProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const { toast } = useToast();

  const toggleFavorite = (pair: string) => {
    const newFavorites = new Set(favorites);
    if (newFavorites.has(pair)) {
      newFavorites.delete(pair);
    } else {
      newFavorites.add(pair);
    }
    setFavorites(newFavorites);
    console.log(`Toggled favorite for ${pair}`);
  };

  const filteredMarkets = markets.filter((m) =>
    m.pair.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleExportCSV = () => {
    const rows = filteredMarkets.map((m) => ({
      Pair: m.pair,
      Price: m.price,
      Change24h: m.change24h,
      Volume24h: m.volume24h,
    }));
    exportWithNotification(() => exportToCSV(rows, { filename: `markets-${Date.now()}.csv` }), toast, 'Markets exported to CSV');
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-4">
          <CardTitle>Markets</CardTitle>
          <div className="flex items-center gap-2">
            <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search markets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
              data-testid="input-search-markets"
            />
            </div>
            <Button variant="outline" size="sm" onClick={handleExportCSV} data-testid="button-export-markets-csv">
              <Download className="h-4 w-4 mr-1" /> CSV
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b text-sm text-muted-foreground">
                <th className="text-left p-3 font-medium">Pair</th>
                <th className="text-right p-3 font-medium">Price</th>
                <th className="text-right p-3 font-medium">24h Change</th>
                <th className="text-right p-3 font-medium">24h Volume</th>
                <th className="text-center p-3 font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredMarkets.map((market) => {
                const isPositive = market.change24h >= 0;
                return (
                  <tr
                    key={market.pair}
                    className="border-b hover-elevate"
                    data-testid={`row-market-${market.pair}`}
                  >
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          onClick={() => toggleFavorite(market.pair)}
                          data-testid={`button-favorite-${market.pair}`}
                        >
                          <Star
                            className={`h-4 w-4 ${
                              favorites.has(market.pair)
                                ? "fill-yellow-500 text-yellow-500"
                                : ""
                            }`}
                          />
                        </Button>
                        <span className="font-semibold">{market.pair}</span>
                      </div>
                    </td>
                    <td className="p-3 text-right font-mono font-semibold" data-testid={`text-price-${market.pair}`}>
                      ${market.price.toLocaleString()}
                    </td>
                    <td className="p-3 text-right">
                      <Badge
                        variant={isPositive ? "default" : "destructive"}
                        className="font-mono"
                      >
                        {isPositive ? (
                          <TrendingUp className="w-3 h-3 mr-1" />
                        ) : (
                          <TrendingDown className="w-3 h-3 mr-1" />
                        )}
                        {isPositive ? "+" : ""}
                        {market.change24h.toFixed(2)}%
                      </Badge>
                    </td>
                    <td className="p-3 text-right font-mono text-sm">
                      ${(market.volume24h / 1000000).toFixed(2)}M
                    </td>
                    <td className="p-3 text-center">
                      <Button size="sm" data-testid={`button-trade-${market.pair}`}>
                        Trade
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
