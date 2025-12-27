import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  TrendingUp, 
  Star, 
  Users, 
  BarChart3, 
  ArrowUpDown,
  Filter,
  Search,
  ExternalLink
} from "lucide-react";
import { 
  useMarketplaceTraders, 
  useFollowTrader,
  type MarketplaceFilters,
  type Trader 
} from "@/hooks/useMarketplace";
import { useFollowTrader as useCopyFollowTrader } from "@/hooks/useCopyTrading";
import { formatCurrency, formatPercentage } from "@/lib/formatters";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";
import { useToast } from "@/hooks/use-toast";
import { useLocation } from "wouter";

export function Marketplace() {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const followTrader = useCopyFollowTrader();
  
  const [filters, setFilters] = useState<MarketplaceFilters>({
    sort_by: "total_return",
    skip: 0,
    limit: 20,
  });
  const [showFilters, setShowFilters] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const { data, isLoading, error, refetch } = useMarketplaceTraders(filters);

  const handleFollow = async (trader: Trader) => {
    try {
      await followTrader.mutateAsync({
        trader_id: trader.user_id,
        allocation_percentage: 100,
      });
      toast({
        title: "Success",
        description: `Now following ${trader.username || `Trader ${trader.user_id}`}`,
      });
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to follow trader",
        variant: "destructive",
      });
    }
  };

  const handleViewProfile = (traderId: number) => {
    setLocation(`/marketplace/trader/${traderId}`);
  };

  const filteredTraders = data?.traders.filter((trader) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      trader.username?.toLowerCase().includes(query) ||
      trader.profile_description?.toLowerCase().includes(query) ||
      trader.trading_strategy?.toLowerCase().includes(query)
    );
  }) || [];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Copy Trading Marketplace
          </CardTitle>
          <CardDescription>
            Discover top signal providers and copy their trades automatically
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search and Filters */}
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search traders by name, description, or strategy..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2"
            >
              <Filter className="h-4 w-4" />
              Filters
            </Button>
          </div>

          {/* Filter Panel */}
          {showFilters && (
            <Card className="p-4 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label>Sort By</Label>
                  <Select
                    value={filters.sort_by}
                    onValueChange={(value: any) =>
                      setFilters({ ...filters, sort_by: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="total_return">Total Return</SelectItem>
                      <SelectItem value="sharpe_ratio">Sharpe Ratio</SelectItem>
                      <SelectItem value="win_rate">Win Rate</SelectItem>
                      <SelectItem value="follower_count">Followers</SelectItem>
                      <SelectItem value="rating">Rating</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Min Rating</Label>
                  <Input
                    type="number"
                    min="0"
                    max="5"
                    step="0.1"
                    placeholder="0.0"
                    value={filters.min_rating || ""}
                    onChange={(e) =>
                      setFilters({
                        ...filters,
                        min_rating: e.target.value ? parseFloat(e.target.value) : undefined,
                      })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label>Min Win Rate (%)</Label>
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    step="1"
                    placeholder="0"
                    value={filters.min_win_rate ? filters.min_win_rate * 100 : ""}
                    onChange={(e) =>
                      setFilters({
                        ...filters,
                        min_win_rate: e.target.value ? parseFloat(e.target.value) / 100 : undefined,
                      })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label>Min Sharpe Ratio</Label>
                  <Input
                    type="number"
                    step="0.1"
                    placeholder="0.0"
                    value={filters.min_sharpe || ""}
                    onChange={(e) =>
                      setFilters({
                        ...filters,
                        min_sharpe: e.target.value ? parseFloat(e.target.value) : undefined,
                      })
                    }
                  />
                </div>
              </div>
            </Card>
          )}

          {/* Traders Grid */}
          {isLoading ? (
            <LoadingSkeleton count={6} className="h-48 w-full" />
          ) : error ? (
            <ErrorRetry
              title="Failed to load marketplace"
              message={error instanceof Error ? error.message : "An unexpected error occurred."}
              onRetry={() => refetch()}
              error={error as Error}
            />
          ) : filteredTraders.length === 0 ? (
            <EmptyState
              icon={TrendingUp}
              title="No traders found"
              description="Try adjusting your filters or search query."
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredTraders.map((trader) => (
                <Card key={trader.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg">
                          {trader.username || `Trader ${trader.user_id}`}
                        </CardTitle>
                        <CardDescription className="mt-1">
                          {trader.profile_description
                            ? trader.profile_description.substring(0, 100) + "..."
                            : "No description"}
                        </CardDescription>
                      </div>
                      {trader.average_rating > 0 && (
                        <div className="flex items-center gap-1">
                          <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                          <span className="text-sm font-semibold">
                            {trader.average_rating.toFixed(1)}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            ({trader.total_ratings})
                          </span>
                        </div>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Performance Metrics */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <div className="text-xs text-muted-foreground">Total Return</div>
                        <div
                          className={`text-lg font-bold ${
                            trader.total_return >= 0 ? "text-green-600" : "text-red-600"
                          }`}
                        >
                          {formatPercentage(trader.total_return)}
                        </div>
                      </div>
                      <div className="space-y-1">
                        <div className="text-xs text-muted-foreground">Win Rate</div>
                        <div className="text-lg font-bold">
                          {formatPercentage(trader.win_rate * 100)}
                        </div>
                      </div>
                      <div className="space-y-1">
                        <div className="text-xs text-muted-foreground">Sharpe Ratio</div>
                        <div className="text-lg font-bold">
                          {trader.sharpe_ratio.toFixed(2)}
                        </div>
                      </div>
                      <div className="space-y-1">
                        <div className="text-xs text-muted-foreground">Followers</div>
                        <div className="text-lg font-bold flex items-center gap-1">
                          <Users className="h-4 w-4" />
                          {trader.follower_count}
                        </div>
                      </div>
                    </div>

                    {/* Additional Info */}
                    <div className="flex items-center gap-2 flex-wrap">
                      {trader.risk_level && (
                        <Badge variant="outline">{trader.risk_level}</Badge>
                      )}
                      {trader.subscription_fee && (
                        <Badge variant="secondary">
                          ${trader.subscription_fee}/mo
                        </Badge>
                      )}
                      {trader.performance_fee_percentage > 0 && (
                        <Badge variant="secondary">
                          {trader.performance_fee_percentage}% perf fee
                        </Badge>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 pt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => handleViewProfile(trader.id)}
                      >
                        <ExternalLink className="h-4 w-4 mr-2" />
                        View Profile
                      </Button>
                      <Button
                        size="sm"
                        className="flex-1"
                        onClick={() => handleFollow(trader)}
                        disabled={followTrader.isPending}
                      >
                        Follow
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Pagination */}
          {data && data.total > filters.limit! && (
            <div className="flex items-center justify-between pt-4">
              <div className="text-sm text-muted-foreground">
                Showing {filters.skip! + 1}-{Math.min(filters.skip! + filters.limit!, data.total)} of{" "}
                {data.total} traders
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={filters.skip === 0}
                  onClick={() =>
                    setFilters({ ...filters, skip: Math.max(0, filters.skip! - filters.limit!) })
                  }
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={filters.skip! + filters.limit! >= data.total}
                  onClick={() =>
                    setFilters({ ...filters, skip: filters.skip! + filters.limit! })
                  }
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
