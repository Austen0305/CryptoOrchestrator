import React, { useState, useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  useMarketplaceOverview,
  useTopProviders,
  useTopIndicators,
  useRevenueTrends,
} from "@/hooks/useMarketplace";
import { formatCurrency, formatPercentage, formatNumber } from "@/lib/formatters";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";
import {
  TrendingUp,
  Users,
  Package,
  DollarSign,
  Star,
  BarChart3,
  Calendar,
} from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { Download, FileDown, FileText, Bell } from "lucide-react";
import { exportToJSON, exportToCSV, exportToPDFSimple } from "@/lib/export";
import { useToast } from "@/hooks/use-toast";
import { AnalyticsThresholdManager } from "@/components/AnalyticsThresholdManager";

const COLORS = ["#8884d8", "#82ca9d", "#ffc658", "#ff7c7c", "#8dd1e1"];

export function MarketplaceAnalyticsDashboard() {
  const { isAuthenticated } = useAuth();
  const { toast } = useToast();
  const [days, setDays] = useState(30);
  const [providerSort, setProviderSort] = useState("total_return");
  const [indicatorSort, setIndicatorSort] = useState("purchase_count");

  const { data: overview, isLoading: overviewLoading, error: overviewError } = useMarketplaceOverview();
  const { data: topProviders, isLoading: providersLoading } = useTopProviders(10, providerSort);
  const { data: topIndicators, isLoading: indicatorsLoading } = useTopIndicators(10, indicatorSort);
  const { data: revenueTrends, isLoading: trendsLoading } = useRevenueTrends(days);

  if (!isAuthenticated) {
    return (
      <EmptyState
        icon={BarChart3}
        title="Authentication Required"
        description="Please log in to view marketplace analytics"
      />
    );
  }

  if (overviewLoading) {
    return <LoadingSkeleton variant="dashboard" className="h-[600px]" />;
  }

  if (overviewError) {
    return <ErrorRetry error={overviewError} onRetry={() => window.location.reload()} />;
  }

  // Memoize expensive computations
  const copyTrading = useMemo(() => overview?.copy_trading, [overview?.copy_trading]);
  const indicators = useMemo(() => overview?.indicators, [overview?.indicators]);

  // Prepare revenue trends data (memoized)
  const trendsData = useMemo(
    () =>
      revenueTrends?.copy_trading?.map((item) => ({
        date: new Date(item.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
        platform: item.platform_revenue,
        providers: item.provider_payout || 0,
      })) || [],
    [revenueTrends?.copy_trading]
  );

  const indicatorTrendsData = useMemo(
    () =>
      revenueTrends?.indicators?.map((item) => ({
        date: new Date(item.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
        platform: item.platform_revenue,
        developers: item.developer_revenue || 0,
        purchases: item.purchase_count || 0,
      })) || [],
    [revenueTrends?.indicators]
  );

  // Category distribution (memoized)
  const categoryData = useMemo(
    () =>
      indicators?.by_category
        ? Object.entries(indicators.by_category).map(([name, value]) => ({
            name: name.charAt(0).toUpperCase() + name.slice(1),
            value,
          }))
        : [],
    [indicators?.by_category]
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Marketplace Analytics</h2>
          <p className="text-muted-foreground">Comprehensive insights into marketplace performance</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              try {
                if (overview) {
                  exportToJSON(overview, { filename: "marketplace_overview" });
                  toast({ title: "Exported", description: "Marketplace overview exported as JSON" });
                }
              } catch (error) {
                toast({
                  title: "Export Failed",
                  description: "Failed to export data",
                  variant: "destructive",
                });
              }
            }}
          >
            <Download className="h-4 w-4 mr-2" />
            Export JSON
          </Button>
          {topProviders?.providers && topProviders.providers.length > 0 && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  try {
                    exportToCSV(topProviders.providers as unknown as Record<string, unknown>[], { filename: "top_providers" });
                    toast({ title: "Exported", description: "Top providers exported as CSV" });
                  } catch (error) {
                    toast({
                      title: "Export Failed",
                      description: "Failed to export data",
                      variant: "destructive",
                    });
                  }
                }}
              >
                <FileDown className="h-4 w-4 mr-2" />
                Export CSV
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  try {
                    exportToPDFSimple(topProviders.providers as unknown as Record<string, unknown>[], {
                      filename: "top_providers",
                      title: "Top Signal Providers Report",
                      columns: ["username", "total_return", "sharpe_ratio", "win_rate", "follower_count", "average_rating"],
                    });
                    toast({ title: "Exported", description: "Top providers exported as PDF" });
                  } catch (error) {
                    toast({
                      title: "Export Failed",
                      description: "Failed to export PDF",
                      variant: "destructive",
                    });
                  }
                }}
              >
                <FileText className="h-4 w-4 mr-2" />
                Export PDF
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Providers</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(copyTrading?.total_providers || 0)}</div>
            <p className="text-xs text-muted-foreground">
              {copyTrading?.approved_providers || 0} approved
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Indicators</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(indicators?.total_indicators || 0)}</div>
            <p className="text-xs text-muted-foreground">
              {indicators?.approved_indicators || 0} approved
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Platform Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency((copyTrading?.platform_revenue || 0) + (indicators?.platform_revenue || 0))}
            </div>
            <p className="text-xs text-muted-foreground">Total revenue</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Rating</CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(copyTrading?.average_rating || 0).toFixed(1)}
            </div>
            <p className="text-xs text-muted-foreground">
              {formatNumber((copyTrading?.total_ratings || 0) + (indicators?.total_ratings || 0))} ratings
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="revenue">Revenue Trends</TabsTrigger>
          <TabsTrigger value="providers">Top Providers</TabsTrigger>
          <TabsTrigger value="indicators">Top Indicators</TabsTrigger>
          <TabsTrigger value="thresholds">
            <Bell className="h-4 w-4 mr-2" />
            Thresholds
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Copy Trading Stats */}
            <Card>
              <CardHeader>
                <CardTitle>Copy Trading Marketplace</CardTitle>
                <CardDescription>Signal provider statistics</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Followers</p>
                    <p className="text-2xl font-bold">{formatNumber(copyTrading?.total_followers || 0)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Payouts</p>
                    <p className="text-2xl font-bold">{formatNumber(copyTrading?.total_payouts || 0)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Provider Earnings</p>
                    <p className="text-2xl font-bold">{formatCurrency(copyTrading?.total_payout_amount || 0)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Platform Revenue</p>
                    <p className="text-2xl font-bold">{formatCurrency(copyTrading?.platform_revenue || 0)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Indicator Stats */}
            <Card>
              <CardHeader>
                <CardTitle>Indicator Marketplace</CardTitle>
                <CardDescription>Custom indicator statistics</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Purchases</p>
                    <p className="text-2xl font-bold">{formatNumber(indicators?.total_purchases || 0)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Free Indicators</p>
                    <p className="text-2xl font-bold">{formatNumber(indicators?.free_indicators || 0)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Developer Earnings</p>
                    <p className="text-2xl font-bold">{formatCurrency(indicators?.developer_revenue || 0)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Platform Revenue</p>
                    <p className="text-2xl font-bold">{formatCurrency(indicators?.platform_revenue || 0)}</p>
                  </div>
                </div>

                {/* Category Distribution */}
                {categoryData.length > 0 && (
                  <div className="mt-4">
                    <p className="text-sm font-medium mb-2">By Category</p>
                    <ResponsiveContainer width="100%" height={200}>
                      <PieChart>
                        <Pie
                          data={categoryData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {categoryData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="revenue" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Revenue Trends</h3>
            <div className="flex items-center gap-2">
              <Select value={days.toString()} onValueChange={(v) => setDays(parseInt(v))}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="7">Last 7 days</SelectItem>
                  <SelectItem value="14">Last 14 days</SelectItem>
                  <SelectItem value="30">Last 30 days</SelectItem>
                  <SelectItem value="60">Last 60 days</SelectItem>
                  <SelectItem value="90">Last 90 days</SelectItem>
                  <SelectItem value="180">Last 6 months</SelectItem>
                  <SelectItem value="365">Last year</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Copy Trading Revenue</CardTitle>
                <CardDescription>Platform vs Provider payouts</CardDescription>
              </CardHeader>
              <CardContent>
                {trendsLoading ? (
                  <LoadingSkeleton variant="chart" className="h-[300px]" />
                ) : trendsData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={trendsData}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                      <Legend />
                      <Bar dataKey="platform" fill="#8884d8" name="Platform Revenue" />
                      <Bar dataKey="providers" fill="#82ca9d" name="Provider Payouts" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyState icon={BarChart3} title="No revenue data" description="No revenue data available for this period" />
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Indicator Revenue</CardTitle>
                <CardDescription>Platform vs Developer earnings</CardDescription>
              </CardHeader>
              <CardContent>
                {trendsLoading ? (
                  <LoadingSkeleton variant="chart" className="h-[300px]" />
                ) : indicatorTrendsData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={indicatorTrendsData}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                      <Legend />
                      <Bar dataKey="platform" fill="#8884d8" name="Platform Revenue" />
                      <Bar dataKey="developers" fill="#ffc658" name="Developer Earnings" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyState icon={BarChart3} title="No revenue data" description="No revenue data available for this period" />
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="providers" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Top Signal Providers</h3>
            <Select value={providerSort} onValueChange={setProviderSort}>
              <SelectTrigger className="w-[200px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="total_return">Total Return</SelectItem>
                <SelectItem value="sharpe_ratio">Sharpe Ratio</SelectItem>
                <SelectItem value="follower_count">Followers</SelectItem>
                <SelectItem value="rating">Rating</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Top 10 Providers</CardTitle>
              <CardDescription>Ranked by {providerSort.replace("_", " ")}</CardDescription>
            </CardHeader>
            <CardContent>
              {providersLoading ? (
                <LoadingSkeleton variant="table" className="h-[400px]" />
              ) : topProviders?.providers && topProviders.providers.length > 0 ? (
                <div className="space-y-2">
                  {topProviders.providers.map((provider, index) => (
                    <div
                      key={provider.id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-bold">
                          {index + 1}
                        </div>
                        <div>
                          <p className="font-medium">{provider.username || `Provider #${provider.id}`}</p>
                          <p className="text-sm text-muted-foreground">
                            {formatPercentage(provider.win_rate)} win rate • {formatNumber(provider.follower_count)} followers
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-sm text-muted-foreground">Total Return</p>
                          <p className="font-bold">{formatPercentage(provider.total_return / 100)}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-muted-foreground">Sharpe</p>
                          <p className="font-bold">{provider.sharpe_ratio.toFixed(2)}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-muted-foreground">Rating</p>
                          <div className="flex items-center gap-1">
                            <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                            <p className="font-bold">{provider.average_rating.toFixed(1)}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState icon={Users} title="No providers" description="No signal providers found" />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="indicators" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Top Indicators</h3>
            <Select value={indicatorSort} onValueChange={setIndicatorSort}>
              <SelectTrigger className="w-[200px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="purchase_count">Purchases</SelectItem>
                <SelectItem value="rating">Rating</SelectItem>
                <SelectItem value="price">Price</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Top 10 Indicators</CardTitle>
              <CardDescription>Ranked by {indicatorSort.replace("_", " ")}</CardDescription>
            </CardHeader>
            <CardContent>
              {indicatorsLoading ? (
                <LoadingSkeleton variant="table" className="h-[400px]" />
              ) : topIndicators?.indicators && topIndicators.indicators.length > 0 ? (
                <div className="space-y-2">
                  {topIndicators.indicators.map((indicator, index) => (
                    <div
                      key={indicator.id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-bold">
                          {index + 1}
                        </div>
                        <div>
                          <p className="font-medium">{indicator.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {indicator.category} • {indicator.is_free ? "Free" : formatCurrency(indicator.price)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-sm text-muted-foreground">Purchases</p>
                          <p className="font-bold">{formatNumber(indicator.purchase_count)}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-muted-foreground">Rating</p>
                          <div className="flex items-center gap-1">
                            <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                            <p className="font-bold">{indicator.average_rating.toFixed(1)}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState icon={Package} title="No indicators" description="No indicators found" />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="thresholds" className="space-y-4">
          <AnalyticsThresholdManager />
        </TabsContent>
      </Tabs>
    </div>
  );
}
