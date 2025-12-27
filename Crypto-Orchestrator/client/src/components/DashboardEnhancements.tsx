/**
 * Dashboard Enhancement Components
 * Provides enhanced UI components for better dashboard experience
 */

import React, { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Activity, Zap, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface QuickStatsProps {
  totalValue: number;
  change24h: number;
  activeBots: number;
  totalTrades: number;
  className?: string;
}

export function QuickStats({
  totalValue,
  change24h,
  activeBots,
  totalTrades,
  className,
}: QuickStatsProps) {
  const isPositive = change24h >= 0;
  const formattedValue = useMemo(
    () => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(totalValue),
    [totalValue]
  );

  return (
    <div className={cn("grid grid-cols-1 md:grid-cols-4 gap-4", className)}>
      <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-medium text-muted-foreground">Total Portfolio</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formattedValue}</div>
          <div className={cn("text-sm flex items-center gap-1 mt-1", isPositive ? "text-green-500" : "text-red-500")}>
            {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {isPositive ? "+" : ""}{change24h.toFixed(2)}%
          </div>
        </CardContent>
      </Card>

      <Card className="border-2 border-blue-500/20 bg-gradient-to-br from-blue-500/5 to-transparent">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-medium text-muted-foreground">Active Bots</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-500" />
            {activeBots}
          </div>
          <div className="text-sm text-muted-foreground mt-1">Running</div>
        </CardContent>
      </Card>

      <Card className="border-2 border-green-500/20 bg-gradient-to-br from-green-500/5 to-transparent">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-medium text-muted-foreground">Total Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold flex items-center gap-2">
            <Zap className="h-5 w-5 text-green-500" />
            {totalTrades}
          </div>
          <div className="text-sm text-muted-foreground mt-1">All time</div>
        </CardContent>
      </Card>

      <Card className="border-2 border-orange-500/20 bg-gradient-to-br from-orange-500/5 to-transparent">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-medium text-muted-foreground">Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-sm font-semibold">All Systems Operational</span>
          </div>
          <Badge variant="outline" className="mt-2">Live</Badge>
        </CardContent>
      </Card>
    </div>
  );
}

interface RecentActivityProps {
  activities: Array<{
    id: string;
    type: "trade" | "bot" | "alert" | "system";
    message: string;
    timestamp: string;
    status?: "success" | "warning" | "error";
  }>;
  maxItems?: number;
}

export function RecentActivity({ activities, maxItems = 5 }: RecentActivityProps) {
  const displayActivities = useMemo(
    () => (activities && Array.isArray(activities) ? activities.slice(0, maxItems) : []),
    [activities, maxItems]
  );

  const getActivityIcon = (type: string) => {
    switch (type) {
      case "trade":
        return <Zap className="h-4 w-4 text-green-500" />;
      case "bot":
        return <Activity className="h-4 w-4 text-blue-500" />;
      case "alert":
        return <AlertCircle className="h-4 w-4 text-orange-500" />;
      default:
        return <Activity className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case "success":
        return "text-green-500";
      case "warning":
        return "text-orange-500";
      case "error":
        return "text-red-500";
      default:
        return "text-muted-foreground";
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg font-bold">Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        {displayActivities.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No recent activity
          </div>
        ) : (
          <div className="space-y-3">
            {displayActivities.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start gap-3 p-3 rounded-lg border border-border/50 hover:bg-accent/30 transition-colors"
              >
                <div className="mt-0.5">{getActivityIcon(activity.type)}</div>
                <div className="flex-1 min-w-0">
                  <p className={cn("text-sm font-medium", getStatusColor(activity.status))}>
                    {activity.message}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {activity.timestamp}
                  </p>
                </div>
                {activity.status && (
                  <Badge
                    variant={
                      activity.status === "success"
                        ? "default"
                        : activity.status === "warning"
                        ? "secondary"
                        : "destructive"
                    }
                    className="text-xs"
                  >
                    {activity.status}
                  </Badge>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface PerformanceSummaryProps {
  winRate: number;
  avgProfit: number;
  totalProfit: number;
  bestTrade: number;
  worstTrade: number;
}

export function PerformanceSummary({
  winRate,
  avgProfit,
  totalProfit,
  bestTrade,
  worstTrade,
}: PerformanceSummaryProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg font-bold">Performance Summary</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div>
            <div className="text-xs text-muted-foreground mb-1">Win Rate</div>
            <div className="text-2xl font-bold">{winRate.toFixed(1)}%</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-1">Avg Profit</div>
            <div className={cn("text-2xl font-bold", avgProfit >= 0 ? "text-green-500" : "text-red-500")}>
              ${avgProfit.toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-1">Total Profit</div>
            <div className={cn("text-2xl font-bold", totalProfit >= 0 ? "text-green-500" : "text-red-500")}>
              ${totalProfit.toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-1">Best Trade</div>
            <div className="text-2xl font-bold text-green-500">${bestTrade.toFixed(2)}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-1">Worst Trade</div>
            <div className="text-2xl font-bold text-red-500">${worstTrade.toFixed(2)}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

