import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Trophy, TrendingUp, Target, Award } from "lucide-react";
import { useLeaderboard, useMyRank } from "@/hooks/useLeaderboard";
import { formatCurrency, formatPercentage } from "@/lib/formatters";
import { useTradingMode } from "@/contexts/TradingModeContext";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";

export function Leaderboard() {
  const { mode } = useTradingMode();
  const normalizedMode = mode === "live" ? "real" : mode;
  const [metric, setMetric] = useState("total_pnl");
  const [period, setPeriod] = useState("all_time");
  
  const { data, isLoading, error, refetch } = useLeaderboard(metric, period, normalizedMode);
  const { data: myRank, isLoading: myRankLoading, error: myRankError } = useMyRank(metric, period, normalizedMode);
  
  const getRankColor = (rank: number) => {
    if (rank === 1) return "text-yellow-500";
    if (rank === 2) return "text-gray-400";
    if (rank === 3) return "text-amber-600";
    return "text-muted-foreground";
  };
  
  const getRankIcon = (rank: number) => {
    if (rank === 1) return <Trophy className="h-5 w-5 text-yellow-500" />;
    if (rank === 2) return <Trophy className="h-5 w-5 text-gray-400" />;
    if (rank === 3) return <Trophy className="h-5 w-5 text-amber-600" />;
    return <Award className="h-4 w-4 text-muted-foreground" />;
  };
  
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5" />
              Trader Leaderboard
            </CardTitle>
            <CardDescription>
              Top traders ranked by performance
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Select value={metric} onValueChange={setMetric}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="total_pnl">Total P&L</SelectItem>
                <SelectItem value="win_rate">Win Rate</SelectItem>
                <SelectItem value="profit_factor">Profit Factor</SelectItem>
                <SelectItem value="sharpe_ratio">Sharpe Ratio</SelectItem>
              </SelectContent>
            </Select>
            <Select value={period} onValueChange={setPeriod}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="24h">24h</SelectItem>
                <SelectItem value="7d">7d</SelectItem>
                <SelectItem value="30d">30d</SelectItem>
                <SelectItem value="all_time">All Time</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading || myRankLoading ? (
          <LoadingSkeleton count={10} className="h-16 w-full mb-2" />
        ) : error || myRankError ? (
          <ErrorRetry
            title="Failed to load leaderboard"
            message={error instanceof Error ? error.message : myRankError instanceof Error ? myRankError.message : "An unexpected error occurred."}
            onRetry={() => { refetch(); }}
            error={(error || myRankError) as Error}
          />
        ) : (
          <div className="space-y-4">
            {/* My Rank */}
            {myRank && (
              <div className="p-4 bg-muted rounded-lg border-2 border-primary">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl font-bold">{myRank.rank}</span>
                    <div>
                      <div className="font-semibold">{myRank.username}</div>
                      <div className="text-sm text-muted-foreground">Your Rank</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">
                      {metric === "total_pnl" && formatCurrency(myRank.total_pnl)}
                      {metric === "win_rate" && formatPercentage(myRank.win_rate)}
                      {metric === "profit_factor" && myRank.profit_factor.toFixed(2)}
                      {metric === "sharpe_ratio" && myRank.sharpe_ratio.toFixed(2)}
                    </div>
                    <div className="text-sm text-muted-foreground">{metric.replace("_", " ")}</div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Leaderboard */}
            {data?.leaderboard && data.leaderboard.length > 0 ? (
              <div className="space-y-2">
                {data.leaderboard.map((entry, index) => {
                  const rank = index + 1;
                  return (
                    <div
                      key={entry.user_id}
                      className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50"
                    >
                      <div className="flex items-center gap-3 flex-1">
                        <div className={`font-bold text-lg w-8 ${getRankColor(rank)}`}>
                          {rank}
                        </div>
                        {getRankIcon(rank)}
                        <div className="flex-1">
                          <div className="font-semibold">{entry.username}</div>
                          <div className="text-sm text-muted-foreground">
                            {entry.total_trades} trades • {formatPercentage(entry.win_rate)} win rate
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold">
                          {metric === "total_pnl" && formatCurrency(entry.total_pnl)}
                          {metric === "win_rate" && formatPercentage(entry.win_rate)}
                          {metric === "profit_factor" && entry.profit_factor.toFixed(2)}
                          {metric === "sharpe_ratio" && entry.sharpe_ratio.toFixed(2)}
                        </div>
                        {metric === "total_pnl" && (
                          <Badge variant={entry.total_pnl >= 0 ? "default" : "destructive"}>
                            {entry.total_pnl >= 0 ? "+" : ""}{formatPercentage((entry.total_pnl / 10000) * 100)}
                          </Badge>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <EmptyState
                icon={Trophy}
                title="No leaderboard data available"
                description="The leaderboard is currently empty. Start trading to see rankings."
              />
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

