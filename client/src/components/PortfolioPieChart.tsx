import React, { useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
import { usePortfolio } from "@/hooks/useApi";
import type { Portfolio } from "@shared/schema";
import { formatCurrency, formatPercentage } from "@/lib/formatters";
import { TrendingUp, RefreshCw, DollarSign, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip as UITooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { EmptyState } from "@/components/EmptyState";

const COLORS = [
  "#8884d8", "#82ca9d", "#ffc658", "#ff7c7c", "#8dd1e1",
  "#d084d0", "#ffb347", "#87ceeb", "#ff6b6b", "#4ecdc4",
  "#95e1d3", "#f38181", "#aa96da", "#fcbad3", "#a8dadc"
];

export function PortfolioPieChart() {
  const { data: portfolio, isLoading } = usePortfolio("paper");

  const chartData = useMemo(() => {
    if (!portfolio?.positions) return [];

    // Portfolio.positions is Record<string, Position> from schema
    const positions = portfolio.positions;

    interface AssetWithoutPercentage {
      symbol: string;
      amount: number;
      value: number;
      price: number;
    }

    const assets: AssetWithoutPercentage[] = Object.entries(positions)
      .filter(([_, position]) => position && position.totalValue > 0)
      .map(([symbol, position]) => {
        const amount = position.amount;
        const value = position.totalValue;
        const price = position.currentPrice;
        return {
          symbol: position.asset || symbol,
          amount,
          value,
          price
        };
      })
      .filter(asset => asset.value > 0)
      .sort((a, b) => b.value - a.value);

    const portfolioTotal = portfolio?.totalBalance ?? 0;
    const totalValue = assets.reduce((sum, asset) => sum + asset.value, 0) || portfolioTotal || 1;

    return assets.map(asset => ({
      name: asset.symbol,
      value: asset.value,
      percentage: (asset.value / totalValue) * 100,
      amount: asset.amount,
      color: COLORS[assets.indexOf(asset) % COLORS.length]
    }));
  }, [portfolio]);

  const totalValue = useMemo(() => {
    const portfolioTotal = portfolio?.totalBalance ?? 0;
    return chartData.reduce((sum, asset) => sum + asset.value, 0) || portfolioTotal || 0;
  }, [chartData, portfolio]);

  const largestAsset = chartData.length > 0 ? chartData[0] : null;
  const top3Assets = chartData.slice(0, 3);

  interface TooltipProps {
    active?: boolean;
    payload?: Array<{
      payload: {
        name: string;
        value: number;
        percentage: number;
        amount: number;
        color?: string;
      };
    }>;
  }

  const CustomTooltip = ({ active, payload }: TooltipProps) => {
    if (active && payload && payload.length && payload[0]) {
      const data = payload[0].payload;
      return (
        <div className="rounded-lg border bg-background p-3 shadow-md">
          <div className="font-medium">{data.name}</div>
          <div className="text-sm text-muted-foreground">
            Value: {formatCurrency(data.value)}
          </div>
          <div className="text-sm text-muted-foreground">
            Allocation: {formatPercentage(data.percentage)}
          </div>
          <div className="text-sm text-muted-foreground">
            Amount: {data.amount.toFixed(6)}
          </div>
        </div>
      );
    }
    return null;
  };

  interface LabelProps {
    cx: number;
    cy: number;
    midAngle: number;
    innerRadius: number;
    outerRadius: number;
    percentage: number;
  }

  const CustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percentage }: LabelProps) => {
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    // Only show label if percentage is significant
    if (percentage < 5) return null;

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor={x > cx ? "start" : "end"}
        dominantBaseline="central"
        fontSize={12}
        fontWeight="bold"
      >
        {`${percentage.toFixed(1)}%`}
      </text>
    );
  };

  const handleRebalance = () => {
    // In production, this would trigger portfolio rebalancing
    alert("Rebalancing functionality will open rebalancing wizard");
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Portfolio Allocation</CardTitle>
          <CardDescription>Loading portfolio data...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center">
            <LoadingSkeleton variant="card" className="w-48 h-48 rounded-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Portfolio Allocation</CardTitle>
          <CardDescription>Your portfolio allocation breakdown</CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={AlertCircle}
            title="No assets in portfolio yet"
            description="Start trading to see your portfolio allocation"
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
              <TrendingUp className="h-5 w-5" />
              Portfolio Allocation
            </CardTitle>
            <CardDescription>
              Interactive breakdown of your portfolio by asset
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <TooltipProvider>
              <UITooltip>
                <TooltipTrigger asChild>
                  <Button variant="outline" size="sm">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Refresh
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Refresh portfolio data</p>
                </TooltipContent>
              </UITooltip>
            </TooltipProvider>
            <Button variant="default" size="sm" onClick={handleRebalance}>
              Rebalance
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Total Value */}
        <div className="text-center">
          <div className="text-sm font-medium text-muted-foreground mb-1">Total Portfolio Value</div>
          <div className="text-3xl font-bold">{formatCurrency(totalValue)}</div>
          <div className="flex items-center justify-center gap-2 mt-2">
            <DollarSign className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">
              {chartData.length} asset{chartData.length !== 1 ? "s" : ""}
            </span>
          </div>
        </div>

        {/* Pie Chart */}
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={CustomLabel}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color || COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(value, entry: any) => (
                  <span style={{ color: entry.color }} className="text-sm">
                    {value} ({entry.payload?.percentage ? formatPercentage(entry.payload.percentage) : '0%'})
                  </span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Top Holdings */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-sm">Top Holdings</h4>
            <Badge variant="outline">{chartData.length} Total</Badge>
          </div>
          <div className="space-y-2">
            {top3Assets.map((asset, index) => (
              <div
                key={asset.name}
                className="flex items-center justify-between p-2 rounded-md border hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: asset.color }}
                  />
                  <span className="font-medium">{asset.name}</span>
                  {index === 0 && (
                    <Badge variant="secondary" className="text-xs">Largest</Badge>
                  )}
                </div>
                <div className="text-right">
                  <div className="font-medium">{formatCurrency(asset.value)}</div>
                  <div className="text-xs text-muted-foreground">
                    {formatPercentage(asset.percentage)}
                  </div>
                </div>
              </div>
            ))}
            {chartData.length > 3 && (
              <div className="text-center text-sm text-muted-foreground pt-2">
                +{chartData.length - 3} more asset{chartData.length - 3 !== 1 ? "s" : ""}
              </div>
            )}
          </div>
        </div>

        {/* Allocation Insights */}
        {largestAsset && largestAsset.percentage > 50 && (
          <div className="rounded-md border border-yellow-500/50 bg-yellow-500/10 p-3">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-yellow-500 mt-0.5" />
              <div className="flex-1">
                <div className="font-medium text-sm">High Concentration Warning</div>
                <div className="text-xs text-muted-foreground mt-1">
                  {largestAsset.name} represents {formatPercentage(largestAsset.percentage)} of your portfolio.
                  Consider diversifying to reduce risk.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Rebalancing Suggestions */}
        {chartData.length > 1 && (
          <div className="rounded-md border bg-muted/50 p-3">
            <div className="font-medium text-sm mb-1">Rebalancing Suggestions</div>
            <div className="text-xs text-muted-foreground">
              Your portfolio allocation has shifted. Consider rebalancing to maintain your target
              allocation strategy.
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

