import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Users, Copy, TrendingUp, UserPlus, UserMinus } from "lucide-react";
import { useFollowedTraders, useFollowTrader, useUnfollowTrader, useCopyTradingStats } from "@/hooks/useCopyTrading";
import { formatCurrency, formatPercentage } from "@/lib/formatters";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";
import { useToast } from "@/hooks/use-toast";

interface FollowedTrader {
  trader_id: number;
  username?: string;
  allocation_percentage: number;
  status: "active" | "inactive" | "paused";
}

interface FollowedTradersResponse {
  traders: FollowedTrader[];
}

export function CopyTrading() {
  const { data: followedTraders, isLoading, error, refetch } = useFollowedTraders();
  const { data: stats, isLoading: statsLoading, error: statsError } = useCopyTradingStats();
  const followTrader = useFollowTrader();
  const unfollowTrader = useUnfollowTrader();
  const { toast } = useToast();
  
  const [traderId, setTraderId] = useState("");
  const [allocation, setAllocation] = useState("100");
  
  const handleFollow = async () => {
    if (!traderId) {
      toast({
        title: "Validation Error",
        description: "Please enter a trader ID",
        variant: "destructive",
      });
      return;
    }
    try {
      await followTrader.mutateAsync({
        trader_id: parseInt(traderId),
        allocation_percentage: parseFloat(allocation),
      });
      setTraderId("");
      setAllocation("100");
      toast({
        title: "Success",
        description: "Successfully followed trader",
      });
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to follow trader",
        variant: "destructive",
      });
    }
  };
  
  const handleUnfollow = async (traderId: number) => {
    try {
      await unfollowTrader.mutateAsync(traderId);
      toast({
        title: "Success",
        description: "Successfully unfollowed trader",
      });
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to unfollow trader",
        variant: "destructive",
      });
    }
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Copy className="h-5 w-5" />
          Copy Trading
        </CardTitle>
        <CardDescription>
          Follow top traders and automatically copy their trades
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Stats */}
        {statsLoading ? (
          <LoadingSkeleton count={4} className="h-20 w-full" />
        ) : statsError ? (
          <ErrorRetry
            title="Failed to load stats"
            message={statsError instanceof Error ? statsError.message : "An unexpected error occurred."}
            onRetry={() => window.location.reload()}
            error={statsError as Error}
          />
        ) : stats ? (
          <div className="grid grid-cols-4 gap-4">
            <div className="p-4 rounded-lg border">
              <div className="text-sm text-muted-foreground">Copied Trades</div>
              <div className="text-2xl font-bold">{stats.total_copied_trades}</div>
            </div>
            <div className="p-4 rounded-lg border">
              <div className="text-sm text-muted-foreground">Total Profit</div>
              <div className="text-2xl font-bold">{formatCurrency(stats.total_profit)}</div>
            </div>
            <div className="p-4 rounded-lg border">
              <div className="text-sm text-muted-foreground">Active Copies</div>
              <div className="text-2xl font-bold">{stats.active_copies}</div>
            </div>
            <div className="p-4 rounded-lg border">
              <div className="text-sm text-muted-foreground">Followed Traders</div>
              <div className="text-2xl font-bold">{stats.followed_traders}</div>
            </div>
          </div>
        ) : null}
        
        {/* Follow New Trader */}
        <div className="p-4 rounded-lg border space-y-3">
          <h3 className="font-semibold flex items-center gap-2">
            <UserPlus className="h-4 w-4" />
            Follow a Trader
          </h3>
          <div className="flex gap-2">
            <Input
              placeholder="Trader ID"
              value={traderId}
              onChange={(e) => setTraderId(e.target.value)}
              type="number"
            />
            <Input
              placeholder="Allocation %"
              value={allocation}
              onChange={(e) => setAllocation(e.target.value)}
              type="number"
              className="w-32"
            />
            <Button onClick={handleFollow} disabled={followTrader.isPending}>
              Follow
            </Button>
          </div>
        </div>
        
        {/* Followed Traders */}
        <div>
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Users className="h-4 w-4" />
            Followed Traders
          </h3>
          {isLoading ? (
            <LoadingSkeleton count={5} className="h-12 w-full mb-2" />
          ) : error ? (
            <ErrorRetry
              title="Failed to load followed traders"
              message={error instanceof Error ? error.message : "An unexpected error occurred."}
              onRetry={() => refetch()}
              error={error as Error}
            />
          ) : followedTraders?.traders && followedTraders.traders.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Trader</TableHead>
                  <TableHead>Allocation</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {followedTraders.traders.map((trader: FollowedTrader) => (
                  <TableRow key={trader.trader_id}>
                    <TableCell>{trader.username || `Trader ${trader.trader_id}`}</TableCell>
                    <TableCell>{trader.allocation_percentage}%</TableCell>
                    <TableCell>
                      <Badge variant={trader.status === "active" ? "default" : "secondary"}>
                        {trader.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleUnfollow(trader.trader_id)}
                        disabled={unfollowTrader.isPending}
                      >
                        <UserMinus className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <EmptyState
              icon={Users}
              title="No followed traders yet"
              description="Follow top traders to start copying their trades automatically."
            />
          )}
        </div>
      </CardContent>
    </Card>
  );
}

