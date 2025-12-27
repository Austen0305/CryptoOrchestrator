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
  Code,
  Star,
  Download,
  ShoppingCart,
  Filter,
  Search,
  ExternalLink,
  TrendingUp,
  Zap,
  LineChart,
} from "lucide-react";
import {
  useMarketplaceIndicators,
  usePurchaseIndicator,
  type IndicatorFilters,
  type Indicator,
} from "@/hooks/useIndicators";
import { formatCurrency } from "@/lib/formatters";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";
import { useToast } from "@/hooks/use-toast";
import { useLocation } from "wouter";
import { useAuth } from "@/hooks/useAuth";

export function IndicatorMarketplace() {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const { user } = useAuth();
  const purchaseIndicator = usePurchaseIndicator();

  const [filters, setFilters] = useState<IndicatorFilters>({
    sort_by: "download_count",
    skip: 0,
    limit: 20,
  });
  const [showFilters, setShowFilters] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const { data, isLoading, error, refetch } = useMarketplaceIndicators(filters);

  const handlePurchase = async (indicator: Indicator) => {
    if (indicator.is_free) {
      toast({
        title: "Free Indicator",
        description: "This indicator is free - no purchase needed!",
      });
      return;
    }

    try {
      await purchaseIndicator.mutateAsync({
        indicatorId: indicator.id,
      });
      toast({
        title: "Success",
        description: `Successfully purchased ${indicator.name}`,
      });
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to purchase indicator",
        variant: "destructive",
      });
    }
  };

  const handleViewDetail = (indicatorId: number) => {
    setLocation(`/indicators/${indicatorId}`);
  };

  const filteredIndicators = data?.indicators.filter((indicator) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      indicator.name.toLowerCase().includes(query) ||
      indicator.description?.toLowerCase().includes(query) ||
      indicator.tags?.some((tag) => tag.toLowerCase().includes(query))
    );
  }) || [];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Code className="h-5 w-5" />
            Indicator Marketplace
          </CardTitle>
          <CardDescription>
            Discover and use custom technical indicators created by the community
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search and Filters */}
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search indicators by name, description, or tags..."
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
                      <SelectItem value="download_count">Downloads</SelectItem>
                      <SelectItem value="purchase_count">Purchases</SelectItem>
                      <SelectItem value="rating">Rating</SelectItem>
                      <SelectItem value="price">Price</SelectItem>
                      <SelectItem value="created_at">Newest</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Category</Label>
                  <Select
                    value={filters.category || ""}
                    onValueChange={(value) =>
                      setFilters({ ...filters, category: value || undefined })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All Categories" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All Categories</SelectItem>
                      <SelectItem value="trend">Trend</SelectItem>
                      <SelectItem value="momentum">Momentum</SelectItem>
                      <SelectItem value="volatility">Volatility</SelectItem>
                      <SelectItem value="volume">Volume</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Type</Label>
                  <Select
                    value={
                      filters.is_free === undefined
                        ? ""
                        : filters.is_free
                        ? "free"
                        : "paid"
                    }
                    onValueChange={(value) =>
                      setFilters({
                        ...filters,
                        is_free: value === "" ? undefined : value === "free",
                      })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All Types" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All Types</SelectItem>
                      <SelectItem value="free">Free</SelectItem>
                      <SelectItem value="paid">Paid</SelectItem>
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
              </div>
            </Card>
          )}

          {/* Indicators Grid */}
          {isLoading ? (
            <LoadingSkeleton count={6} className="h-48 w-full" />
          ) : error ? (
            <ErrorRetry
              title="Failed to load marketplace"
              message={error instanceof Error ? error.message : "An unexpected error occurred."}
              onRetry={() => refetch()}
              error={error as Error}
            />
          ) : filteredIndicators.length === 0 ? (
            <EmptyState
              icon={Code}
              title="No indicators found"
              description="Try adjusting your filters or search query."
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredIndicators.map((indicator) => (
                <Card key={indicator.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg">{indicator.name}</CardTitle>
                        <CardDescription className="mt-1 line-clamp-2">
                          {indicator.description || "No description"}
                        </CardDescription>
                      </div>
                      {indicator.average_rating > 0 && (
                        <div className="flex items-center gap-1">
                          <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                          <span className="text-sm font-semibold">
                            {indicator.average_rating.toFixed(1)}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            ({indicator.total_ratings})
                          </span>
                        </div>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Stats */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <div className="text-xs text-muted-foreground">Downloads</div>
                        <div className="text-lg font-bold flex items-center gap-1">
                          <Download className="h-4 w-4" />
                          {indicator.download_count}
                        </div>
                      </div>
                      <div className="space-y-1">
                        <div className="text-xs text-muted-foreground">Purchases</div>
                        <div className="text-lg font-bold flex items-center gap-1">
                          <ShoppingCart className="h-4 w-4" />
                          {indicator.purchase_count}
                        </div>
                      </div>
                    </div>

                    {/* Tags and Category */}
                    <div className="flex items-center gap-2 flex-wrap">
                      {indicator.category && (
                        <Badge variant="outline">{indicator.category}</Badge>
                      )}
                      {indicator.is_free ? (
                        <Badge variant="secondary" className="bg-green-100 text-green-800">
                          Free
                        </Badge>
                      ) : (
                        <Badge variant="secondary">
                          {formatCurrency(indicator.price)}
                        </Badge>
                      )}
                      {indicator.language && (
                        <Badge variant="outline" className="text-xs">
                          {indicator.language}
                        </Badge>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 pt-2">
                      {/* Show analytics link if user owns this indicator */}
                      {user && indicator.developer && user.id.toString() === indicator.developer.id.toString() && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setLocation(`/developer/analytics`)}
                        >
                          <LineChart className="h-4 w-4 mr-2" />
                          Analytics
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => handleViewDetail(indicator.id)}
                      >
                        <ExternalLink className="h-4 w-4 mr-2" />
                        View
                      </Button>
                      {!indicator.is_free && (
                        <Button
                          size="sm"
                          className="flex-1"
                          onClick={() => handlePurchase(indicator)}
                          disabled={purchaseIndicator.isPending}
                        >
                          <ShoppingCart className="h-4 w-4 mr-2" />
                          Buy
                        </Button>
                      )}
                      {indicator.is_free && (
                        <Button
                          size="sm"
                          className="flex-1"
                          onClick={() => handleViewDetail(indicator.id)}
                        >
                          <Download className="h-4 w-4 mr-2" />
                          Use
                        </Button>
                      )}
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
                Showing {filters.skip! + 1}-{Math.min(filters.skip! + filters.limit!, data.total)}{" "}
                of {data.total} indicators
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
