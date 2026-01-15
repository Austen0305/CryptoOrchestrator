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
      <Card className="border-primary/50 transition-all duration-300 hover:bg-primary/5">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-black text-primary uppercase tracking-widest font-mono">Total Portfolio</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-black text-foreground drop-shadow-sm font-mono">{formattedValue}</div>
          <div className={cn("text-xs font-bold flex items-center gap-1 mt-1 px-2 py-0.5 w-fit font-mono", isPositive ? "text-green-400 bg-green-400/10" : "text-red-400 bg-red-400/10")}>
            {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {isPositive ? "+" : ""}{change24h.toFixed(2)}%
          </div>
        </CardContent>
      </Card>

      <Card className="border-blue-500/50 transition-all duration-300 hover:bg-blue-500/10">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-black text-blue-400 uppercase tracking-widest font-mono">Active Bots</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-black flex items-center gap-2 text-foreground font-mono">
            <Activity className="h-5 w-5 text-blue-400" />
            {activeBots}
          </div>
          <div className="text-xs font-bold text-blue-400/80 mt-1 font-mono uppercase">Live Engines</div>
        </CardContent>
      </Card>

      <Card className="border-green-500/50 transition-all duration-300 hover:bg-green-500/10">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-black text-green-400 uppercase tracking-widest font-mono">Total Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-black flex items-center gap-2 text-foreground font-mono">
            <Zap className="h-5 w-5 text-green-400" />
            {totalTrades}
          </div>
          <div className="text-xs font-bold text-green-400/80 mt-1 font-mono uppercase">Executions</div>
        </CardContent>
      </Card>

      <Card className="border-orange-500/50 transition-all duration-300 hover:bg-orange-500/10">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-black text-orange-400 uppercase tracking-widest font-mono">System Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 mb-2">
            <div className="h-2 w-2 rounded-none bg-green-500 animate-pulse shadow-[0_0_8px_#22c55e]" />
            <span className="text-xs font-black text-foreground uppercase font-mono">Operational</span>
          </div>
          <Badge variant="outline" className="text-[10px] font-black border-primary/30 uppercase tracking-tighter font-mono">Latency: 14ms</Badge>
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
    <Card className="border-border/50 shadow-none overflow-hidden h-full">
      <CardHeader className="border-b-2 border-primary/20 bg-background/50">
        <CardTitle className="text-lg font-black tracking-tight text-primary uppercase font-mono">&gt; Live Feed_</CardTitle>
      </CardHeader>
      <CardContent className="pt-4">
        {displayActivities.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground font-medium italic font-mono">
            // Waiting for activity...
          </div>
        ) : (
          <div className="space-y-2">
            {displayActivities.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start gap-3 p-3 border-l-2 border-l-transparent border-t border-b border-r border-border/30 bg-muted/20 hover:border-l-primary hover:bg-primary/5 transition-all duration-200 group font-mono"
              >
                <div className="mt-0.5 p-1.5 rounded-none bg-background/50 border border-border/50 group-hover:border-primary/30 transition-colors">
                  {getActivityIcon(activity.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className={cn("text-xs font-bold tracking-tight uppercase", getStatusColor(activity.status))}>
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
                      activity.status === "success" ? "border-green-500/50 text-green-500 shadow-[0_0_5px_rgba(34,197,94,0.3)]" :
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
  className?: string;
}

export function PerformanceSummary({
  winRate,
  avgProfit,
  totalProfit,
  bestTrade,
  worstTrade,
  className,
}: PerformanceSummaryProps) {
  return (
    <Card className={cn("border-border/50 shadow-none h-full", className)}>
      <CardHeader className="border-b-2 border-primary/20 bg-background/50">
        <CardTitle className="text-lg font-black tracking-tight text-primary uppercase font-mono">&gt; Performance_</CardTitle>
      </CardHeader>
      <CardContent className="pt-6">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
          <div className="space-y-1">
            <div className="text-[10px] font-black text-muted-foreground uppercase tracking-widest font-mono">Win Rate</div>
            <div className="text-2xl font-black text-foreground font-mono">{winRate.toFixed(1)}%</div>
          </div>
          <div className="space-y-1">
            <div className="text-[10px] font-black text-muted-foreground uppercase tracking-widest font-mono">Avg Profit</div>
            <div className={cn("text-2xl font-black font-mono", avgProfit >= 0 ? "text-green-400" : "text-red-400")}>
              ${avgProfit.toFixed(2)}
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-[10px] font-black text-muted-foreground uppercase tracking-widest font-mono">Net Profit</div>
            <div className={cn("text-2xl font-black font-mono", totalProfit >= 0 ? "text-green-400 drop-shadow-[0_0_5px_rgba(34,197,94,0.5)]" : "text-red-400")}>
              ${totalProfit.toFixed(2)}
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-[10px] font-black text-muted-foreground uppercase tracking-widest font-mono">Best Execution</div>
            <div className="text-2xl font-black text-green-400 font-mono">${bestTrade.toFixed(2)}</div>
          </div>
          <div className="space-y-1">
            <div className="text-[10px] font-black text-muted-foreground uppercase tracking-widest font-mono">Max Drawdown</div>
            <div className="text-2xl font-black text-red-400 font-mono">${Math.abs(worstTrade).toFixed(2)}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

