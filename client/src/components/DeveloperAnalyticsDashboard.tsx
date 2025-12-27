import React, { useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useDeveloperAnalytics, useIndicatorAnalytics } from "@/hooks/useMarketplace";
import { formatCurrency, formatNumber } from "@/lib/formatters";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";
import { Package, DollarSign, Star, TrendingUp, BarChart3, Download, FileDown, FileText } from "lucide-react";
import { useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { exportToJSON, exportToCSV, exportToPDFSimple } from "@/lib/export";
import { useToast } from "@/hooks/use-toast";

export function DeveloperAnalyticsDashboard() {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const { data: analytics, isLoading, error } = useDeveloperAnalytics();

  if (isLoading) {
    return <LoadingSkeleton variant="dashboard" className="h-[600px]" />;
  }

  if (error) {
    return <ErrorRetry error={error} onRetry={() => window.location.reload()} />;
  }

  if (!analytics || analytics.total_indicators === 0) {
    return (
      <EmptyState
        icon={Package}
        title="No Indicators Yet"
        description="Create your first indicator to start tracking analytics"
        action={{
          label: "Create Indicator",
          onClick: () => setLocation("/indicators/create"),
        }}
      />
    );
  }

  // Memoize chart data transformation
  const chartData = useMemo(
    () =>
      analytics.indicators.map((ind) => ({
        name: ind.name.length > 15 ? ind.name.substring(0, 15) + "..." : ind.name,
        purchases: ind.purchases,
        revenue: ind.revenue,
        earnings: ind.developer_earnings,
      })),
    [analytics.indicators]
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Developer Analytics</h2>
          <p className="text-muted-foreground">Track your indicator performance and earnings</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              try {
                if (analytics) {
                  exportToJSON(analytics, { filename: "developer_analytics" });
                  toast({ title: "Exported", description: "Developer analytics exported as JSON" });
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
          {analytics?.indicators && analytics.indicators.length > 0 && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  try {
                    exportToCSV(analytics.indicators, { filename: "indicator_performance" });
                    toast({ title: "Exported", description: "Indicator performance exported as CSV" });
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
                    exportToPDFSimple(analytics.indicators, {
                      filename: "indicator_performance",
                      title: "Developer Analytics Report",
                      columns: ["name", "purchases", "revenue", "developer_earnings", "average_rating"],
                    });
                    toast({ title: "Exported", description: "Analytics exported as PDF" });
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
            <CardTitle className="text-sm font-medium">Total Indicators</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(analytics.total_indicators)}</div>
            <p className="text-xs text-muted-foreground">Published indicators</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Purchases</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(analytics.total_purchases)}</div>
            <p className="text-xs text-muted-foreground">Total sales</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(analytics.total_revenue)}</div>
            <p className="text-xs text-muted-foreground">Gross revenue</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Your Earnings</CardTitle>
            <DollarSign className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{formatCurrency(analytics.developer_earnings)}</div>
            <p className="text-xs text-muted-foreground">70% of revenue</p>
          </CardContent>
        </Card>
      </div>

      {/* Average Rating Card */}
      <Card>
        <CardHeader>
          <CardTitle>Average Rating</CardTitle>
          <CardDescription>Overall performance rating</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Star className="h-8 w-8 fill-yellow-400 text-yellow-400" />
              <div>
                <div className="text-3xl font-bold">{analytics.average_rating.toFixed(1)}</div>
                <p className="text-sm text-muted-foreground">out of 5.0</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Indicator Performance</CardTitle>
          <CardDescription>Purchases and revenue by indicator</CardDescription>
        </CardHeader>
        <CardContent>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip
                  formatter={(value: number, name: string) => {
                    if (name === "earnings" || name === "revenue") {
                      return formatCurrency(value);
                    }
                    return formatNumber(value);
                  }}
                />
                <Bar yAxisId="left" dataKey="purchases" fill="#8884d8" name="Purchases" />
                <Bar yAxisId="right" dataKey="earnings" fill="#82ca9d" name="Your Earnings" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState icon={BarChart3} title="No data" description="No performance data available yet" />
          )}
        </CardContent>
      </Card>

      {/* Indicator List */}
      <Card>
        <CardHeader>
          <CardTitle>Your Indicators</CardTitle>
          <CardDescription>Detailed performance for each indicator</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {analytics.indicators.map((indicator) => (
              <div
                key={indicator.id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
                onClick={() => setLocation(`/indicators/${indicator.id}`)}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold">{indicator.name}</h3>
                    {indicator.average_rating > 0 && (
                      <div className="flex items-center gap-1">
                        <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                        <span className="text-sm">{indicator.average_rating.toFixed(1)}</span>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Purchases</p>
                    <p className="font-bold">{formatNumber(indicator.purchases)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Revenue</p>
                    <p className="font-bold">{formatCurrency(indicator.revenue)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Your Earnings</p>
                    <p className="font-bold text-green-600">{formatCurrency(indicator.developer_earnings)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
