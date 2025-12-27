/**
 * Trading Safety Status Widget
 * Displays real-time trading safety metrics and kill switch status
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Shield, TrendingDown, TrendingUp, DollarSign, Activity, RefreshCw } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

interface SafetyConfiguration {
  max_position_size_pct: number;
  daily_loss_limit_pct: number;
  max_consecutive_losses: number;
  min_account_balance: number;
  max_slippage_pct: number;
  max_portfolio_heat: number;
}

interface SafetyStatus {
  kill_switch_active: boolean;
  kill_switch_reason: string | null;
  daily_pnl: number;
  trades_today: number;
  consecutive_losses: number;
  last_reset: string;
  configuration: SafetyConfiguration;
}

const tradingSafetyApi = {
  getStatus: async (): Promise<SafetyStatus> => {
    const response = await fetch('/api/trading-safety/status');
    if (!response.ok) throw new Error('Failed to fetch safety status');
    return response.json();
  },
  
  resetKillSwitch: async (adminOverride: boolean = false): Promise<{ success: boolean }> => {
    const response = await fetch(`/api/trading-safety/reset-kill-switch?admin_override=${adminOverride}`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to reset kill switch');
    return response.json();
  },
};

export function TradingSafetyStatus() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const { data: safetyStatus, isLoading, error } = useQuery({
    queryKey: ['trading-safety-status'],
    queryFn: tradingSafetyApi.getStatus,
    refetchInterval: 5000, // Update every 5 seconds
  });

  const resetKillSwitchMutation = useMutation({
    mutationFn: (adminOverride: boolean) => tradingSafetyApi.resetKillSwitch(adminOverride),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trading-safety-status'] });
      toast({
        title: "Kill Switch Reset",
        description: "Trading has been re-enabled. Monitor carefully.",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Reset Failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Trading Safety
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !safetyStatus) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Trading Safety
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-4 text-muted-foreground">
            Unable to load safety status
          </div>
        </CardContent>
      </Card>
    );
  }

  const {
    kill_switch_active,
    kill_switch_reason,
    daily_pnl,
    trades_today,
    consecutive_losses,
    configuration,
  } = safetyStatus;

  // Calculate daily loss percentage (assuming $10k default balance for display)
  const dailyLossPct = (daily_pnl / 10000) * 100;
  const isDailyLossWarning = dailyLossPct < -3; // Warning at -3%
  const isDailyLossCritical = dailyLossPct < -4; // Critical at -4%

  return (
    <Card className={cn(kill_switch_active && "border-destructive")}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className={cn(
              "h-5 w-5",
              kill_switch_active ? "text-destructive" : "text-green-500"
            )} />
            Trading Safety
          </div>
          <Badge variant={kill_switch_active ? "destructive" : "default"}>
            {kill_switch_active ? "STOPPED" : "ACTIVE"}
          </Badge>
        </CardTitle>
        <CardDescription>
          Real-time risk monitoring and protection
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Kill Switch Alert */}
        {kill_switch_active && (
          <div className="p-4 bg-destructive/10 border border-destructive rounded-lg space-y-2">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold text-destructive">Kill Switch Active</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {kill_switch_reason || "Trading has been halted for safety"}
                </p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => resetKillSwitchMutation.mutate(true)}
              disabled={resetKillSwitchMutation.isPending}
              className="w-full"
            >
              {resetKillSwitchMutation.isPending ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Resetting...
                </>
              ) : (
                "Reset Kill Switch (Admin Override)"
              )}
            </Button>
          </div>
        )}

        {/* Daily P&L */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-medium">
              <DollarSign className="h-4 w-4" />
              Daily P&L
            </div>
            <div className={cn(
              "font-semibold",
              daily_pnl >= 0 ? "text-green-500" : "text-red-500"
            )}>
              {daily_pnl >= 0 ? "+" : ""}${daily_pnl.toFixed(2)}
              <span className="text-xs ml-1">
                ({dailyLossPct >= 0 ? "+" : ""}{dailyLossPct.toFixed(2)}%)
              </span>
            </div>
          </div>
          
          {/* Loss Warning */}
          {isDailyLossWarning && !kill_switch_active && (
            <div className={cn(
              "text-xs p-2 rounded",
              isDailyLossCritical ? "bg-red-50 text-red-700" : "bg-yellow-50 text-yellow-700"
            )}>
              {isDailyLossCritical ? "⚠️ Critical: " : "⚠ Warning: "}
              Approaching daily loss limit ({Math.abs(dailyLossPct).toFixed(1)}% of {configuration.daily_loss_limit_pct * 100}%)
            </div>
          )}
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="text-sm text-muted-foreground">Trades Today</div>
            <div className="text-2xl font-bold flex items-center gap-1">
              <Activity className="h-4 w-4" />
              {trades_today}
            </div>
          </div>
          
          <div className="space-y-1">
            <div className="text-sm text-muted-foreground">Consecutive Losses</div>
            <div className={cn(
              "text-2xl font-bold flex items-center gap-1",
              consecutive_losses >= 2 && "text-red-500"
            )}>
              <TrendingDown className="h-4 w-4" />
              {consecutive_losses}
              <span className="text-xs text-muted-foreground ml-1">
                / {configuration.max_consecutive_losses}
              </span>
            </div>
          </div>
        </div>

        {/* Configuration Summary */}
        <div className="pt-4 border-t space-y-2">
          <div className="text-xs font-medium text-muted-foreground uppercase">
            Protection Limits
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Max Position:</span>
              <span className="font-medium">{configuration.max_position_size_pct * 100}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Max Loss:</span>
              <span className="font-medium">{configuration.daily_loss_limit_pct * 100}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Max Slippage:</span>
              <span className="font-medium">{configuration.max_slippage_pct * 100}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Portfolio Heat:</span>
              <span className="font-medium">{configuration.max_portfolio_heat * 100}%</span>
            </div>
          </div>
        </div>

        {/* Status Footer */}
        <div className="flex items-center justify-between pt-2 text-xs text-muted-foreground">
          <div>Last reset: {new Date(safetyStatus.last_reset).toLocaleTimeString()}</div>
          <div className="flex items-center gap-1">
            <div className={cn(
              "h-2 w-2 rounded-full",
              kill_switch_active ? "bg-red-500 animate-pulse" : "bg-green-500"
            )} />
            {kill_switch_active ? "Halted" : "Monitoring"}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
