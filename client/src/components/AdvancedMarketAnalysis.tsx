import React, { useState, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
  Area,
  AreaChart,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Sparkles,
  RefreshCw,
  Download,
  Filter,
  Target,
} from "lucide-react";
import { useAdvancedMarketAnalysis } from "@/hooks/useMarkets";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import { formatCurrency, formatPercentage } from "@/lib/formatters";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";

interface AdvancedMarketAnalysisProps {
  pair: string;
}

export const AdvancedMarketAnalysis = React.memo(function AdvancedMarketAnalysis({ pair }: AdvancedMarketAnalysisProps) {
  const { isAuthenticated } = useAuth();
  const [indicators, setIndicators] = useState<string[]>(["rsi", "macd", "bollinger"]);
  const [period, setPeriod] = useState<number>(14);
  const { data: analysis, isLoading, refetch, error } = useAdvancedMarketAnalysis(pair, indicators);

  // Use real analysis data from API, show loading/error states if not available
  const analysisData = analysis;

  // Generate historical indicator data from real analysis data
  const historicalData = analysisData?.historical_data || [];

  const getSignalColor = (signal: string) => {
    switch (signal.toLowerCase()) {
      case "buy":
        return "text-green-500 bg-green-500/10 border-green-500/50";
      case "sell":
        return "text-red-500 bg-red-500/10 border-red-500/50";
      default:
        return "text-yellow-500 bg-yellow-500/10 border-yellow-500/50";
    }
  };

  if (!isAuthenticated) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Advanced Market Analysis</CardTitle>
          <CardDescription>Please log in to access advanced analysis</CardDescription>
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
              <Sparkles className="h-5 w-5 text-purple-500" />
              Advanced Market Analysis
            </CardTitle>
            <CardDescription>
              Comprehensive technical analysis with multiple indicators for {pair}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isLoading}>
              <RefreshCw className={cn("h-4 w-4 mr-2", isLoading && "animate-spin")} />
              Refresh
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {isLoading ? (
          <LoadingSkeleton count={6} className="h-24 w-full" />
        ) : error ? (
          <ErrorRetry
            title="Failed to load market analysis"
            message={error instanceof Error ? error.message : "Unable to fetch advanced market analysis. Please try again."}
            onRetry={() => refetch()}
            error={error as Error}
          />
        ) : !analysisData ? (
          <EmptyState
            icon={Sparkles}
            title="No analysis available"
            description={`Advanced market analysis for ${pair} is not available at the moment.`}
          />
        ) : (
          <>
            {/* Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className={cn("border-2", getSignalColor(analysisData.recommendation))}>
                <CardContent className="pt-4">
                  <div className="text-sm font-medium mb-1">Recommendation</div>
                  <div className="text-2xl font-bold uppercase">{analysisData.recommendation}</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    Confidence: {formatPercentage(analysisData.confidence)}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm font-medium text-muted-foreground mb-1">Current Price</div>
                  <div className="text-2xl font-bold">{formatCurrency(analysisData.current_price)}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm font-medium text-muted-foreground mb-1">Signal Balance</div>
                  <div className="flex items-center gap-2">
                    <Badge variant="default" className="bg-green-500">
                      Bullish: {analysisData.signals.bullish}
                    </Badge>
                    <Badge variant="destructive">Bearish: {analysisData.signals.bearish}</Badge>
                    <Badge variant="secondary">Neutral: {analysisData.signals.neutral}</Badge>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Summary Text */}
            <div className="rounded-lg border bg-muted/50 p-4">
              <p className="text-sm">{analysisData.summary}</p>
            </div>

            <Tabs defaultValue="indicators" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="indicators">Indicators</TabsTrigger>
                <TabsTrigger value="charts">Charts</TabsTrigger>
                <TabsTrigger value="signals">Signals</TabsTrigger>
                <TabsTrigger value="levels">Levels</TabsTrigger>
              </TabsList>

              <TabsContent value="indicators" className="space-y-4 mt-4">
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Indicator</TableHead>
                        <TableHead>Value</TableHead>
                        <TableHead>Signal</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow>
                        <TableCell className="font-medium">RSI (14)</TableCell>
                        <TableCell>{analysisData.indicators.rsi.toFixed(1)}</TableCell>
                        <TableCell>
                          {analysisData.indicators.rsi > 70 ? (
                            <Badge variant="destructive">Overbought</Badge>
                          ) : analysisData.indicators.rsi < 30 ? (
                            <Badge variant="default" className="bg-green-500">Oversold</Badge>
                          ) : (
                            <Badge variant="secondary">Neutral</Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          {analysisData.indicators.rsi > 70 ? (
                            <TrendingDown className="h-4 w-4 text-red-500" />
                          ) : analysisData.indicators.rsi < 30 ? (
                            <TrendingUp className="h-4 w-4 text-green-500" />
                          ) : (
                            <Activity className="h-4 w-4 text-yellow-500" />
                          )}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell className="font-medium">MACD</TableCell>
                        <TableCell>
                          {analysisData.indicators.macd.macd.toFixed(1)} /{" "}
                          {analysisData.indicators.macd.signal.toFixed(1)}
                        </TableCell>
                        <TableCell>
                          {analysisData.indicators.macd.histogram > 0 ? (
                            <Badge variant="default" className="bg-green-500">Bullish</Badge>
                          ) : (
                            <Badge variant="destructive">Bearish</Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          {analysisData.indicators.macd.histogram > 0 ? (
                            <TrendingUp className="h-4 w-4 text-green-500" />
                          ) : (
                            <TrendingDown className="h-4 w-4 text-red-500" />
                          )}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell className="font-medium">Bollinger Bands</TableCell>
                        <TableCell>
                          Upper: {formatCurrency(analysisData.indicators.bollinger.upper)}
                          <br />
                          Lower: {formatCurrency(analysisData.indicators.bollinger.lower)}
                        </TableCell>
                        <TableCell>
                          {analysisData.current_price > analysisData.indicators.bollinger.upper ? (
                            <Badge variant="destructive">Above Upper</Badge>
                          ) : analysisData.current_price < analysisData.indicators.bollinger.lower ? (
                            <Badge variant="default" className="bg-green-500">Below Lower</Badge>
                          ) : (
                            <Badge variant="secondary">Within Bands</Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          {analysisData.current_price > analysisData.indicators.bollinger.upper ? (
                            <TrendingDown className="h-4 w-4 text-red-500" />
                          ) : analysisData.current_price < analysisData.indicators.bollinger.lower ? (
                            <TrendingUp className="h-4 w-4 text-green-500" />
                          ) : (
                            <Activity className="h-4 w-4 text-yellow-500" />
                          )}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell className="font-medium">SMA (20)</TableCell>
                        <TableCell>{formatCurrency(analysisData.indicators.sma_20)}</TableCell>
                        <TableCell>
                          {analysisData.current_price > analysisData.indicators.sma_20 ? (
                            <Badge variant="default" className="bg-green-500">Above</Badge>
                          ) : (
                            <Badge variant="destructive">Below</Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          {analysisData.current_price > analysisData.indicators.sma_20 ? (
                            <TrendingUp className="h-4 w-4 text-green-500" />
                          ) : (
                            <TrendingDown className="h-4 w-4 text-red-500" />
                          )}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell className="font-medium">SMA (50)</TableCell>
                        <TableCell>{formatCurrency(analysisData.indicators.sma_50)}</TableCell>
                        <TableCell>
                          {analysisData.current_price > analysisData.indicators.sma_50 ? (
                            <Badge variant="default" className="bg-green-500">Above</Badge>
                          ) : (
                            <Badge variant="destructive">Below</Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          {analysisData.current_price > analysisData.indicators.sma_50 ? (
                            <TrendingUp className="h-4 w-4 text-green-500" />
                          ) : (
                            <TrendingDown className="h-4 w-4 text-red-500" />
                          )}
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>
              </TabsContent>

              <TabsContent value="charts" className="space-y-4 mt-4">
                <div className="space-y-4">
                  {/* Price Chart with Indicators */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Price & Bollinger Bands</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <AreaChart data={historicalData}>
                          <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                          <XAxis dataKey="date" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                          <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: "hsl(var(--card))",
                              border: "1px solid hsl(var(--border))",
                              borderRadius: "6px",
                            }}
                          />
                          <Area
                            type="monotone"
                            dataKey="upper_band"
                            stroke="#ef4444"
                            fill="#ef4444"
                            fillOpacity={0.1}
                            name="Upper Band"
                          />
                          <Area
                            type="monotone"
                            dataKey="lower_band"
                            stroke="#22c55e"
                            fill="#22c55e"
                            fillOpacity={0.1}
                            name="Lower Band"
                          />
                          <Line
                            type="monotone"
                            dataKey="price"
                            stroke="#8884d8"
                            strokeWidth={2}
                            name="Price"
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* RSI Chart */}
                  <Card>
                    <CardHeader>
                      <CardTitle>RSI (Relative Strength Index)</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={200}>
                        <LineChart data={historicalData}>
                          <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                          <XAxis dataKey="date" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                          <YAxis domain={[0, 100]} tick={{ fill: "hsl(var(--muted-foreground))" }} />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: "hsl(var(--card))",
                              border: "1px solid hsl(var(--border))",
                              borderRadius: "6px",
                            }}
                          />
                          <Line
                            type="monotone"
                            dataKey="rsi"
                            stroke="#8884d8"
                            strokeWidth={2}
                            name="RSI"
                          />
                          <Line
                            type="monotone"
                            dataKey={() => 70}
                            stroke="#ef4444"
                            strokeDasharray="5 5"
                            strokeWidth={1}
                            name="Overbought (70)"
                          />
                          <Line
                            type="monotone"
                            dataKey={() => 30}
                            stroke="#22c55e"
                            strokeDasharray="5 5"
                            strokeWidth={1}
                            name="Oversold (30)"
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* MACD Chart */}
                  <Card>
                    <CardHeader>
                      <CardTitle>MACD (Moving Average Convergence Divergence)</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={historicalData}>
                          <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                          <XAxis dataKey="date" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                          <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: "hsl(var(--card))",
                              border: "1px solid hsl(var(--border))",
                              borderRadius: "6px",
                            }}
                          />
                          <Bar
                            dataKey="macd"
                            fill="#8884d8"
                            name="MACD"
                            radius={[4, 4, 0, 0]}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              <TabsContent value="signals" className="space-y-4 mt-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card className="border-green-500/50 bg-green-500/10">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-green-500">
                        <TrendingUp className="h-5 w-5" />
                        Bullish Signals
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {[
                          "Price above SMA(20) and SMA(50)",
                          "MACD positive crossover",
                          "RSI in neutral zone (not overbought)",
                          "Price near lower Bollinger Band (support)",
                          "Volume increasing",
                        ].map((signal, idx) => (
                          <div key={idx} className="flex items-center gap-2 text-sm">
                            <Badge variant="default" className="bg-green-500">
                              {idx + 1}
                            </Badge>
                            <span>{signal}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-red-500/50 bg-red-500/10">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-red-500">
                        <TrendingDown className="h-5 w-5" />
                        Bearish Signals
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {[
                          "Price approaching upper Bollinger Band",
                          "RSI approaching overbought zone",
                        ].map((signal, idx) => (
                          <div key={idx} className="flex items-center gap-2 text-sm">
                            <Badge variant="destructive">{idx + 1}</Badge>
                            <span>{signal}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              <TabsContent value="levels" className="space-y-4 mt-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Support Levels</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      {[
                        { level: analysisData.indicators.bollinger.lower, strength: "Strong" },
                        { level: analysisData.indicators.sma_50, strength: "Medium" },
                        { level: analysisData.indicators.sma_20, strength: "Weak" },
                      ].map((support, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-2 rounded-md border bg-green-500/10 border-green-500/50"
                        >
                          <div>
                            <div className="font-medium">{formatCurrency(support.level)}</div>
                            <div className="text-xs text-muted-foreground">{support.strength}</div>
                          </div>
                          <Target className="h-4 w-4 text-green-500" />
                        </div>
                      ))}
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Resistance Levels</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      {[
                        { level: analysisData.indicators.bollinger.upper, strength: "Strong" },
                        { level: analysisData.indicators.bollinger.middle + 500, strength: "Medium" },
                        { level: analysisData.current_price + 1000, strength: "Weak" },
                      ].map((resistance, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-2 rounded-md border bg-red-500/10 border-red-500/50"
                        >
                          <div>
                            <div className="font-medium">{formatCurrency(resistance.level)}</div>
                            <div className="text-xs text-muted-foreground">{resistance.strength}</div>
                          </div>
                          <Target className="h-4 w-4 text-red-500" />
                        </div>
                      ))}
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Key Levels</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <div className="flex items-center justify-between p-2 rounded-md border">
                        <div>
                          <div className="font-medium">Current Price</div>
                          <div className="text-xs text-muted-foreground">Entry/Exit</div>
                        </div>
                        <div className="font-bold text-primary">
                          {formatCurrency(analysisData.current_price)}
                        </div>
                      </div>
                      <div className="flex items-center justify-between p-2 rounded-md border">
                        <div>
                          <div className="font-medium">Bollinger Middle</div>
                          <div className="text-xs text-muted-foreground">Moving Average</div>
                        </div>
                        <div className="font-medium">
                          {formatCurrency(analysisData.indicators.bollinger.middle)}
                        </div>
                      </div>
                      <div className="flex items-center justify-between p-2 rounded-md border">
                        <div>
                          <div className="font-medium">Band Width</div>
                          <div className="text-xs text-muted-foreground">Volatility Measure</div>
                        </div>
                        <div className="font-medium">
                          {formatCurrency(analysisData.indicators.bollinger.width)}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
            </Tabs>
          </>
        )}
      </CardContent>
    </Card>
  );
});

