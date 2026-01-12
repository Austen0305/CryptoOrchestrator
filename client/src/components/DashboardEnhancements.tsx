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
      <Card className="glass-premium border-primary/20 hover-lift transition-all duration-300">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-black text-muted-foreground uppercase tracking-widest">Total Portfolio</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-black text-foreground drop-shadow-sm">{formattedValue}</div>
          <div className={cn("text-xs font-bold flex items-center gap-1 mt-1 px-2 py-0.5 rounded-full w-fit", isPositive ? "text-trading-profit bg-trading-profit/10" : "text-trading-loss bg-trading-loss/10")}>
            {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {isPositive ? "+" : ""}{change24h.toFixed(2)}%
          </div>
        </CardContent>
      </Card>

      <Card className="glass-premium border-blue-500/20 hover-lift transition-all duration-300">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-black text-muted-foreground uppercase tracking-widest">Active Bots</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-black flex items-center gap-2 text-foreground">
            <Activity className="h-5 w-5 text-blue-400 drop-shadow-glow-blue" />
            {activeBots}
          </div>
          <div className="text-xs font-bold text-blue-400/80 mt-1">Live Engines</div>
        </CardContent>
      </Card>

      <Card className="glass-premium border-green-500/20 hover-lift transition-all duration-300">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-black text-muted-foreground uppercase tracking-widest">Total Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-black flex items-center gap-2 text-foreground">
            <Zap className="h-5 w-5 text-green-400 drop-shadow-glow" />
            {totalTrades}
          </div>
          <div className="text-xs font-bold text-green-400/80 mt-1">Executions</div>
        </CardContent>
      </Card>

      <Card className="glass-premium border-orange-500/20 hover-lift transition-all duration-300">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-black text-muted-foreground uppercase tracking-widest">System Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 mb-2">
            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse shadow-glow" />
            <span className="text-xs font-black text-foreground uppercase">Operational</span>
          </div>
          <Badge variant="outline" className="text-[10px] font-black border-primary/30 uppercase tracking-tighter">Latency: 14ms</Badge>
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
        return <Zap className="h-4 w-4 text-green-400" />;
      case "bot":
        return <Activity className="h-4 w-4 text-blue-400" />;
      case "alert":
        return <AlertCircle className="h-4 w-4 text-orange-400" />;
      default:
        return <Activity className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case "success":
        return "text-green-400";
      case "warning":
        return "text-orange-400";
      case "error":
        return "text-red-400";
      default:
        return "text-muted-foreground";
    }
  };

  return (
    <Card className="glass-premium border-border/50 shadow-xl overflow-hidden">
      <CardHeader className="border-b border-primary/10">
        <CardTitle className="text-lg font-black tracking-tight text-foreground uppercase">Live Feed</CardTitle>
      </CardHeader>
      <CardContent className="pt-4">
        {displayActivities.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground font-medium italic">
            Waiting for activity...
          </div>
        ) : (
          <div className="space-y-2">
            {displayActivities.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start gap-3 p-3 rounded-xl border border-border/30 bg-muted/20 hover:bg-primary/5 transition-all duration-200 group"
              >
                <div className="mt-0.5 p-1.5 rounded-lg bg-background/50 border border-border/50 group-hover:border-primary/30 transition-colors">
                  {getActivityIcon(activity.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className={cn("text-sm font-bold tracking-tight", getStatusColor(activity.status))}>
                    {activity.message}
                  </p>
                  <p className="text-[10px] text-muted-foreground mt-1 font-mono uppercase tracking-widest">
                    {activity.timestamp}
                  </p>
                </div>
                {activity.status && (
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-[10px] font-black uppercase tracking-tighter",
                      activity.status === "success" ? "border-green-500/50 text-green-500" :
                      activity.status === "warning" ? "border-orange-500/50 text-orange-500" :
                      "border-red-500/50 text-red-500"
                    )}
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
    <Card className="glass-premium border-border/50 shadow-xl">
      <CardHeader className="border-b border-primary/10">
        <CardTitle className="text-lg font-black tracking-tight text-foreground uppercase">Performance Insights</CardTitle>
      </CardHeader>
      <CardContent className="pt-6">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
          <div className="space-y-1">
            <div className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">Win Rate</div>
            <div className="text-2xl font-black text-foreground">{winRate.toFixed(1)}%</div>
          </div>
          <div className="space-y-1">
            <div className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">Avg Profit</div>
            <div className={cn("text-2xl font-black", avgProfit >= 0 ? "text-trading-profit" : "text-trading-loss")}>
              ${avgProfit.toFixed(2)}
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">Net Profit</div>
            <div className={cn("text-2xl font-black", totalProfit >= 0 ? "text-trading-profit shadow-glow-green" : "text-trading-loss")}>
              ${totalProfit.toFixed(2)}
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">Best Execution</div>
            <div className="text-2xl font-black text-trading-profit">${bestTrade.toFixed(2)}</div>
          </div>
          <div className="space-y-1">
            <div className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">Max Drawdown</div>
            <div className="text-2xl font-black text-trading-loss">${Math.abs(worstTrade).toFixed(2)}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

