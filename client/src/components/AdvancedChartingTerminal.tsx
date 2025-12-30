import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  createChart,
  IChartApi,
  ISeriesApi,
  CandlestickData,
  Time,
  ColorType,
  UTCTimestamp,
  LineStyleOptions,
  LineData,
} from "lightweight-charts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  TrendingUp,
  Settings,
  Layers,
  AlertCircle,
  Save,
  Download,
  Maximize2,
  Minimize2,
  X,
  Plus,
  LineChart,
} from "lucide-react";
import { useMarketplaceIndicators, useExecuteIndicator } from "@/hooks/useIndicators";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useToast } from "@/hooks/use-toast";
import { usePreferences } from "@/hooks/usePreferences";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { useAuth } from "@/hooks/useAuth";
import { MarketHeatmap } from "@/components/MarketHeatmap";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface IndicatorOverlay {
  id: string;
  indicatorId: number;
  name: string;
  color: string;
  visible: boolean;
  parameters: Record<string, any>;
}

interface DrawingTool {
  type: "trendline" | "horizontal" | "vertical" | "fibonacci";
  points: Array<{ time: Time; price: number }>;
  color: string;
  visible: boolean;
}

interface ChartLayout {
  id: string;
  name: string;
  charts: number; // 1, 2, 4 charts
}

export function AdvancedChartingTerminal() {
  const { toast } = useToast();
  const { subscribeSymbols, getCandles, isConnected, getLatestMarketData } = useWebSocket();
  const { user } = useAuth();
  const { preferences, updatePreferences } = usePreferences();
  const executeIndicator = useExecuteIndicator();

  const [selectedPair, setSelectedPair] = useState("BTC/USD");
  const [timeframe, setTimeframe] = useState("1D");
  const [layout, setLayout] = useState<ChartLayout>({ id: "1", name: "Single", charts: 1 });
  const [indicators, setIndicators] = useState<IndicatorOverlay[]>([]);
  const [drawings, setDrawings] = useState<DrawingTool[]>([]);
  const [alerts, setAlerts] = useState<Array<{ id: string; pair: string; condition: "above" | "below"; price: number; active: boolean }>>([]);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [indicatorDialogOpen, setIndicatorDialogOpen] = useState(false);
  const [alertDialogOpen, setAlertDialogOpen] = useState(false);
  const [isExecutingIndicators, setIsExecutingIndicators] = useState(false);

  const chartContainerRefs = useRef<Array<HTMLDivElement | null>>([]);
  const chartRefs = useRef<Array<IChartApi | null>>([]);
  const candlestickSeriesRefs = useRef<Array<ISeriesApi<"Candlestick"> | null>>([]);
  const indicatorSeriesRefs = useRef<Map<string, ISeriesApi<"Line">>>(new Map());

  const { data: marketplaceIndicators } = useMarketplaceIndicators({
    limit: 100,
    is_free: true, // Show free indicators for overlay
  });

  // Initialize charts
  useEffect(() => {
    const chartCount = layout.charts;
    chartContainerRefs.current = [];
    chartRefs.current = [];
    candlestickSeriesRefs.current = [];

    for (let i = 0; i < chartCount; i++) {
      const containerId = `chart-container-${i}`;
      const container = document.getElementById(containerId) as HTMLDivElement;
      if (!container) continue;

      chartContainerRefs.current[i] = container;

      const chart = createChart(container, {
        layout: {
          background: { type: ColorType.Solid, color: "transparent" },
          textColor: "hsl(var(--foreground))",
        },
        grid: {
          vertLines: { color: "hsl(var(--border) / 0.3)" },
          horzLines: { color: "hsl(var(--border) / 0.3)" },
        },
        width: container.clientWidth,
        height: container.clientHeight,
        timeScale: {
          timeVisible: true,
          secondsVisible: false,
        },
        rightPriceScale: {
          borderColor: "hsl(var(--border))",
        },
      });

      chartRefs.current[i] = chart;

      // Create candlestick series
      // Verify chart was created successfully
      if (!chart || typeof chart.addCandlestickSeries !== 'function') {
        console.error('Chart initialization failed: addCandlestickSeries not available');
        throw new Error('Chart library not properly loaded');
      }

      // @ts-ignore - lightweight-charts types may be outdated
      const candlestickSeries = chart.addCandlestickSeries({
        upColor: "#22c55e",
        downColor: "#ef4444",
        borderVisible: false,
        wickUpColor: "#22c55e",
        wickDownColor: "#ef4444",
      });
      candlestickSeriesRefs.current[i] = candlestickSeries;

      // Handle resize
      const handleResize = () => {
        if (container && chart) {
          chart.applyOptions({
            width: container.clientWidth,
            height: container.clientHeight,
          });
        }
      };

      window.addEventListener("resize", handleResize);
    }

    return () => {
      chartRefs.current.forEach((chart) => {
        if (chart) chart.remove();
      });
      chartRefs.current = [];
      candlestickSeriesRefs.current = [];
    };
  }, [layout]);

  // Define updateIndicatorOverlays before using it
  const updateIndicatorOverlays = useCallback(async (candleData: CandlestickData[]) => {
    if (!user || indicators.length === 0 || isExecutingIndicators) return;

    setIsExecutingIndicators(true);

    // Convert candle data to market data format for API
    const marketData = candleData.map((c) => ({
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
      volume: 0, // Volume not available in lightweight-charts by default
      timestamp: new Date((c.time as number) * 1000).toISOString(),
    }));

    // Execute each indicator
    for (const indicator of indicators) {
      if (!indicator.visible) continue;

      try {
        const result = await executeIndicator.mutateAsync({
          indicatorId: indicator.indicatorId,
          market_data: marketData,
          parameters: indicator.parameters,
        }) as { values?: unknown[] };

        if (result.values && Array.isArray(result.values) && result.values.length > 0) {
          const indicatorId = `indicator-${indicator.id}`;
          let series = indicatorSeriesRefs.current.get(indicatorId);

          if (!series && chartRefs.current[0]) {
            // @ts-ignore - lightweight-charts types may be outdated
            series = chartRefs.current[0].addLineSeries({
              color: indicator.color,
              lineWidth: 2,
              title: indicator.name,
            });
            if (series) {
              indicatorSeriesRefs.current.set(indicatorId, series);
            }
          }

          if (series && result.values.length === candleData.length) {
            // Map indicator values to line data
            const lineData: LineData[] = candleData
              .map((c, i) => {
                const val = Array.isArray(result.values![i]) ? (result.values![i] as number[])[0] : (result.values![i] as number);
                return val !== undefined && val !== null ? { time: c.time, value: val } : null;
              })
              .filter((item): item is LineData => item !== null);
            if (lineData.length > 0) {
              series.setData(lineData);
            }
          } else if (series && result.values.length > 0) {
            // Single value indicator (like RSI) - create constant line or use last value
            const value = Array.isArray(result.values[0]) ? (result.values[0] as number[])[0] : (result.values[0] as number);
            if (value !== undefined && value !== null) {
              const lineData: LineData[] = candleData.map((c) => ({
                time: c.time,
                value: value,
              }));
              series.setData(lineData);
            }
          }
        }
      } catch (error) {
        console.error(`Error executing indicator ${indicator.name}:`, error);
        toast({
          title: "Indicator Error",
          description: `Failed to execute ${indicator.name}`,
          variant: "destructive",
        });
      }
    }

    setIsExecutingIndicators(false);
  }, [indicators, user, executeIndicator, toast, isExecutingIndicators]);

  // Load and update chart data
  useEffect(() => {
    if (!chartRefs.current[0] || !candlestickSeriesRefs.current[0]) return;

    const candles = getCandles(selectedPair);
    if (candles && candles.length > 0) {
      const candleData: CandlestickData[] = candles.map((c) => ({
        time: (c[0] / 1000) as UTCTimestamp,
        open: c[1],
        high: c[2],
        low: c[3],
        close: c[4],
      }));

      // Update all charts with same data
      candlestickSeriesRefs.current.forEach((series) => {
        if (series) series.setData(candleData);
      });

      // Update indicator overlays
      updateIndicatorOverlays(candleData);
    }
  }, [selectedPair, timeframe, indicators, updateIndicatorOverlays, getCandles]);

  // Monitor alerts
  useEffect(() => {
    if (alerts.filter((a) => a.active).length === 0) return;

    const interval = setInterval(() => {
      const latest = getLatestMarketData();
      const tick = latest[selectedPair];
      if (tick && typeof tick.price === "number") {
        const currentPrice = tick.price;

        alerts.forEach((alert) => {
          if (!alert.active || alert.pair !== selectedPair) return;

          const triggered =
            (alert.condition === "above" && currentPrice >= alert.price) ||
            (alert.condition === "below" && currentPrice <= alert.price);

          if (triggered) {
            toast({
              title: "Price Alert Triggered!",
              description: `${alert.pair} ${alert.condition === "above" ? "reached" : "dropped to"} $${alert.price}`,
            });
            setAlerts(alerts.map((a) => (a.id === alert.id ? { ...a, active: false } : a)));
          }
        });
      }
    }, 1000); // Check every second

    return () => clearInterval(interval);
  }, [alerts, selectedPair, getLatestMarketData, toast]);

  const handleAddIndicator = (indicatorId: number) => {
    const indicator = marketplaceIndicators?.indicators.find((ind) => ind.id === indicatorId);
    if (!indicator) return;

    const overlay: IndicatorOverlay = {
      id: `overlay-${Date.now()}`,
      indicatorId: indicator.id,
      name: indicator.name,
      color: `hsl(${Math.random() * 360}, 70%, 50%)`,
      visible: true,
      parameters: {},
    };

    setIndicators([...indicators, overlay]);
    setIndicatorDialogOpen(false);
    toast({
      title: "Indicator Added",
      description: `${indicator.name} added to chart`,
    });
  };

  const handleRemoveIndicator = (id: string) => {
    setIndicators(indicators.filter((ind) => ind.id !== id));
    const series = indicatorSeriesRefs.current.get(`indicator-${id}`);
    if (series && chartRefs.current[0]) {
      chartRefs.current[0].removeSeries(series);
      indicatorSeriesRefs.current.delete(`indicator-${id}`);
    }
  };

  const handleSaveTemplate = async () => {
    const template = {
      id: `chart-template-${Date.now()}`,
      name: `Template ${new Date().toLocaleString()}`,
      pair: selectedPair,
      timeframe,
      layout,
      indicators: indicators.map((ind) => ({
        indicatorId: ind.indicatorId,
        parameters: ind.parameters,
        color: ind.color,
      })),
      drawings,
      createdAt: Date.now(),
    };

    try {
      // Get existing chart templates from preferences
      const existingTemplates = (preferences?.uiSettings as any)?.chartTemplates || [];
      
      // Add new template to the list
      const updatedTemplates = [...existingTemplates, template];
      
      // Save to backend via preferences API
      await updatePreferences({
        uiSettings: {
          ...preferences?.uiSettings,
          chartTemplates: updatedTemplates,
        } as any,
      });
      
      toast({
        title: "Template Saved",
        description: "Chart template saved successfully",
      });
    } catch (error) {
      console.error("Failed to save chart template:", error);
      toast({
        title: "Error",
        description: "Failed to save chart template. Please try again.",
        variant: "destructive",
      });
    }
  };

  const timeframes = ["1m", "5m", "15m", "1H", "4H", "1D", "1W", "1M"];
  const layouts: ChartLayout[] = [
    { id: "1", name: "Single", charts: 1 },
    { id: "2", name: "2 Charts", charts: 2 },
    { id: "4", name: "4 Charts", charts: 4 },
  ];

  return (
    <div className={`space-y-4 ${isFullscreen ? "fixed inset-0 z-50 bg-background p-4" : ""}`}>
      <Tabs defaultValue="charts" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="charts">Charts</TabsTrigger>
          <TabsTrigger value="heatmap">Heatmap & Correlation</TabsTrigger>
        </TabsList>
        
        <TabsContent value="charts" className="space-y-4">
          <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <LineChart className="h-5 w-5" />
                Advanced Charting Terminal
              </CardTitle>
              <CardDescription>
                Professional trading charts with indicators, drawings, and alerts
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={handleSaveTemplate}>
                <Save className="h-4 w-4 mr-2" />
                Save Template
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsFullscreen(!isFullscreen)}
              >
                {isFullscreen ? (
                  <Minimize2 className="h-4 w-4" />
                ) : (
                  <Maximize2 className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Controls */}
          <div className="flex flex-wrap items-center gap-4 p-4 border rounded-lg">
            <div className="flex items-center gap-2">
              <Label>Pair</Label>
              <Input
                value={selectedPair}
                onChange={(e) => setSelectedPair(e.target.value)}
                className="w-32"
                placeholder="BTC/USD"
              />
            </div>

            <div className="flex items-center gap-2">
              <Label>Timeframe</Label>
              <Select value={timeframe} onValueChange={setTimeframe}>
                <SelectTrigger className="w-24">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {timeframes.map((tf) => (
                    <SelectItem key={tf} value={tf}>
                      {tf}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <Label>Layout</Label>
              <Select
                value={layout.id}
                onValueChange={(id) => {
                  const selectedLayout = layouts.find((l) => l.id === id);
                  if (selectedLayout) setLayout(selectedLayout);
                }}
              >
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {layouts.map((l) => (
                    <SelectItem key={l.id} value={l.id}>
                      {l.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Dialog open={indicatorDialogOpen} onOpenChange={setIndicatorDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Indicator
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Add Indicator</DialogTitle>
                  <DialogDescription>
                    Select an indicator from the marketplace to overlay on your chart
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-2 max-h-[60vh] overflow-y-auto">
                  {marketplaceIndicators?.indicators.map((indicator) => (
                    <div
                      key={indicator.id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent cursor-pointer"
                      onClick={() => handleAddIndicator(indicator.id)}
                    >
                      <div>
                        <div className="font-semibold">{indicator.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {indicator.description}
                        </div>
                        <div className="flex gap-2 mt-1">
                          {indicator.category && (
                            <Badge variant="outline">{indicator.category}</Badge>
                          )}
                          {indicator.is_free && (
                            <Badge variant="secondary">Free</Badge>
                          )}
                        </div>
                      </div>
                      <Button size="sm">Add</Button>
                    </div>
                  ))}
                </div>
              </DialogContent>
            </Dialog>

            <Button variant="outline" size="sm">
              <Layers className="h-4 w-4 mr-2" />
              Drawings
            </Button>

            <Dialog open={alertDialogOpen} onOpenChange={setAlertDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm">
                  <AlertCircle className="h-4 w-4 mr-2" />
                  Alerts ({alerts.filter((a) => a.active).length})
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Price Alerts</DialogTitle>
                  <DialogDescription>
                    Set alerts to be notified when price reaches a target level
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Pair</Label>
                    <Input value={selectedPair} readOnly />
                  </div>
                  <div className="space-y-2">
                    <Label>Condition</Label>
                    <Select
                      defaultValue="above"
                      onValueChange={(value: "above" | "below") => {
                        // Will be used when creating alert
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="above">Price goes above</SelectItem>
                        <SelectItem value="below">Price goes below</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Target Price</Label>
                    <Input
                      type="number"
                      placeholder="Enter target price"
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          const price = parseFloat(e.currentTarget.value);
                          const condition = (e.currentTarget.closest(".space-y-4")?.querySelector("select") as HTMLSelectElement)?.value as "above" | "below";
                          if (price && condition) {
                            const newAlert = {
                              id: `alert-${Date.now()}`,
                              pair: selectedPair,
                              condition,
                              price,
                              active: true,
                            };
                            setAlerts([...alerts, newAlert]);
                            setAlertDialogOpen(false);
                            toast({
                              title: "Alert Created",
                              description: `Alert set for ${selectedPair} ${condition} $${price}`,
                            });
                          }
                        }
                      }}
                    />
                  </div>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    <Label>Active Alerts</Label>
                    {alerts.filter((a) => a.active).length === 0 ? (
                      <p className="text-sm text-muted-foreground">No active alerts</p>
                    ) : (
                      alerts
                        .filter((a) => a.active)
                        .map((alert) => (
                          <div
                            key={alert.id}
                            className="flex items-center justify-between p-2 border rounded"
                          >
                            <div>
                              <div className="font-medium">{alert.pair}</div>
                              <div className="text-sm text-muted-foreground">
                                {alert.condition === "above" ? ">" : "<"} ${alert.price}
                              </div>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setAlerts(alerts.map((a) => (a.id === alert.id ? { ...a, active: false } : a)));
                              }}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </div>
                        ))
                    )}
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Active Indicators */}
          {indicators.length > 0 && (
            <div className="flex flex-wrap gap-2 p-3 border rounded-lg bg-muted/50">
              <span className="text-sm font-medium">Active Indicators:</span>
              {indicators.map((indicator) => (
                <Badge
                  key={indicator.id}
                  variant="secondary"
                  className="flex items-center gap-1 cursor-pointer"
                  style={{ backgroundColor: indicator.color + "20", borderColor: indicator.color }}
                >
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: indicator.color }}
                  />
                  {indicator.name}
                  <button
                    onClick={() => handleRemoveIndicator(indicator.id)}
                    className="ml-1 hover:bg-destructive/20 rounded p-0.5"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}

          {/* Chart Grid */}
          <div
            className={`grid gap-4 ${
              layout.charts === 1
                ? "grid-cols-1"
                : layout.charts === 2
                ? "grid-cols-2"
                : "grid-cols-2"
            }`}
            style={{ minHeight: isFullscreen ? "calc(100vh - 300px)" : "600px" }}
          >
            {Array.from({ length: layout.charts }).map((_, index) => (
              <Card key={index} className="relative">
                <CardContent className="p-0">
                  <div
                    id={`chart-container-${index}`}
                    className="w-full"
                    style={{ height: layout.charts === 1 ? "600px" : "400px" }}
                  />
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
        </TabsContent>
        
        <TabsContent value="heatmap" className="space-y-4">
          <MarketHeatmap
            defaultSymbols={[
              selectedPair,
              "ETH/USD",
              "BNB/USD",
              "SOL/USD",
              "ADA/USD",
              "XRP/USD",
              "DOT/USD",
              "MATIC/USD",
            ]}
            showControls={true}
            height={600}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
