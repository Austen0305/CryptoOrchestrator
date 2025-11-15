import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Maximize2, Radio } from "lucide-react";
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts";
import { useEffect, useRef, useState } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";

interface PriceChartProps {
  pair: string;
  currentPrice: number;
  change24h: number;
  data: Array<{ time: string; price: number; volume?: number }>;
  live?: boolean;
}

export function PriceChart({ pair, currentPrice, change24h, data, live = true }: PriceChartProps) {
  const isPositive = change24h >= 0;
  const timeframes = ["1H", "4H", "1D", "1W", "1M"];
  const { subscribeSymbols, unsubscribeSymbols, getLatestMarketData, getCandles, isConnected } = useWebSocket();
  const [liveData, setLiveData] = useState(data);
  const [recentlyBackfilled, setRecentlyBackfilled] = useState(false);
  const priceRef = useRef(currentPrice);
  const lastCandleLenRef = useRef<number>(0);

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

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-4">
        <div className="space-y-1">
          <CardTitle className="text-2xl font-semibold">{pair}</CardTitle>
          <div className="flex items-baseline gap-3">
            <span className="text-3xl font-mono font-bold" data-testid="text-current-price">
              ${ (live && priceRef.current ? priceRef.current : currentPrice).toLocaleString() }
            </span>
            <Badge
              variant={isPositive ? "default" : "destructive"}
              className="font-mono"
              data-testid="text-price-change"
            >
              {isPositive ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
              {isPositive ? "+" : ""}{change24h.toFixed(2)}%
            </Badge>
            <span className="inline-flex items-center text-xs text-muted-foreground gap-1">
              <Radio className={`h-3 w-3 ${isConnected ? 'text-green-500' : 'text-yellow-500'}`} />
              {isConnected ? 'Live' : 'Reconnecting…'}
            </span>
            {recentlyBackfilled && (
              <Badge variant="secondary" className="ml-2">Backfilled</Badge>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {timeframes.map((tf) => (
            <Button
              key={tf}
              variant={tf === "1D" ? "secondary" : "ghost"}
              size="sm"
              data-testid={`button-timeframe-${tf}`}
            >
              {tf}
            </Button>
          ))}
          <Button variant="ghost" size="icon" data-testid="button-fullscreen" aria-label="Fullscreen">
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex-1 pb-4">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={live ? liveData : data}>
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
            <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
            <XAxis
              dataKey="time"
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
              tickLine={false}
              tickFormatter={(value) => `$${value.toLocaleString()}`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "6px",
              }}
              labelStyle={{ color: "hsl(var(--foreground))" }}
            />
            <Area
              type="monotone"
              dataKey="price"
              stroke={isPositive ? "hsl(var(--chart-up))" : "hsl(var(--chart-down))"}
              strokeWidth={2}
              fill="url(#priceGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
