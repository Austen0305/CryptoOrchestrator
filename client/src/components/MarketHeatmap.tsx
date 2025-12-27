/**
 * Market Heatmap Component
 * Displays heatmap visualization of market data (price changes, volumes, correlations)
 */

import React, { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { TrendingUp, TrendingDown, BarChart3, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { useHeatmapData } from "@/hooks/useHeatmap";

interface HeatmapCell {
  symbol: string;
  value: number;
  color: string;
  label: string;
}

interface CorrelationMatrix {
  symbols: string[];
  matrix: Record<string, Record<string, number>>;
}

interface MarketHeatmapProps {
  defaultSymbols?: string[];
  showControls?: boolean;
  height?: number;
}

export function MarketHeatmap({
  defaultSymbols = ["BTC/USD", "ETH/USD", "BNB/USD", "SOL/USD", "ADA/USD", "XRP/USD", "DOT/USD", "MATIC/USD"],
  showControls = true,
  height = 500,
}: MarketHeatmapProps) {
  const { toast } = useToast();
  const [symbols, setSymbols] = useState<string[]>(defaultSymbols);
  const [symbolsInput, setSymbolsInput] = useState<string>(defaultSymbols.join(","));
  const [metric, setMetric] = useState<"change_24h" | "volume_24h" | "correlation">("change_24h");
  // Use React Query hook for heatmap data
  const { data: heatmapResponse, isLoading, error: queryError } = useHeatmapData(
    symbols,
    metric,
    30,
    symbols.length > 0
  );

  const heatmapData = heatmapResponse?.data || null;
  const error = queryError ? (queryError instanceof Error ? queryError.message : "Failed to fetch heatmap data") : null;

  // Parse symbols from input
  const handleSymbolsChange = () => {
    const parsed = symbolsInput
      .split(",")
      .map((s) => s.trim().toUpperCase())
      .filter((s) => s.length > 0);
    
    if (parsed.length > 0) {
      setSymbols(parsed);
    } else {
      toast({
        title: "Invalid Input",
        description: "Please enter at least one trading pair",
        variant: "destructive",
      });
    }
  };

  // Calculate color for cell based on value
  const getCellColor = (value: number, metricType: string): string => {
    if (metricType === "correlation") {
      // Correlation: -1 (red) to +1 (green)
      if (value >= 0.7) return "bg-green-600";
      if (value >= 0.3) return "bg-green-400";
      if (value >= -0.3) return "bg-yellow-400";
      if (value >= -0.7) return "bg-orange-400";
      return "bg-red-600";
    } else if (metricType === "change_24h") {
      // Price change: negative (red) to positive (green)
      if (value >= 5) return "bg-green-600";
      if (value >= 2) return "bg-green-400";
      if (value >= 0) return "bg-green-200";
      if (value >= -2) return "bg-red-200";
      if (value >= -5) return "bg-red-400";
      return "bg-red-600";
    } else {
      // Volume: use gradient from low to high
      const maxVolume = Math.max(
        ...Object.values(heatmapData || {}).map((d) => d.volume_24h || 0)
      );
      if (maxVolume === 0) return "bg-gray-300";
      const ratio = value / maxVolume;
      if (ratio >= 0.8) return "bg-blue-600";
      if (ratio >= 0.6) return "bg-blue-400";
      if (ratio >= 0.4) return "bg-blue-300";
      if (ratio >= 0.2) return "bg-blue-200";
      return "bg-blue-100";
    }
  };

  // Format value for display
  const formatValue = (value: number, metricType: string): string => {
    if (metricType === "correlation") {
      return value.toFixed(2);
    } else if (metricType === "change_24h") {
      return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
    } else {
      // Volume
      if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
      if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
      if (value >= 1e3) return `$${(value / 1e3).toFixed(2)}K`;
      return `$${value.toFixed(2)}`;
    }
  };

  // Prepare heatmap cells
  const heatmapCells = useMemo(() => {
    if (!heatmapData) return [];

    if (metric === "correlation") {
      // Correlation matrix: show all pairs
      const cells: HeatmapCell[] = [];
      for (const symbol1 of symbols) {
        for (const symbol2 of symbols) {
          const value = heatmapData[symbol1]?.[symbol2] ?? 0;
          cells.push({
            symbol: `${symbol1} vs ${symbol2}`,
            value,
            color: getCellColor(value, "correlation"),
            label: formatValue(value, "correlation"),
          });
        }
      }
      return cells;
    } else {
      // Single value per symbol
      return symbols.map((symbol) => {
        const data = heatmapData[symbol] || {};
        const value = metric === "change_24h" ? data.change_24h || 0 : data.volume_24h || 0;
        return {
          symbol,
          value,
          color: getCellColor(value, metric),
          label: formatValue(value, metric),
        };
      });
    }
  }, [heatmapData, symbols, metric]);

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Market Heatmap</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-destructive py-8">{error}</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Market Heatmap
            </CardTitle>
            <CardDescription>
              Visualize market data across multiple trading pairs
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {showControls && (
          <div className="flex flex-wrap items-center gap-4 p-4 border rounded-lg">
            <div className="flex-1 min-w-[200px]">
              <Label>Trading Pairs (comma-separated)</Label>
              <div className="flex gap-2">
                <Input
                  value={symbolsInput}
                  onChange={(e) => setSymbolsInput(e.target.value)}
                  placeholder="BTC/USD, ETH/USD, ..."
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      handleSymbolsChange();
                    }
                  }}
                />
                <Button onClick={handleSymbolsChange} size="sm">
                  Update
                </Button>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Label>Metric</Label>
              <Select value={metric} onValueChange={(v: any) => setMetric(v)}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="change_24h">24h Change</SelectItem>
                  <SelectItem value="volume_24h">24h Volume</SelectItem>
                  <SelectItem value="correlation">Correlation</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        )}

        {isLoading ? (
          <LoadingSkeleton height={`${height}px`} />
        ) : (
          <div
            className="border rounded-lg p-4 overflow-auto"
            style={{ minHeight: `${height}px` }}
          >
            {metric === "correlation" ? (
              // Correlation matrix grid
              <div className="space-y-2">
                <div className="grid gap-2" style={{ gridTemplateColumns: `auto repeat(${symbols.length}, 1fr)` }}>
                  {/* Header row */}
                  <div className="font-semibold text-sm p-2 border-b">Pair</div>
                  {symbols.map((symbol) => (
                    <div key={symbol} className="font-semibold text-sm p-2 border-b text-center">
                      {symbol.split("/")[0]}
                    </div>
                  ))}
                  
                  {/* Data rows */}
                  {symbols.map((symbol1) => (
                    <React.Fragment key={symbol1}>
                      <div className="font-medium text-sm p-2 border-r">{symbol1.split("/")[0]}</div>
                      {symbols.map((symbol2) => {
                        const value = heatmapData?.[symbol1]?.[symbol2] ?? 0;
                        const color = getCellColor(value, "correlation");
                        return (
                          <div
                            key={`${symbol1}-${symbol2}`}
                            className={`${color} text-white text-center p-2 rounded cursor-pointer hover:opacity-80 transition-opacity`}
                            title={`${symbol1} vs ${symbol2}: ${value.toFixed(3)}`}
                          >
                            {value.toFixed(2)}
                          </div>
                        );
                      })}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            ) : (
              // Single value heatmap (change or volume)
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {heatmapCells.map((cell) => (
                  <div
                    key={cell.symbol}
                    className={`${cell.color} text-white p-4 rounded-lg text-center cursor-pointer hover:opacity-80 transition-opacity`}
                    title={`${cell.symbol}: ${cell.label}`}
                  >
                    <div className="font-semibold text-sm mb-1">{cell.symbol.split("/")[0]}</div>
                    <div className="text-lg font-bold">{cell.label}</div>
                    {metric === "change_24h" && (
                      <div className="mt-1">
                        {cell.value >= 0 ? (
                          <TrendingUp className="h-4 w-4 mx-auto" />
                        ) : (
                          <TrendingDown className="h-4 w-4 mx-auto" />
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Legend */}
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span className="font-medium">Legend:</span>
          {metric === "correlation" ? (
            <>
              <div className="flex items-center gap-1">
                <div className="w-4 h-4 bg-red-600 rounded" />
                <span>Strong Negative (-1 to -0.7)</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-4 h-4 bg-yellow-400 rounded" />
                <span>Weak (-0.3 to 0.3)</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-4 h-4 bg-green-600 rounded" />
                <span>Strong Positive (0.7 to 1)</span>
              </div>
            </>
          ) : metric === "change_24h" ? (
            <>
              <div className="flex items-center gap-1">
                <div className="w-4 h-4 bg-red-600 rounded" />
                <span>Negative</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-4 h-4 bg-green-600 rounded" />
                <span>Positive</span>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center gap-1">
                <div className="w-4 h-4 bg-blue-100 rounded" />
                <span>Low Volume</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-4 h-4 bg-blue-600 rounded" />
                <span>High Volume</span>
              </div>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
