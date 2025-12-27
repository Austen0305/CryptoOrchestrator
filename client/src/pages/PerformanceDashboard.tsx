import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from "recharts";
import { TrendingUp, TrendingDown, DollarSign, Activity, Target, Percent } from "lucide-react";

interface PerformanceMetrics {
  daily_pnl: number[];
  cumulative_returns: number[];
  trades: any[];
  metrics: {
    total_profit: number;
    win_rate: number;
    sharpe_ratio: number;
    max_drawdown: number;
    profit_factor: number;
    total_trades: number;
  };
}

export default function PerformanceDashboard() {
  const { data: performance, isLoading } = useQuery<PerformanceMetrics>({
    queryKey: ['performance', 'metrics'],
    queryFn: async () => {
      return await apiRequest<PerformanceMetrics>('/api/performance/metrics', {
        method: 'GET',
      });
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  if (isLoading || !performance) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-4 bg-muted rounded w-24"></div>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-muted rounded w-32 mb-2"></div>
                <div className="h-4 bg-muted rounded w-20"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  const metrics = performance.metrics;

  // Prepare daily P&L chart data
  const dailyPnlData = performance.daily_pnl.map((pnl: number, index: number) => ({
    day: `Day ${index + 1}`,
    pnl: pnl,
  }));

  // Prepare cumulative returns chart data
  const cumulativeData = performance.cumulative_returns.map((ret: number, index: number) => ({
    day: `Day ${index + 1}`,
    returns: ret * 100, // Convert to percentage
  }));

  // Win/Loss distribution
  const winLossData = [
    { name: 'Wins', value: Math.round(metrics.win_rate * metrics.total_trades / 100), color: 'hsl(var(--chart-1))' },
    { name: 'Losses', value: Math.round((100 - metrics.win_rate) * metrics.total_trades / 100), color: 'hsl(var(--chart-2))' },
  ];

  // Prepare recent trades data
  const recentTrades = performance.trades.slice(-20).map((trade: any) => ({
    symbol: trade.symbol,
    pnl: trade.pnl,
    date: new Date(trade.timestamp).toLocaleDateString(),
  }));

  return (
    <div className="space-y-6 w-full">
      <div>
        <h1 className="text-3xl font-bold" data-testid="performance-dashboard">Performance Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Real-time trading performance metrics and analytics
        </p>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Profit</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${metrics.total_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${metrics.total_profit.toFixed(2)}
            </div>
            <div className="flex items-center text-xs text-muted-foreground mt-1">
              {metrics.total_profit >= 0 ? (
                <TrendingUp className="h-3 w-3 mr-1 text-green-600" />
              ) : (
                <TrendingDown className="h-3 w-3 mr-1 text-red-600" />
              )}
              <span>Last 30 days</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.win_rate.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground mt-1">
              {Math.round(metrics.win_rate * metrics.total_trades / 100)} wins of {metrics.total_trades}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sharpe Ratio</CardTitle>
            <Percent className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.sharpe_ratio.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Risk-adjusted returns
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Max Drawdown</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {(metrics.max_drawdown * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Worst peak-to-trough decline
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily P&L Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Daily P&L</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={dailyPnlData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                <XAxis
                  dataKey="day"
                  tick={{ fill: "hsl(var(--muted-foreground))" }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "hsl(var(--muted-foreground))" }}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--background))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "6px",
                  }}
                />
                <Bar
                  dataKey="pnl"
                  fill="hsl(var(--chart-1))"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Cumulative Returns Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Cumulative Returns</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={cumulativeData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                <XAxis
                  dataKey="day"
                  tick={{ fill: "hsl(var(--muted-foreground))" }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "hsl(var(--muted-foreground))" }}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--background))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "6px",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="returns"
                  stroke="hsl(var(--chart-1))"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Win/Loss Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Win/Loss Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={winLossData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({name, value}) => `${name}: ${value}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {winLossData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Recent Trades Table */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Trades</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {recentTrades.map((trade: any, index: number) => (
                <div
                  key={index}
                  className="flex justify-between items-center p-2 rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <div className="text-sm font-medium">{trade.symbol}</div>
                    <div className="text-xs text-muted-foreground">{trade.date}</div>
                  </div>
                  <div className={`text-sm font-bold ${trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Additional Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Advanced Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-muted-foreground">Profit Factor</div>
              <div className="text-2xl font-bold mt-1">{metrics.profit_factor.toFixed(2)}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Gross profit / Gross loss
              </p>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Total Trades</div>
              <div className="text-2xl font-bold mt-1">{metrics.total_trades}</div>
              <p className="text-xs text-muted-foreground mt-1">
                All closed positions
              </p>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Avg Trade</div>
              <div className="text-2xl font-bold mt-1">
                ${(metrics.total_profit / metrics.total_trades).toFixed(2)}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Per trade average
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
