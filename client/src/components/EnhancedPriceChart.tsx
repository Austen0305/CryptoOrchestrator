import { useEffect, useRef, useState, useCallback } from "react";
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time, ColorType, UTCTimestamp } from "lightweight-charts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Maximize2, Radio } from "lucide-react";
import { useWebSocket } from "@/hooks/useWebSocket";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";
import { LineChart } from "lucide-react";
import React from "react";

interface EnhancedPriceChartProps {
  pair: string;
  currentPrice: number;
  change24h: number;
  data?: Array<{ time: string; price: number; volume?: number }>;
  live?: boolean;
  isLoading?: boolean;
  error?: Error | null;
}

export const EnhancedPriceChart = React.memo(function EnhancedPriceChart({
  pair,
  currentPrice,
  change24h,
  data = [],
  live = true,
  isLoading = false,
  error = null,
}: EnhancedPriceChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const areaSeriesRef = useRef<ISeriesApi<"Area"> | null>(null);
  const [chartType, setChartType] = useState<"candlestick" | "area">("candlestick");
  const [timeframe, setTimeframe] = useState<string>("1D");
  const { subscribeSymbols, unsubscribeSymbols, getLatestMarketData, getCandles, isConnected } = useWebSocket();
  const priceRef = useRef(currentPrice);
  const lastUpdateRef = useRef<number>(0);

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "hsl(var(--foreground))",
      },
      grid: {
        vertLines: { color: "hsl(var(--border) / 0.3)" },
        horzLines: { color: "hsl(var(--border) / 0.3)" },
      },
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: "hsl(var(--border))",
      },
    });

    chartRef.current = chart;

    // Create candlestick series
    // @ts-ignore - lightweight-charts types may be outdated
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });
    candlestickSeriesRef.current = candlestickSeries;

    // Create area series
    // @ts-ignore - lightweight-charts types may be outdated
    const areaSeries = chart.addAreaSeries({
      lineColor: "hsl(var(--primary))",
      topColor: "hsl(var(--primary) / 0.3)",
      bottomColor: "hsl(var(--primary) / 0.05)",
      lineWidth: 2,
    });
    areaSeriesRef.current = areaSeries;

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chart) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      chartRef.current = null;
    };
  }, []);

  // Subscribe to WebSocket updates
  useEffect(() => {
    if (!live) return;
    subscribeSymbols([pair]);
    return () => unsubscribeSymbols([pair]);
  }, [pair, live, subscribeSymbols, unsubscribeSymbols]);

  // Update chart with real-time data
  useEffect(() => {
    if (!live || !chartRef.current || !candlestickSeriesRef.current || !areaSeriesRef.current) return;

    const interval = setInterval(() => {
      const latest = getLatestMarketData();
      const tick = latest[pair];
      if (tick && typeof tick.price === "number") {
        const price = tick.price;
        priceRef.current = price;
        const now = Date.now();
        const time = Math.floor(now / 1000) as UTCTimestamp;

        // Update area series
        if (areaSeriesRef.current) {
          areaSeriesRef.current.update({ time, value: price });
        }

        // Update candlestick if we have OHLC data
        const candles = getCandles(pair);
        if (candles && candles.length > 0) {
          const latestCandle = candles[candles.length - 1];
          if (latestCandle && latestCandle.length >= 5) {
            const candleData: CandlestickData = {
              time: (latestCandle[0] / 1000) as Time,
              open: latestCandle[1],
              high: latestCandle[2],
              low: latestCandle[3],
              close: latestCandle[4],
            };
            if (candlestickSeriesRef.current) {
              candlestickSeriesRef.current.update(candleData);
            }
          }
        }
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [pair, live, getLatestMarketData, getCandles]);

  // Load initial data
  useEffect(() => {
    if (!chartRef.current || !candlestickSeriesRef.current || !areaSeriesRef.current) return;

    const candles = getCandles(pair);
    if (candles && candles.length > 0) {
            const candleData: CandlestickData[] = candles.map((c) => ({
        time: (c[0] / 1000) as UTCTimestamp,
        open: c[1],
        high: c[2],
        low: c[3],
        close: c[4],
      }));

      if (chartType === "candlestick" && candlestickSeriesRef.current) {
        candlestickSeriesRef.current.setData(candleData);
      } else if (chartType === "area" && areaSeriesRef.current) {
        const areaData = candleData.map((c) => ({ time: c.time, value: c.close }));
        areaSeriesRef.current.setData(areaData);
      }
    } else if (data && data.length > 0) {
      // Fallback to provided data
      const areaData = data.map((d) => ({
        time: Math.floor(new Date(d.time).getTime() / 1000) as UTCTimestamp,
        value: d.price,
      }));

      if (areaSeriesRef.current) {
        areaSeriesRef.current.setData(areaData);
      }
    }
  }, [pair, data, getCandles, chartType]);

  // Toggle chart type visibility
  useEffect(() => {
    if (!candlestickSeriesRef.current || !areaSeriesRef.current) return;

    if (chartType === "candlestick") {
      // Use applyOptions to show/hide series
      candlestickSeriesRef.current?.applyOptions({ visible: true });
      areaSeriesRef.current?.applyOptions({ visible: false });
    } else {
      candlestickSeriesRef.current?.applyOptions({ visible: false });
      areaSeriesRef.current?.applyOptions({ visible: true });
    }
  }, [chartType]);

  const handleRetry = () => {
    window.dispatchEvent(new CustomEvent("pricechart:retry", { detail: { pair } }));
  };

  const isPositive = change24h >= 0;
  const timeframes = ["1H", "4H", "1D", "1W", "1M"];

  if (isLoading) {
    return (
      <Card className="h-full flex flex-col border-2 border-card-border/70 shadow-2xl">
        <CardHeader className="flex-row items-center justify-between space-y-0 pb-5 px-6 pt-6">
          <CardTitle className="text-xl md:text-2xl font-extrabold">{pair}</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 pb-6 px-6">
          <LoadingSkeleton className="h-full w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="h-full flex flex-col border-2 border-card-border/70 shadow-2xl">
        <CardHeader className="flex-row items-center justify-between space-y-0 pb-5 px-6 pt-6">
          <CardTitle className="text-xl md:text-2xl font-extrabold">{pair}</CardTitle>
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

  return (
    <Card className="h-full flex flex-col border-2 border-card-border/70 shadow-2xl">
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-5 px-6 pt-6 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border-b-2 border-primary/20">
        <div className="flex flex-col space-y-1">
          <CardTitle className="text-xl md:text-2xl font-extrabold text-foreground drop-shadow-sm">{pair}</CardTitle>
          <div className="flex items-center space-x-2">
            <span className="text-2xl font-bold">${priceRef.current.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
            <Badge variant={isPositive ? "default" : "destructive"} className="text-xs">
              {isPositive ? <TrendingUp className="h-3 w-3 mr-1" /> : <TrendingDown className="h-3 w-3 mr-1" />}
              {Math.abs(change24h).toFixed(2)}%
            </Badge>
            {isConnected && (
              <Badge variant="outline" className="text-xs">
                <Radio className="h-3 w-3 mr-1" />
                Live
              </Badge>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <div className="flex rounded-lg border border-border bg-background p-1">
            {timeframes.map((tf) => (
              <Button
                key={tf}
                variant={timeframe === tf ? "default" : "ghost"}
                size="sm"
                className="h-7 px-2 text-xs"
                onClick={() => setTimeframe(tf)}
              >
                {tf}
              </Button>
            ))}
          </div>
          <div className="flex rounded-lg border border-border bg-background p-1">
            <Button
              variant={chartType === "candlestick" ? "default" : "ghost"}
              size="sm"
              className="h-7 px-2 text-xs"
              onClick={() => setChartType("candlestick")}
            >
              Candles
            </Button>
            <Button
              variant={chartType === "area" ? "default" : "ghost"}
              size="sm"
              className="h-7 px-2 text-xs"
              onClick={() => setChartType("area")}
            >
              Area
            </Button>
          </div>
          <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex-1 pb-6 px-6">
        <div ref={chartContainerRef} className="w-full h-full min-h-[400px]" />
      </CardContent>
    </Card>
  );
});
