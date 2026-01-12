/**
 * Trading Safety Status Widget
 * Displays real-time trading safety metrics and kill switch status with premium animations
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Shield, TrendingDown, TrendingUp, DollarSign, Activity, RefreshCw, Zap } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";
import { apiRequest } from "@/lib/queryClient";
import { motion, AnimatePresence } from "framer-motion";

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
    try {
      return await apiRequest<SafetyStatus>('/api/trading-safety/status', { method: 'GET' });
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Failed to fetch safety status');
    }
  },
  
  resetKillSwitch: async (adminOverride: boolean = false): Promise<{ success: boolean }> => {
    try {
      return await apiRequest<{ success: boolean }>(
        `/api/trading-safety/reset-kill-switch?admin_override=${adminOverride}`,
        { method: 'POST' }
      );
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Failed to reset kill switch');
    }
  },
};

export function TradingSafetyStatus() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const { data: safetyStatus, isLoading, error } = useQuery({
    queryKey: ['trading-safety-status'],
    queryFn: tradingSafetyApi.getStatus,
    refetchInterval: 5000, 
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
      <Card className="glass-card overflow-hidden">
        <CardContent className="flex items-center justify-center py-12">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          >
            <RefreshCw className="h-8 w-8 text-primary/40" />
          </motion.div>
        </CardContent>
      </Card>
    );
  }

  if (error || !safetyStatus) {
    return (
      <Card className="border-destructive/50 bg-destructive/5">
        <CardContent className="text-center py-8 text-destructive">
          <AlertTriangle className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="font-medium">Safety Engine Offline</p>
          <p className="text-xs opacity-70">Check backend connection</p>
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
  const isDailyLossWarning = dailyLossPct < -3; 
  const isDailyLossCritical = dailyLossPct < -4; 

  // Risk Sphere Logic: dynamic color and pulse
  const getRiskColor = () => {
    if (kill_switch_active) return "rgba(239, 68, 68, 0.8)"; // Red
    if (isDailyLossCritical) return "rgba(249, 115, 22, 0.8)"; // Orange
    if (isDailyLossWarning) return "rgba(234, 179, 8, 0.8)"; // Yellow
    return "rgba(34, 197, 94, 0.8)"; // Green
  };

  const getRiskGlow = () => {
    if (kill_switch_active) return "0 0 30px rgba(239, 68, 68, 0.4)";
    if (isDailyLossCritical) return "0 0 30px rgba(249, 115, 22, 0.4)";
    if (isDailyLossWarning) return "0 0 30px rgba(234, 179, 8, 0.4)";
    return "0 0 30px rgba(34, 197, 94, 0.4)";
  };

  return (
    <Card className={cn(
      "glass-card border-none transition-all duration-500",
      kill_switch_active && "ring-2 ring-destructive ring-offset-2 ring-offset-background"
    )}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-lg font-bold">
          <div className="flex items-center gap-2">
            <Zap className={cn(
              "h-5 w-5",
              kill_switch_active ? "text-destructive" : "text-primary"
            )} />
            Guardian AI
          </div>
          <Badge className={cn(
            "px-2 py-0.5",
            kill_switch_active ? "bg-destructive text-destructive-foreground" : "bg-primary/20 text-primary border-primary/30"
          )}>
            {kill_switch_active ? "HALTED" : "SECURED"}
          </Badge>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Risk Sphere Visualization */}
        <div className="relative flex justify-center py-4">
          <motion.div
            className="w-32 h-32 rounded-full relative flex items-center justify-center"
            style={{
              background: `radial-gradient(circle at 30% 30%, ${getRiskColor()}, rgba(0,0,0,0.4))`,
              boxShadow: getRiskGlow(),
            }}
            animate={{
              scale: kill_switch_active ? [1, 1.1, 1] : [1, 1.05, 1],
            }}
            transition={{
              duration: kill_switch_active ? 1 : 4,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            <div className="absolute inset-0 rounded-full bg-white/10 blur-[2px] pointer-events-none" />
            <div className="z-10 text-center">
              <div className="text-3xl font-black text-white drop-shadow-md">
                {Math.max(0, 100 - (consecutive_losses * 20) - (kill_switch_active ? 100 : 0))}%
              </div>
              <div className="text-[10px] font-bold text-white/80 tracking-widest uppercase">
                Safety
              </div>
            </div>
            {/* Rotating rings */}
            <motion.div 
              className="absolute -inset-2 border border-white/10 rounded-full"
              animate={{ rotate: 360 }}
              transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
            />
            <motion.div 
              className="absolute -inset-4 border border-white/5 rounded-full"
              animate={{ rotate: -360 }}
              transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
            />
          </motion.div>
        </div>

        {/* Kill Switch Reason */}
        <AnimatePresence>
          {kill_switch_active && (
            <motion.div 
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl overflow-hidden"
            >
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-red-400 leading-tight">Emergency Protocol Engaged</p>
                  <p className="text-xs text-muted-foreground italic">
                    {kill_switch_reason || "Anomaly detected in execution pipeline. Local nodes suspended."}
                  </p>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => resetKillSwitchMutation.mutate(true)}
                    disabled={resetKillSwitchMutation.isPending}
                    className="w-full text-[10px] h-7 uppercase tracking-widest"
                  >
                    {resetKillSwitchMutation.isPending ? "Resetting..." : "Admin Override"}
                  </Button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Detailed Metrics */}
        <div className="grid grid-cols-2 gap-3">
          <div className="stat-card p-3 bg-white/5 border border-white/10 rounded-2xl">
            <div className="text-[10px] text-muted-foreground uppercase font-bold tracking-tighter mb-1">PnL / 24h</div>
            <div className={cn(
              "text-lg font-bold flex items-center gap-1",
              daily_pnl >= 0 ? "text-green-400" : "text-red-400"
            )}>
              {daily_pnl >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
              {daily_pnl >= 0 ? "+" : ""}{Math.abs(daily_pnl).toFixed(2)}
            </div>
          </div>
          <div className="stat-card p-3 bg-white/5 border border-white/10 rounded-2xl">
            <div className="text-[10px] text-muted-foreground uppercase font-bold tracking-tighter mb-1">Session Volume</div>
            <div className="text-lg font-bold flex items-center gap-1 text-primary-foreground">
              <Activity className="h-4 w-4 text-primary" />
              {trades_today} <span className="text-[10px] text-muted-foreground font-normal">tx</span>
            </div>
          </div>
        </div>

        {/* Protection Limits Bar */}
        <div className="space-y-1.5 pt-2">
          <div className="flex justify-between text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
            <span>Risk Exposure</span>
            <span>{Math.abs(dailyLossPct).toFixed(1)}% / {configuration.daily_loss_limit_pct * 100}%</span>
          </div>
          <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden border border-white/10">
            <motion.div 
              className={cn(
                "h-full rounded-full",
                isDailyLossCritical ? "bg-red-500" : isDailyLossWarning ? "bg-yellow-500" : "bg-primary"
              )}
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(100, (Math.abs(dailyLossPct) / (configuration.daily_loss_limit_pct * 100)) * 100)}%` }}
              transition={{ duration: 1 }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
