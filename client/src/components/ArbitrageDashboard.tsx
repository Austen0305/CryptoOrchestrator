import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Play,
  Square,
  Zap,
  DollarSign,
  Clock,
} from "lucide-react";
import {
  useArbitrageStatus,
  useArbitrageOpportunities,
  useArbitrageStats,
  useStartArbitrage,
  useStopArbitrage,
  useExecuteArbitrage,
} from "@/hooks/useArbitrage";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import { formatCurrency, formatPercentage } from "@/lib/formatters";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { EmptyState } from "@/components/EmptyState";
import { ErrorRetry } from "@/components/ErrorRetry";

interface ArbitrageOpportunity {
  id?: string;
  opportunity_id?: string;
  pair?: string;
  symbol?: string;
  exchangeA?: string;
  buy_exchange?: string;
  exchangeB?: string;
  sell_exchange?: string;
  priceA?: number;
  buy_price?: number;
  priceB?: number;
  sell_price?: number;
  spread?: number;
  spread_percent?: number;
  spreadPercent?: number;
  estimatedProfit?: number;
  estimated_profit_usd?: number;
  profit_percent?: number;
  volume?: string;
  volume_available?: number;
  timestamp?: string;
}

interface ArbitrageStatus {
  isRunning: boolean;
  lastScanTime: Date | string;
  activeOpportunities: number;
}

interface ArbitrageStats {
  totalOpportunities: number;
  totalExecuted: number;
  totalProfit: number;
  successRate: number;
  averageProfit: number;
}

export function ArbitrageDashboard() {
  const { isAuthenticated } = useAuth();
  const {
    data: status,
    isLoading: statusLoading,
    error: statusError,
    refetch: refetchStatus,
  } = useArbitrageStatus();
  const {
    data: opportunities,
    isLoading: opportunitiesLoading,
    error: opportunitiesError,
    refetch: refetchOpportunities,
  } = useArbitrageOpportunities();
  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
    refetch: refetchStats,
  } = useArbitrageStats();
  const startArbitrage = useStartArbitrage();
  const stopArbitrage = useStopArbitrage();
  const executeArbitrage = useExecuteArbitrage();

  const hasError = statusError || opportunitiesError || statsError;
  const error = statusError || opportunitiesError || statsError;

  // Use real API data, with loading states and proper typing
  const statusData: ArbitrageStatus = (status as ArbitrageStatus) || {
    isRunning: false,
    lastScanTime: new Date(),
    activeOpportunities: 0,
  };
  const opportunitiesData: ArbitrageOpportunity[] = (opportunities as ArbitrageOpportunity[]) || [];
  const statsData: ArbitrageStats = (stats as ArbitrageStats) || {
    totalOpportunities: 0,
    totalExecuted: 0,
    totalProfit: 0,
    successRate: 0,
    averageProfit: 0,
  };

  const handleStart = async () => {
    await startArbitrage.mutateAsync();
  };

  const handleStop = async () => {
    await stopArbitrage.mutateAsync();
  };

  const handleExecute = async (opportunityId: string) => {
    await executeArbitrage.mutateAsync(opportunityId);
  };

  if (!isAuthenticated) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Arbitrage Dashboard</CardTitle>
          <CardDescription>Please log in to access arbitrage features</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (statusLoading || opportunitiesLoading || statsLoading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-yellow-500" />
            Cross-DEX Arbitrage
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <LoadingSkeleton count={4} className="h-20 w-full" />
            </div>
            <LoadingSkeleton count={1} className="h-64 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (hasError) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-yellow-500" />
            Cross-DEX Arbitrage
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorRetry
            title="Failed to load arbitrage data"
            onRetry={() => {
              refetchStatus();
              refetchOpportunities();
              refetchStats();
            }}
            error={error as Error}
          />
        </CardContent>
      </Card>
    );
  }

  if (opportunitiesData.length === 0 && !statusData.isRunning) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-yellow-500" />
            Cross-DEX Arbitrage
          </CardTitle>
          <CardDescription>Real-time arbitrage opportunities across exchanges</CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={Zap}
            title="No Arbitrage Opportunities"
            description="Start the arbitrage scanner to find opportunities across DEX aggregators"
            action={{
              label: "Start Scanner",
              onClick: handleStart,
            }}
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-yellow-500" />
              Cross-DEX Arbitrage
            </CardTitle>
            <CardDescription>
              Real-time arbitrage opportunities across DEX aggregators
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={statusData.isRunning ? "default" : "secondary"}>
              {statusData.isRunning ? "Running" : "Stopped"}
            </Badge>
            {statusData.isRunning ? (
              <Button
                variant="destructive"
                size="sm"
                onClick={handleStop}
                disabled={stopArbitrage.isPending}
              >
                <Square className="h-4 w-4 mr-2" />
                Stop
              </Button>
            ) : (
              <Button
                variant="default"
                size="sm"
                onClick={handleStart}
                disabled={startArbitrage.isPending}
              >
                <Play className="h-4 w-4 mr-2" />
                Start
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Stats Summary */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="rounded-lg border bg-card p-4">
            <div className="text-sm font-medium text-muted-foreground">Total Opportunities</div>
            <div className="text-2xl font-bold">{statsData.totalOpportunities}</div>
          </div>
          <div className="rounded-lg border bg-card p-4">
            <div className="text-sm font-medium text-muted-foreground">Executed</div>
            <div className="text-2xl font-bold text-green-500">{statsData.totalExecuted}</div>
          </div>
          <div className="rounded-lg border bg-card p-4">
            <div className="text-sm font-medium text-muted-foreground">Total Profit</div>
            <div className="text-2xl font-bold text-green-500">
              {formatCurrency(statsData.totalProfit)}
            </div>
          </div>
          <div className="rounded-lg border bg-card p-4">
            <div className="text-sm font-medium text-muted-foreground">Success Rate</div>
            <div className="text-2xl font-bold">{formatPercentage(statsData.successRate)}</div>
          </div>
        </div>

        <Tabs defaultValue="opportunities" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="opportunities">Opportunities</TabsTrigger>
            <TabsTrigger value="stats">Statistics</TabsTrigger>
          </TabsList>

          <TabsContent value="opportunities" className="space-y-4">
            {opportunitiesLoading ? (
              <LoadingSkeleton count={5} className="h-12 w-full" />
            ) : opportunitiesData.length === 0 ? (
              <EmptyState
                icon={Activity}
                title="No arbitrage opportunities found"
                description="Start scanning to find opportunities across exchanges"
              />
            ) : (
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Pair</TableHead>
                      <TableHead>DEX A</TableHead>
                      <TableHead>DEX B</TableHead>
                      <TableHead>Spread</TableHead>
                      <TableHead>Profit</TableHead>
                      <TableHead>Volume</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {opportunitiesData.map((opp: ArbitrageOpportunity) => {
                      const opportunityId = opp.id || opp.opportunity_id || "";
                      const pair = opp.pair || opp.symbol || "N/A";
                      const buyExchange = opp.exchangeA || opp.buy_exchange || "N/A";
                      const sellExchange = opp.exchangeB || opp.sell_exchange || "N/A";
                      const buyPrice = opp.priceA || opp.buy_price || 0;
                      const sellPrice = opp.priceB || opp.sell_price || 0;
                      const spread = opp.spread ?? sellPrice - buyPrice;
                      const spreadPercent =
                        opp.spreadPercent || opp.spread_percent || (spread / buyPrice) * 100;
                      const estimatedProfit = opp.estimatedProfit || opp.estimated_profit_usd || 0;
                      const volume =
                        opp.volume || (opp.volume_available ? `${opp.volume_available}` : "N/A");

                      return (
                        <TableRow key={opportunityId}>
                          <TableCell className="font-medium">{pair}</TableCell>
                          <TableCell>
                            <div className="text-sm">{buyExchange}</div>
                            <div className="text-xs text-muted-foreground">
                              {formatCurrency(buyPrice)}
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="text-sm">{sellExchange}</div>
                            <div className="text-xs text-muted-foreground">
                              {formatCurrency(sellPrice)}
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <div
                                className={cn(
                                  "font-medium",
                                  spread > 0 ? "text-green-500" : "text-red-500"
                                )}
                              >
                                {formatCurrency(spread)}
                              </div>
                              <Badge
                                variant="outline"
                                className={cn(
                                  spreadPercent > 0.3 ? "border-green-500 text-green-500" : ""
                                )}
                              >
                                {formatPercentage(spreadPercent)}
                              </Badge>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="font-medium text-green-500">
                              {formatCurrency(estimatedProfit)}
                            </div>
                          </TableCell>
                          <TableCell className="text-muted-foreground">{volume}</TableCell>
                          <TableCell>
                            <Button
                              size="sm"
                              onClick={() => handleExecute(opportunityId)}
                              disabled={executeArbitrage.isPending}
                            >
                              Execute
                            </Button>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
          </TabsContent>

          <TabsContent value="stats" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <DollarSign className="h-4 w-4" />
                    Profit Metrics
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Total Profit</span>
                    <span className="font-bold text-green-500">
                      {formatCurrency(statsData.totalProfit)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Average Profit</span>
                    <span className="font-medium">{formatCurrency(statsData.averageProfit)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Success Rate</span>
                    <span className="font-medium">{formatPercentage(statsData.successRate)}</span>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    Activity Metrics
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Total Opportunities</span>
                    <span className="font-bold">{statsData.totalOpportunities}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Executed</span>
                    <span className="font-medium text-green-500">{statsData.totalExecuted}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Pending</span>
                    <span className="font-medium">
                      {statsData.totalOpportunities - statsData.totalExecuted}
                    </span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
