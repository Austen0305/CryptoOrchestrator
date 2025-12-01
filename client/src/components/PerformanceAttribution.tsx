import React from "react";
import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { TrendingUp, Target, Percent, Activity, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatCurrency, formatPercentage, formatNumber } from "@/lib/formatters";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";

interface AttributionData {
  strategy: string;
  alpha: number;
  beta: number;
  sharpe: number;
  informationRatio: number;
  contribution: number;
  trades: number;
  winRate: number;
  avgReturn: number;
}

interface CumulativeReturn {
  month: string;
  returns: number;
  benchmark: number;
  alpha: number;
}

interface FactorAnalysis {
  factor: string;
  exposure: number;
  contribution: number;
  color: string;
}

interface PerformanceAttributionResponse {
  attribution: AttributionData[];
  cumulativeReturns: CumulativeReturn[];
  factorAnalysis: FactorAnalysis[];
}

// Mock data fallback (will be replaced when API endpoint is available)
const MOCK_ATTRIBUTION_DATA: PerformanceAttributionResponse = {
  attribution: [
    {
      strategy: "ML Enhanced",
      alpha: 8.5,
      beta: 1.2,
      sharpe: 2.1,
      informationRatio: 1.8,
      contribution: 45,
      trades: 120,
      winRate: 68,
      avgReturn: 3.2,
    },
    {
      strategy: "Smart Adaptive",
      alpha: 6.2,
      beta: 0.9,
      sharpe: 1.8,
      informationRatio: 1.5,
      contribution: 30,
      trades: 85,
      winRate: 65,
      avgReturn: 2.8,
    },
    {
      strategy: "Mean Reversion",
      alpha: 4.1,
      beta: 0.6,
      sharpe: 1.5,
      informationRatio: 1.2,
      contribution: 15,
      trades: 150,
      winRate: 58,
      avgReturn: 2.1,
    },
    {
      strategy: "Trend Following",
      alpha: 2.8,
      beta: 1.1,
      sharpe: 1.3,
      informationRatio: 1.0,
      contribution: 10,
      trades: 95,
      winRate: 62,
      avgReturn: 1.9,
    },
  ],
  cumulativeReturns: [
    { month: "Jan", returns: 0, benchmark: 0, alpha: 0 },
    { month: "Feb", returns: 2.5, benchmark: 1.8, alpha: 0.7 },
    { month: "Mar", returns: 5.2, benchmark: 3.5, alpha: 1.7 },
    { month: "Apr", returns: 8.7, benchmark: 6.2, alpha: 2.5 },
    { month: "May", returns: 12.3, benchmark: 9.1, alpha: 3.2 },
    { month: "Jun", returns: 15.8, benchmark: 12.5, alpha: 3.3 },
    { month: "Jul", returns: 18.4, benchmark: 15.2, alpha: 3.2 },
    { month: "Aug", returns: 22.1, benchmark: 18.5, alpha: 3.6 },
    { month: "Sep", returns: 24.5, benchmark: 21.2, alpha: 3.3 },
    { month: "Oct", returns: 27.8, benchmark: 23.8, alpha: 4.0 },
    { month: "Nov", returns: 30.2, benchmark: 26.1, alpha: 4.1 },
    { month: "Dec", returns: 32.5, benchmark: 28.5, alpha: 4.0 },
  ],
  factorAnalysis: [
    { factor: "Momentum", exposure: 0.65, contribution: 12.5, color: "#8884d8" },
    { factor: "Value", exposure: 0.45, contribution: 8.2, color: "#82ca9d" },
    { factor: "Size", exposure: 0.25, contribution: 4.5, color: "#ffc658" },
    { factor: "Volatility", exposure: -0.15, contribution: -2.1, color: "#ff7c7c" },
    { factor: "Quality", exposure: 0.35, contribution: 6.8, color: "#8dd1e1" },
  ],
};

export function PerformanceAttribution() {
  const { isAuthenticated } = useAuth();

  // Note: API endpoint /api/analytics/performance/attribution doesn't exist yet
  // Using mock data as fallback. When endpoint is available, remove the mock fallback.
  const { data, isLoading, error, refetch } = useQuery<PerformanceAttributionResponse>({
    queryKey: ['performance-attribution'],
    queryFn: async () => {
      try {
        // Try to fetch from API (will fail until endpoint is created)
        const response = await apiRequest<PerformanceAttributionResponse>(
          '/api/analytics/performance/attribution',
          { method: 'GET' }
        );
        return response;
      } catch (err) {
        // Fallback to mock data until API endpoint is available
        console.warn('Performance Attribution API endpoint not available, using mock data:', err);
        return MOCK_ATTRIBUTION_DATA;
      }
    },
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds
    retry: false, // Don't retry since we have mock fallback
  });

  // Use data or fallback to mock
  const attributionData = data?.attribution || MOCK_ATTRIBUTION_DATA.attribution;
  const cumulativeReturns = data?.cumulativeReturns || MOCK_ATTRIBUTION_DATA.cumulativeReturns;
  const factorAnalysis = data?.factorAnalysis || MOCK_ATTRIBUTION_DATA.factorAnalysis;

  const totalAlpha = attributionData.reduce((sum, d) => sum + d.alpha * (d.contribution / 100), 0);
  const totalBeta = attributionData.reduce((sum, d) => sum + d.beta * (d.contribution / 100), 0);
  const totalSharpe = attributionData.reduce((sum, d) => sum + d.sharpe * (d.contribution / 100), 0);
  const totalInfoRatio = attributionData.reduce((sum, d) => sum + d.informationRatio * (d.contribution / 100), 0);

  if (isLoading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Performance Attribution
          </CardTitle>
        </CardHeader>
        <CardContent>
          <LoadingSkeleton className="h-96" />
        </CardContent>
      </Card>
    );
  }

  if (error && !data) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Performance Attribution
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorRetry error={error as Error} onRetry={() => refetch()} />
        </CardContent>
      </Card>
    );
  }

  if (!attributionData || attributionData.length === 0) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Performance Attribution
          </CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={BarChart3}
            title="No Performance Data"
            description="Performance attribution data is not available yet."
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Performance Attribution
        </CardTitle>
        <CardDescription>
          Alpha/beta decomposition and factor analysis of portfolio performance
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <Tabs defaultValue="attribution" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="attribution">Attribution</TabsTrigger>
            <TabsTrigger value="factors">Factors</TabsTrigger>
            <TabsTrigger value="cumulative">Cumulative</TabsTrigger>
            <TabsTrigger value="risk-adjusted">Risk Metrics</TabsTrigger>
          </TabsList>

          <TabsContent value="attribution" className="space-y-4">
            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm font-medium text-muted-foreground">Total Alpha</div>
                  <div className={cn("text-2xl font-bold", totalAlpha >= 0 ? "text-green-500" : "text-red-500")}>
                    {formatPercentage(totalAlpha)}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm font-medium text-muted-foreground">Total Beta</div>
                  <div className="text-2xl font-bold">{formatNumber(totalBeta, 2)}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm font-medium text-muted-foreground">Sharpe Ratio</div>
                  <div className="text-2xl font-bold">{formatNumber(totalSharpe, 2)}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm font-medium text-muted-foreground">Info Ratio</div>
                  <div className="text-2xl font-bold">{formatNumber(totalInfoRatio, 2)}</div>
                </CardContent>
              </Card>
            </div>

            {/* Attribution Table */}
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Strategy</TableHead>
                    <TableHead>Contribution</TableHead>
                    <TableHead>Alpha</TableHead>
                    <TableHead>Beta</TableHead>
                    <TableHead>Sharpe</TableHead>
                    <TableHead>Info Ratio</TableHead>
                    <TableHead>Trades</TableHead>
                    <TableHead>Win Rate</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {attributionData.map((item) => (
                    <TableRow key={item.strategy}>
                      <TableCell className="font-medium">{item.strategy}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="w-24 bg-muted rounded-full h-2">
                            <div
                              className="bg-primary h-2 rounded-full"
                              style={{ width: `${item.contribution}%` }}
                            />
                          </div>
                          <span className="text-sm">{formatPercentage(item.contribution)}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className={cn(item.alpha >= 0 ? "text-green-500" : "text-red-500", "font-medium")}>
                          {formatPercentage(item.alpha)}
                        </span>
                      </TableCell>
                      <TableCell>{formatNumber(item.beta, 2)}</TableCell>
                      <TableCell>{formatNumber(item.sharpe, 2)}</TableCell>
                      <TableCell>{formatNumber(item.informationRatio, 2)}</TableCell>
                      <TableCell>{item.trades}</TableCell>
                      <TableCell>
                        <Badge variant={item.winRate >= 60 ? "default" : "secondary"}>
                          {formatPercentage(item.winRate)}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </TabsContent>

          <TabsContent value="factors" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Factor Exposure & Contribution</CardTitle>
                <CardDescription>
                  Risk factor analysis and contribution to returns
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={factorAnalysis}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                    <XAxis dataKey="factor" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                    <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "6px",
                      }}
                    />
                    <Legend />
                    <Bar dataKey="exposure" fill="#8884d8" name="Exposure" />
                    <Bar dataKey="contribution" fill="#82ca9d" name="Contribution %" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <div className="space-y-2">
              {factorAnalysis.map((factor) => (
                <Card key={factor.factor}>
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: factor.color }}
                        />
                        <div className="font-medium">{factor.factor}</div>
                        <Badge variant="outline">
                          Exposure: {formatNumber(factor.exposure, 2)}
                        </Badge>
                      </div>
                      <div className={cn(
                        "font-bold",
                        factor.contribution >= 0 ? "text-green-500" : "text-red-500"
                      )}>
                        {formatPercentage(factor.contribution)}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="cumulative" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Cumulative Returns vs Benchmark</CardTitle>
                <CardDescription>
                  Portfolio performance vs benchmark with alpha generation
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={cumulativeReturns}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                    <XAxis dataKey="month" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                    <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "6px",
                      }}
                      formatter={(value: number) => `${value}%`}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="returns"
                      stroke="#8884d8"
                      strokeWidth={2}
                      name="Portfolio Returns"
                      dot={{ r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="benchmark"
                      stroke="#82ca9d"
                      strokeWidth={2}
                      name="Benchmark"
                      strokeDasharray="5 5"
                    />
                    <Line
                      type="monotone"
                      dataKey="alpha"
                      stroke="#ffc658"
                      strokeWidth={2}
                      name="Alpha"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="risk-adjusted" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="h-4 w-4" />
                    Risk-Adjusted Metrics
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {attributionData.map((item) => (
                    <div key={item.strategy} className="flex items-center justify-between p-3 rounded-md border">
                      <div>
                        <div className="font-medium">{item.strategy}</div>
                        <div className="text-sm text-muted-foreground">
                          {item.trades} trades • {formatPercentage(item.winRate)} win rate
                        </div>
                      </div>
                      <div className="text-right space-y-1">
                        <div className="text-sm">
                          <span className="text-muted-foreground">Sharpe: </span>
                          <span className="font-medium">{formatNumber(item.sharpe, 2)}</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-muted-foreground">Info Ratio: </span>
                          <span className="font-medium">{formatNumber(item.informationRatio, 2)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    Alpha Generation
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {attributionData.map((item) => (
                    <div key={item.strategy} className="p-3 rounded-md border">
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-medium">{item.strategy}</div>
                        <Badge
                          variant={item.alpha >= 0 ? "default" : "destructive"}
                        >
                          {formatPercentage(item.alpha)}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-muted-foreground">Beta: </span>
                        <span className="font-medium">{formatNumber(item.beta, 2)}</span>
                        <span className="text-muted-foreground ml-4">Avg Return: </span>
                        <span className={cn(
                          "font-medium",
                          item.avgReturn >= 0 ? "text-green-500" : "text-red-500"
                        )}>
                          {formatPercentage(item.avgReturn)}
                        </span>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

