import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Maximize2, Radio, AlertCircle } from "lucide-react";
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts";
import { useEffect, useRef, useState, useMemo } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";
import React from "react";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";
import { LineChart } from "lucide-react";

interface PriceChartProps {
  pair: string;
  currentPrice: number;
  change24h: number;
  data: Array<{ time: string; price: number; volume?: number }>;
  live?: boolean;
  isLoading?: boolean;
  error?: Error | null;
}

export const PriceChart = React.memo(function PriceChart({ 
  pair, 
  currentPrice, 
  change24h, 
  data, 
  live = true,
  isLoading = false,
  error = null
}: PriceChartProps) {
  const isPositive = change24h >= 0;
  const timeframes = ["1H", "4H", "1D", "1W", "1M"];
  const { subscribeSymbols, unsubscribeSymbols, getLatestMarketData, getCandles, isConnected } = useWebSocket();
  const [liveData, setLiveData] = useState(data);
  const [recentlyBackfilled, setRecentlyBackfilled] = useState(false);
  const priceRef = useRef(currentPrice);
  const lastCandleLenRef = useRef<number>(0);
  const [retryCount, setRetryCount] = useState(0);

  // Subscribe/unsubscribe
  useEffect(() => {
    if (!live) return;
    subscribeSymbols([pair]);
    return () => unsubscribeSymbols([pair]);
  }, [pair, live, subscribeSymbols, unsubscribeSymbols]);

  // Apply incoming ticks to the chart series
  useEffect(() => {
    if (!live) return;
    const interval = setInterval(() => {
      const latest = getLatestMarketData();
      const tick = latest[pair];
      if (tick && typeof tick.price === 'number') {
        const price = tick.price as number; // ensure number type
        priceRef.current = price;
        setLiveData(prev => {
          const next = [...prev, { time: new Date().toLocaleTimeString(), price }];
          return next.slice(-300);
        });
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [pair, live, getLatestMarketData]);

  // Check for backfilled candles and rebuild base series when available
  useEffect(() => {
    if (!live) return;
    const interval = setInterval(() => {
      const candles = getCandles(pair);
      if (candles && candles.length && candles.length !== lastCandleLenRef.current) {
        lastCandleLenRef.current = candles.length;
        const series = candles.map(c => ({ time: new Date(c[0]).toLocaleTimeString(), price: c[4] }));
        setLiveData(series.slice(-300));
        setRecentlyBackfilled(true);
        setTimeout(() => setRecentlyBackfilled(false), 5000);
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [pair, live, getCandles]);

  const handleRetry = () => {
    setRetryCount(prev => prev + 1);
    // Trigger a re-render to retry data fetching
    window.dispatchEvent(new CustomEvent('pricechart:retry', { detail: { pair, retryCount: retryCount + 1 } }));
  };

  const chartData = live ? liveData : data;
  const hasData = chartData && chartData.length > 0;

  if (isLoading) {
    return (
      <Card 
        className="h-full flex flex-col border-2 border-card-border/70 shadow-2xl bg-gradient-to-br from-card via-card/98 to-card/95" 
        style={{ borderWidth: '3px', borderStyle: 'solid', boxShadow: '0px 20px 40px -10px hsl(220 8% 2% / 0.60), 0px 10px 20px -10px hsl(220 8% 2% / 0.60)' }}
        role="region"
        aria-label={`Price chart for ${pair}`}
      >
        <CardHeader className="flex-row items-center justify-between space-y-0 pb-5 px-6 pt-6 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border-b-2 border-primary/20">
          <div className="space-y-2">
            <CardTitle className="text-xl md:text-2xl font-extrabold text-foreground drop-shadow-sm">{pair}</CardTitle>
            <div className="flex items-baseline gap-3 flex-wrap">
              <LoadingSkeleton className="h-8 w-32" />
              <LoadingSkeleton className="h-6 w-20" />
            </div>
          </div>
        </CardHeader>
        <CardContent className="flex-1 pb-6 px-6">
          <LoadingSkeleton className="h-full w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card 
        className="h-full flex flex-col border-2 border-card-border/70 shadow-2xl bg-gradient-to-br from-card via-card/98 to-card/95" 
        style={{ borderWidth: '3px', borderStyle: 'solid', boxShadow: '0px 20px 40px -10px hsl(220 8% 2% / 0.60), 0px 10px 20px -10px hsl(220 8% 2% / 0.60)' }}
        role="region"
        aria-label={`Price chart for ${pair}`}
      >
        <CardHeader className="flex-row items-center justify-between space-y-0 pb-5 px-6 pt-6 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border-b-2 border-primary/20">
          <CardTitle className="text-xl md:text-2xl font-extrabold text-foreground drop-shadow-sm">{pair}</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 pb-6 px-6">
          <ErrorRetry
            title="Failed to load price chart"
            message={error.message || "Unable to fetch price data. Please try again."}
            onRetry={handleRetry}
            error={error}
          />
        </CardContent>
      </Card>
    );
  }

  if (!hasData) {
    return (
      <Card 
        className="h-full flex flex-col border-2 border-card-border/70 shadow-2xl bg-gradient-to-br from-card via-card/98 to-card/95" 
        style={{ borderWidth: '3px', borderStyle: 'solid', boxShadow: '0px 20px 40px -10px hsl(220 8% 2% / 0.60), 0px 10px 20px -10px hsl(220 8% 2% / 0.60)' }}
        role="region"
        aria-label={`Price chart for ${pair}`}
      >
        <CardHeader className="flex-row items-center justify-between space-y-0 pb-5 px-6 pt-6 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border-b-2 border-primary/20">
          <CardTitle className="text-xl md:text-2xl font-extrabold text-foreground drop-shadow-sm">{pair}</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 pb-6 px-6">
          <EmptyState
            icon={LineChart}
            title="No price data available"
            description="Price data for this trading pair is not available at the moment."
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card 
      className="h-full flex flex-col border-2 border-card-border/70 shadow-2xl bg-gradient-to-br from-card via-card/98 to-card/95" 
      style={{ borderWidth: '3px', borderStyle: 'solid', boxShadow: '0px 20px 40px -10px hsl(220 8% 2% / 0.60), 0px 10px 20px -10px hsl(220 8% 2% / 0.60)' }}
      role="region"
      aria-label={`Price chart for ${pair}`}
    >
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-5 px-6 pt-6 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border-b-2 border-primary/20">
        <div className="space-y-2">
          <CardTitle className="text-xl md:text-2xl font-extrabold text-foreground drop-shadow-sm">{pair}</CardTitle>
          <div className="flex items-baseline gap-3 flex-wrap">
            <span 
              className="text-2xl md:text-3xl font-mono font-bold text-foreground" 
              data-testid="text-current-price"
              aria-label={`Current price: $${(live && priceRef.current ? priceRef.current : currentPrice).toLocaleString()}`}
            >
              ${ (live && priceRef.current ? priceRef.current : currentPrice).toLocaleString() }
            </span>
            <Badge
              variant={isPositive ? "default" : "destructive"}
              className="badge-enhanced font-mono font-semibold"
              data-testid="text-price-change"
              aria-label={`24 hour change: ${isPositive ? "+" : ""}${change24h.toFixed(2)}%`}
            >
              {isPositive ? <TrendingUp className="w-3 h-3 mr-1" aria-hidden="true" /> : <TrendingDown className="w-3 h-3 mr-1" aria-hidden="true" />}
              {isPositive ? "+" : ""}{change24h.toFixed(2)}%
            </Badge>
            <span className="inline-flex items-center text-xs text-muted-foreground gap-1.5 font-medium">
              <Radio className={`h-3 w-3 ${isConnected ? 'text-green-500 animate-pulse' : 'text-yellow-500'}`} />
              {isConnected ? 'Live' : 'Reconnecting…'}
            </span>
            {recentlyBackfilled && (
              <Badge variant="secondary" className="ml-2 badge-enhanced">Backfilled</Badge>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          {timeframes.map((tf) => (
            <Button
              key={tf}
              variant={tf === "1D" ? "secondary" : "ghost"}
              size="sm"
              data-testid={`button-timeframe-${tf}`}
              className="rounded-md font-medium"
            >
              {tf}
            </Button>
          ))}
          <Button 
            variant="ghost" 
            size="icon" 
            data-testid="button-fullscreen" 
            aria-label="Fullscreen"
            className="rounded-md hover:bg-accent/50"
          >
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex-1 pb-6 px-6">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor={isPositive ? "hsl(142 76% 36%)" : "hsl(0 84% 40%)"}
                  stopOpacity={0.3}
                />
                <stop
                  offset="95%"
                  stopColor={isPositive ? "hsl(142 76% 36%)" : "hsl(0 84% 40%)"}
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.2} />
            <XAxis
              dataKey="time"
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11, fontWeight: 500 }}
              tickLine={false}
              axisLine={{ stroke: "hsl(var(--border))", strokeWidth: 1 }}
            />
            <YAxis
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11, fontWeight: 500 }}
              tickLine={false}
              axisLine={{ stroke: "hsl(var(--border))", strokeWidth: 1 }}
              tickFormatter={(value) => `$${value.toLocaleString()}`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
                boxShadow: "var(--shadow-lg)",
                padding: "8px 12px",
              }}
              labelStyle={{ color: "hsl(var(--foreground))", fontWeight: 600, marginBottom: "4px" }}
              cursor={{ stroke: "hsl(var(--primary))", strokeWidth: 1, strokeDasharray: "4 4" }}
            />
            <Area
              type="monotone"
              dataKey="price"
              stroke={isPositive ? "hsl(142 76% 46%)" : "hsl(0 84% 50%)"}
              strokeWidth={2.5}
              fill="url(#priceGradient)"
              dot={false}
              activeDot={{ r: 4, fill: isPositive ? "hsl(142 76% 46%)" : "hsl(0 84% 50%)", strokeWidth: 2, stroke: "hsl(var(--card))" }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
});
