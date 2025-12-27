import React, { useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useProviderAnalytics } from "@/hooks/useMarketplace";
import { formatCurrency, formatPercentage, formatNumber } from "@/lib/formatters";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";
import {
  TrendingUp,
  Users,
  DollarSign,
  Star,
  BarChart3,
  Target,
  Activity,
  Download,
  FileDown,
  FileText,
} from "lucide-react";
import { useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { exportToJSON, exportToCSV, exportToPDFSimple } from "@/lib/export";
import { useToast } from "@/hooks/use-toast";
import { AnalyticsThresholdManager } from "@/components/AnalyticsThresholdManager";

interface ProviderAnalyticsDashboardProps {
  providerId: number;
}

export function ProviderAnalyticsDashboard({ providerId }: ProviderAnalyticsDashboardProps) {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const { data: analytics, isLoading, error } = useProviderAnalytics(providerId);

  if (isLoading) {
    return <LoadingSkeleton variant="dashboard" className="h-[600px]" />;
  }

  if (error) {
    return <ErrorRetry error={error} onRetry={() => window.location.reload()} />;
  }

  if (!analytics) {
    return (
      <EmptyState
        icon={BarChart3}
        title="No Analytics Available"
        description="Analytics will appear once you start trading and gaining followers"
      />
    );
  }

  // Prepare payout history chart data
  const payoutData = analytics.recent_payouts.map((payout) => ({
    date: new Date(payout.period_end).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    amount: payout.provider_payout,
    status: payout.status,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Provider Analytics</h2>
          <p className="text-muted-foreground">Track your signal provider performance and earnings</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              try {
                if (analytics) {
                  exportToJSON(analytics, { filename: "provider_analytics" });
                  toast({ title: "Exported", description: "Provider analytics exported as JSON" });
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
          {analytics?.recent_payouts && analytics.recent_payouts.length > 0 && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  try {
                    exportToCSV(analytics.recent_payouts, { filename: "payout_history" });
                    toast({ title: "Exported", description: "Payout history exported as CSV" });
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
                    exportToPDFSimple(analytics.recent_payouts, {
                      filename: "payout_history",
                      title: "Provider Payout History",
                      columns: ["period_start", "period_end", "provider_payout", "status"],
                    });
                    toast({ title: "Exported", description: "Payout history exported as PDF" });
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

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Return</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatPercentage(analytics.total_return / 100)}</div>
            <p className="text-xs text-muted-foreground">All-time performance</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Followers</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(analytics.follower_count)}</div>
            <p className="text-xs text-muted-foreground">Active followers</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Earnings</CardTitle>
            <DollarSign className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{formatCurrency(analytics.total_earnings)}</div>
            <p className="text-xs text-muted-foreground">{formatNumber(analytics.total_payouts)} payouts</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Rating</CardTitle>
            <Star className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.average_rating.toFixed(1)}</div>
            <p className="text-xs text-muted-foreground">{formatNumber(analytics.total_ratings)} ratings</p>
          </CardContent>
        </Card>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Performance Metrics</CardTitle>
            <CardDescription>Key trading statistics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Win Rate</p>
                <p className="text-2xl font-bold">{formatPercentage(analytics.win_rate)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Sharpe Ratio</p>
                <p className="text-2xl font-bold">{analytics.sharpe_ratio.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Trades</p>
                <p className="text-2xl font-bold">{formatNumber(analytics.total_trades)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Return</p>
                <p className="text-2xl font-bold">{formatPercentage(analytics.total_return / 100)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Earnings Overview</CardTitle>
            <CardDescription>Payout history</CardDescription>
          </CardHeader>
          <CardContent>
            {payoutData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={payoutData}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                  <Bar dataKey="amount" fill="#82ca9d" name="Payout" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState icon={DollarSign} title="No payouts yet" description="Payouts will appear here once processed" />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Payouts */}
      {analytics.recent_payouts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Payouts</CardTitle>
            <CardDescription>Last {analytics.recent_payouts.length} payout periods</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {analytics.recent_payouts.map((payout) => (
                <div
                  key={payout.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div>
                    <p className="font-medium">
                      {new Date(payout.period_start).toLocaleDateString()} - {new Date(payout.period_end).toLocaleDateString()}
                    </p>
                    <p className="text-sm text-muted-foreground">Status: {payout.status}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-green-600">{formatCurrency(payout.provider_payout)}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Ratings */}
      {analytics.recent_ratings.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Ratings</CardTitle>
            <CardDescription>Latest feedback from followers</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {analytics.recent_ratings.map((rating) => (
                <div key={rating.id} className="flex items-start gap-3 p-3 border rounded-lg">
                  <div className="flex items-center gap-1">
                    {[...Array(5)].map((_, i) => (
                      <Star
                        key={i}
                        className={`h-4 w-4 ${
                          i < rating.rating ? "fill-yellow-400 text-yellow-400" : "text-muted-foreground"
                        }`}
                      />
                    ))}
                  </div>
                  <div className="flex-1">
                    {rating.comment && <p className="text-sm">{rating.comment}</p>}
                    <p className="text-xs text-muted-foreground mt-1">
                      {new Date(rating.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Analytics Thresholds Section */}
      <div className="mt-8">
        <AnalyticsThresholdManager />
      </div>
    </div>
  );
}
