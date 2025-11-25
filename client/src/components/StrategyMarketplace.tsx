/**
 * Strategy Marketplace Component - Browse and purchase strategies
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useStrategies, Strategy } from "@/hooks/useStrategies";
import { Loader2, Search, Star, Download, TrendingUp, Users } from "lucide-react";
import { useState } from "react";
import { formatPercentage } from "@/lib/formatters";

export function StrategyMarketplace() {
  const { data: strategies, isLoading } = useStrategies(true); // Include public strategies
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"rating" | "performance" | "popularity">("rating");

  // Filter public/published strategies
  const marketplaceStrategies = strategies?.filter((s) => s.is_public && s.is_published) || [];

  // Filter by search query
  const filteredStrategies = marketplaceStrategies.filter((strategy) =>
    strategy.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    strategy.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    strategy.strategy_type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Sort strategies
  const sortedStrategies = [...filteredStrategies].sort((a, b) => {
    switch (sortBy) {
      case "rating":
        return (b.rating || 0) - (a.rating || 0);
      case "performance":
        return (b.backtest_sharpe_ratio || 0) - (a.backtest_sharpe_ratio || 0);
      case "popularity":
        return b.usage_count - a.usage_count;
      default:
        return 0;
    }
  });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Strategy Marketplace</h2>
        <p className="text-muted-foreground mt-1">
          Browse and use strategies from the community ({marketplaceStrategies.length} available)
        </p>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search strategies..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-3 py-2 rounded-md border bg-background"
            >
              <option value="rating">Sort by Rating</option>
              <option value="performance">Sort by Performance</option>
              <option value="popularity">Sort by Popularity</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Strategy Grid */}
      {sortedStrategies.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">
              {searchQuery ? "No strategies found matching your search." : "No strategies available in the marketplace yet."}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedStrategies.map((strategy) => (
            <Card key={strategy.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{strategy.name}</CardTitle>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="outline">{strategy.strategy_type.toUpperCase()}</Badge>
                      <Badge variant="secondary">{strategy.category}</Badge>
                    </div>
                  </div>
                  {strategy.rating > 0 && (
                    <div className="flex items-center gap-1">
                      <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                      <span className="text-sm font-medium">{strategy.rating.toFixed(1)}</span>
                    </div>
                  )}
                </div>
                <CardDescription className="mt-2">
                  {strategy.description?.substring(0, 120)}...
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Performance Metrics */}
                  {strategy.backtest_sharpe_ratio !== null && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Sharpe Ratio:</span>
                        <span className="font-medium">{strategy.backtest_sharpe_ratio.toFixed(2)}</span>
                      </div>
                      {strategy.backtest_win_rate !== null && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Win Rate:</span>
                          <span className="font-medium">{formatPercentage(strategy.backtest_win_rate)}</span>
                        </div>
                      )}
                      {strategy.backtest_total_return !== null && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Total Return:</span>
                          <span className="font-medium text-green-600">
                            {formatPercentage(strategy.backtest_total_return)}
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Usage Stats */}
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Users className="h-4 w-4" />
                      <span>{strategy.usage_count} users</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <TrendingUp className="h-4 w-4" />
                      <span>v{strategy.version}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <Button className="flex-1" variant="outline">
                      <Download className="h-4 w-4 mr-2" />
                      View Details
                    </Button>
                    <Button className="flex-1">
                      Use Strategy
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
