import React, { useState } from "react";
import { useRoute, useLocation } from "wouter";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Star,
  TrendingUp,
  TrendingDown,
  Users,
  BarChart3,
  ArrowLeft,
  UserPlus,
  Award,
  Target,
  AlertTriangle,
  LineChart,
} from "lucide-react";
import {
  useTraderProfile,
  useRateTrader,
  useFollowTrader,
  type TraderProfile as TraderProfileType,
} from "@/hooks/useMarketplace";
import { useFollowTrader as useCopyFollowTrader } from "@/hooks/useCopyTrading";
import { formatCurrency, formatPercentage } from "@/lib/formatters";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/hooks/useAuth";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export function TraderProfile() {
  const [, params] = useRoute("/marketplace/trader/:traderId");
  const [, setLocation] = useLocation();
  const traderId = params?.traderId;
  const { toast } = useToast();
  const { user } = useAuth();
  const followTrader = useCopyFollowTrader();
  const rateTrader = useRateTrader();

  const [ratingDialogOpen, setRatingDialogOpen] = useState(false);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");

  const { data: trader, isLoading, error, refetch } = useTraderProfile(
    traderId ? parseInt(traderId) : 0
  );

  const handleFollow = async () => {
    if (!trader) return;
    try {
      await followTrader.mutateAsync({
        trader_id: trader.user_id,
        allocation_percentage: 100,
      });
      toast({
        title: "Success",
        description: `Now following ${trader.username || `Trader ${trader.user_id}`}`,
      });
      setLocation("/copy-trading");
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to follow trader",
        variant: "destructive",
      });
    }
  };

  const handleRate = async () => {
    if (!trader) return;
    try {
      await rateTrader.mutateAsync({
        traderId: trader.id,
        rating,
        comment: comment || undefined,
      });
      toast({
        title: "Success",
        description: "Rating submitted successfully",
      });
      setRatingDialogOpen(false);
      setComment("");
      refetch();
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to submit rating",
        variant: "destructive",
      });
    }
  };

  if (isLoading) {
    return <LoadingSkeleton count={5} className="h-32 w-full" />;
  }

  if (error) {
    return (
      <ErrorRetry
        title="Failed to load trader profile"
        message={error instanceof Error ? error.message : "An unexpected error occurred."}
        onRetry={() => refetch()}
        error={error as Error}
      />
    );
  }

  if (!trader) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <p className="text-muted-foreground">Trader not found</p>
          <Button onClick={() => setLocation("/marketplace")} className="mt-4">
            Back to Marketplace
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => setLocation("/marketplace")}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">
            {trader.username || `Trader ${trader.user_id}`}
          </h1>
          {trader.profile_description && (
            <p className="text-muted-foreground mt-1">{trader.profile_description}</p>
          )}
        </div>
        <div className="flex gap-2">
          {/* Show analytics link if user owns this provider */}
          {user && trader && user.id.toString() === trader.user_id.toString() && (
            <Button
              variant="outline"
              onClick={() => setLocation(`/provider-analytics/${trader.id}`)}
            >
              <LineChart className="h-4 w-4 mr-2" />
              View Analytics
            </Button>
          )}
          <Dialog open={ratingDialogOpen} onOpenChange={setRatingDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Star className="h-4 w-4 mr-2" />
                Rate
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Rate This Trader</DialogTitle>
                <DialogDescription>
                  Share your experience following this trader
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Rating</Label>
                  <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => setRating(star)}
                        className="focus:outline-none"
                      >
                        <Star
                          className={`h-6 w-6 ${
                            star <= rating
                              ? "fill-yellow-400 text-yellow-400"
                              : "text-gray-300"
                          }`}
                        />
                      </button>
                    ))}
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Comment (Optional)</Label>
                  <Textarea
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="Share your experience..."
                    rows={4}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setRatingDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleRate} disabled={rateTrader.isPending}>
                  Submit Rating
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          <Button onClick={handleFollow} disabled={followTrader.isPending}>
            <UserPlus className="h-4 w-4 mr-2" />
            Follow Trader
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Return</CardDescription>
            <CardTitle
              className={`text-2xl ${
                trader.total_return >= 0 ? "text-green-600" : "text-red-600"
              }`}
            >
              {formatPercentage(trader.total_return)}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Win Rate</CardDescription>
            <CardTitle className="text-2xl">
              {formatPercentage(trader.win_rate * 100)}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Sharpe Ratio</CardDescription>
            <CardTitle className="text-2xl">{trader.sharpe_ratio.toFixed(2)}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Followers</CardDescription>
            <CardTitle className="text-2xl flex items-center gap-2">
              <Users className="h-5 w-5" />
              {trader.follower_count}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Performance Metrics
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Total Trades</span>
              <span className="font-semibold">{trader.total_trades}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Winning Trades</span>
              <span className="font-semibold text-green-600">{trader.winning_trades}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Total Profit</span>
              <span
                className={`font-semibold ${
                  trader.total_profit >= 0 ? "text-green-600" : "text-red-600"
                }`}
              >
                {formatCurrency(trader.total_profit)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Profit Factor</span>
              <span className="font-semibold">{trader.profit_factor.toFixed(2)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Max Drawdown</span>
              <span className="font-semibold text-red-600">
                {formatPercentage(trader.max_drawdown)}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Award className="h-5 w-5" />
              Reputation
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Average Rating</span>
              <div className="flex items-center gap-2">
                <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                <span className="font-semibold text-lg">
                  {trader.average_rating > 0 ? trader.average_rating.toFixed(1) : "N/A"}
                </span>
              </div>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Total Ratings</span>
              <span className="font-semibold">{trader.total_ratings}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Curator Status</span>
              <Badge
                variant={
                  trader.curator_status === "approved" ? "default" : "secondary"
                }
              >
                {trader.curator_status}
              </Badge>
            </div>
            {trader.last_metrics_update && (
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Last Updated</span>
                <span className="text-sm">
                  {new Date(trader.last_metrics_update).toLocaleDateString()}
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Trading Strategy & Risk */}
      {(trader.trading_strategy || trader.risk_level) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Trading Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {trader.trading_strategy && (
              <div>
                <Label className="text-muted-foreground">Trading Strategy</Label>
                <p className="mt-1">{trader.trading_strategy}</p>
              </div>
            )}
            {trader.risk_level && (
              <div>
                <Label className="text-muted-foreground">Risk Level</Label>
                <Badge variant="outline" className="mt-1">
                  {trader.risk_level}
                </Badge>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Fees */}
      {(trader.subscription_fee || trader.performance_fee_percentage > 0) && (
        <Card>
          <CardHeader>
            <CardTitle>Fees</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {trader.subscription_fee && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Monthly Subscription</span>
                <span className="font-semibold">{formatCurrency(trader.subscription_fee)}</span>
              </div>
            )}
            {trader.performance_fee_percentage > 0 && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Performance Fee</span>
                <span className="font-semibold">
                  {formatPercentage(trader.performance_fee_percentage)}%
                </span>
              </div>
            )}
            {(trader as any).minimum_subscription_amount && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Minimum Subscription</span>
                <span className="font-semibold">
                  {formatCurrency((trader as any).minimum_subscription_amount)}
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
