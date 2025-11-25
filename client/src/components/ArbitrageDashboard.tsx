import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TrendingUp, TrendingDown, Activity, Play, Square, Zap, DollarSign, Clock } from "lucide-react";
import { useArbitrageStatus, useArbitrageOpportunities, useArbitrageStats, useStartArbitrage, useStopArbitrage, useExecuteArbitrage } from "@/hooks/useArbitrage";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import { formatCurrency, formatPercentage } from "@/lib/formatters";

export function ArbitrageDashboard() {
  const { isAuthenticated } = useAuth();
  const { data: status, isLoading: statusLoading } = useArbitrageStatus();
  const { data: opportunities, isLoading: opportunitiesLoading } = useArbitrageOpportunities();
  const { data: stats, isLoading: statsLoading } = useArbitrageStats();
  const startArbitrage = useStartArbitrage();
  const stopArbitrage = useStopArbitrage();
  const executeArbitrage = useExecuteArbitrage();

  // Mock data - in production, this would come from the API
  const mockStatus = {
    isRunning: false,
    lastScanTime: new Date(),
    activeOpportunities: 0,
  };

  const mockOpportunities = [
    {
      id: "1",
      pair: "BTC/USD",
      exchangeA: "Kraken",
      exchangeB: "Binance",
      priceA: 47300,
      priceB: 47450,
      spread: 150,
      spreadPercent: 0.32,
      estimatedProfit: 145,
      volume: 1.0,
      timestamp: new Date(),
    },
    {
      id: "2",
      pair: "ETH/USD",
      exchangeA: "Kraken",
      exchangeB: "Coinbase",
      priceA: 2915,
      priceB: 2928,
      spread: 13,
      spreadPercent: 0.45,
      estimatedProfit: 12.5,
      volume: 10.0,
      timestamp: new Date(),
    },
  ];

  const mockStats = {
    totalOpportunities: 45,
    totalExecuted: 12,
    totalProfit: 1250,
    successRate: 92.5,
    averageProfit: 104.17,
  };

  const statusData = status || mockStatus;
  const opportunitiesData = opportunities || mockOpportunities;
  const statsData = stats || mockStats;

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

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-yellow-500" />
              Multi-Exchange Arbitrage
            </CardTitle>
            <CardDescription>
              Real-time arbitrage opportunities across exchanges
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={statusData.isRunning ? "default" : "secondary"}>
              {statusData.isRunning ? "Running" : "Stopped"}
            </Badge>
            {statusData.isRunning ? (
              <Button variant="destructive" size="sm" onClick={handleStop} disabled={stopArbitrage.isPending}>
                <Square className="h-4 w-4 mr-2" />
                Stop
              </Button>
            ) : (
              <Button variant="default" size="sm" onClick={handleStart} disabled={startArbitrage.isPending}>
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
            <div className="text-2xl font-bold text-green-500">{formatCurrency(statsData.totalProfit)}</div>
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
              <div className="text-center py-8 text-muted-foreground">
                Loading opportunities...
              </div>
            ) : opportunitiesData.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No arbitrage opportunities found</p>
                <p className="text-sm">Start scanning to find opportunities across exchanges</p>
              </div>
            ) : (
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Pair</TableHead>
                      <TableHead>Exchange A</TableHead>
                      <TableHead>Exchange B</TableHead>
                      <TableHead>Spread</TableHead>
                      <TableHead>Profit</TableHead>
                      <TableHead>Volume</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {opportunitiesData.map((opp: any) => (
                      <TableRow key={opp.id}>
                        <TableCell className="font-medium">{opp.pair}</TableCell>
                        <TableCell>
                          <div className="text-sm">{opp.exchangeA}</div>
                          <div className="text-xs text-muted-foreground">{formatCurrency(opp.priceA)}</div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">{opp.exchangeB}</div>
                          <div className="text-xs text-muted-foreground">{formatCurrency(opp.priceB)}</div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className={cn(
                              "font-medium",
                              opp.spread > 0 ? "text-green-500" : "text-red-500"
                            )}>
                              {formatCurrency(opp.spread)}
                            </div>
                            <Badge variant="outline" className={cn(
                              opp.spreadPercent > 0.3 ? "border-green-500 text-green-500" : ""
                            )}>
                              {formatPercentage(opp.spreadPercent)}
                            </Badge>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="font-medium text-green-500">
                            {formatCurrency(opp.estimatedProfit)}
                          </div>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {opp.volume}
                        </TableCell>
                        <TableCell>
                          <Button
                            size="sm"
                            onClick={() => handleExecute(opp.id)}
                            disabled={executeArbitrage.isPending}
                          >
                            Execute
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
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
                    <span className="font-bold text-green-500">{formatCurrency(statsData.totalProfit)}</span>
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

