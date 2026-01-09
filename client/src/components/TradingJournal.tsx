import React, { useState, useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { CalendarIcon, Plus, Search, Download, Filter, FileText, TrendingUp, TrendingDown, DollarSign } from "lucide-react";
import { OptimizedSearch } from "@/components/OptimizedSearch";
import { format } from "date-fns";
import { useTrades } from "@/hooks/useApi";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";
import { formatCurrency, formatPercentage } from "@/lib/formatters";
import { useDebounce } from "@/hooks/useDebounce";
import { usePagination } from "@/hooks/usePagination";
import { Pagination } from "@/components/Pagination";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { EmptyState } from "@/components/EmptyState";
import { ErrorRetry } from "@/components/ErrorRetry";
import type { Trade } from "@shared/schema";

interface TradeEntry {
  id: string;
  date: Date;
  symbol: string;
  side: "buy" | "sell";
  entryPrice: number;
  exitPrice?: number;
  quantity: number;
  fees: number;
  pnl?: number;
  pnlPercent?: number;
  strategy: string;
  notes: string;
  screenshot?: string;
  tags: string[];
}

export function TradingJournal() {
  const { data: trades, isLoading, error, refetch } = useTrades();
  const { toast } = useToast();
  const [searchTerm, setSearchTerm] = useState("");
  const debouncedSearchTerm = useDebounce(searchTerm, 300);
  const [selectedDate, setSelectedDate] = useState<Date>();
  const [filterStrategy, setFilterStrategy] = useState<string>("all");
  const [filterSide, setFilterSide] = useState<string>("all");
  const [selectedTrade, setSelectedTrade] = useState<TradeEntry | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  // Transform API trades to TradeEntry format
  // Trade type from API may have additional fields, so we use a union type for flexibility
  const tradesArray = Array.isArray(trades) ? trades : [];
  const transformedTrades: TradeEntry[] = tradesArray.map((trade: Trade & {
    tradeId?: string;
    date?: number | string;
    symbol?: string;
    exitPrice?: number;
    entryPrice?: number;
    profitLoss?: number;
    profitLossPercent?: number;
    strategy?: string;
    notes?: string;
    comment?: string;
    tags?: string[];
    quantity?: number; // Add optional quantity property
    pnl?: number; // Add optional pnl property
    pnlPercent?: number; // Add optional pnlPercent property
  }) => ({
    id: trade.id || trade.tradeId || String(Math.random()),
    date: new Date(trade.timestamp || trade.date || Date.now()),
    symbol: trade.pair || trade.symbol || "N/A",
    side: trade.side || "buy",
    entryPrice: trade.price || trade.entryPrice || 0,
    exitPrice: trade.exitPrice,
    quantity: (trade.amount ?? trade.quantity ?? 0) as number,
    fees: trade.fee || 0,
    pnl: trade.pnl ?? trade.profitLoss ?? undefined,
    pnlPercent: trade.pnlPercent ?? trade.profitLossPercent ?? undefined,
    strategy: trade.strategy || trade.botId || "Manual",
    notes: trade.notes || trade.comment || "",
    tags: trade.tags || [],
  }));

  const filteredTrades = useMemo(() => {
    return transformedTrades.filter(trade => {
      const matchesSearch = trade.symbol.toLowerCase().includes(debouncedSearchTerm.toLowerCase()) ||
        trade.notes.toLowerCase().includes(debouncedSearchTerm.toLowerCase()) ||
        trade.strategy.toLowerCase().includes(debouncedSearchTerm.toLowerCase());
      
      const matchesStrategy = filterStrategy === "all" || trade.strategy === filterStrategy;
      const matchesSide = filterSide === "all" || trade.side === filterSide;
      const matchesDate = !selectedDate || format(trade.date, "yyyy-MM-dd") === format(selectedDate, "yyyy-MM-dd");

      return matchesSearch && matchesStrategy && matchesSide && matchesDate;
    });
  }, [transformedTrades, debouncedSearchTerm, filterStrategy, filterSide, selectedDate]);

  const { page, pageSize, totalPages, totalItems, goToPage, setPageSize } = usePagination({
    totalItems: filteredTrades.length,
    initialPageSize: 10,
  });

  const paginatedTrades = useMemo(() => {
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    return filteredTrades.slice(start, end);
  }, [filteredTrades, page, pageSize]);

  const totalPnL = useMemo(() => filteredTrades.reduce((sum, trade) => sum + (trade.pnl || 0), 0), [filteredTrades]);
  const totalTrades = filteredTrades.length;
  const winningTrades = useMemo(() => filteredTrades.filter(t => (t.pnl || 0) > 0).length, [filteredTrades]);
  const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0;

  const strategies = Array.from(new Set(transformedTrades.map(t => t.strategy)));

  const handleExportPDF = async () => {
    const { exportTradesToPDF, exportWithNotification } = await import('@/lib/export');
    // Convert TradeEntry[] to TradeExport[]
    const exportTrades = filteredTrades.map(trade => ({
      timestamp: trade.date.getTime(),
      date: trade.date.toISOString(),
      symbol: trade.symbol,
      pair: trade.symbol,
      side: trade.side,
      type: trade.side,
      price: trade.entryPrice,
      amount: trade.quantity,
      total: trade.entryPrice * trade.quantity,
      fees: trade.fees,
      pnl: trade.pnl,
      pnlPercent: trade.pnlPercent,
      strategy: trade.strategy,
      notes: trade.notes
    }));
    exportWithNotification(
      () => exportTradesToPDF(exportTrades, { filename: `trading-journal-${Date.now()}.pdf` }),
      toast,
      'Trading journal exported to PDF'
    );
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Trading Journal
            </CardTitle>
            <CardDescription>
              Track and analyze all your trades with notes and screenshots
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Export PDF
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Export Trading Journal</DialogTitle>
                  <DialogDescription>
                    Export your trading journal to PDF for record keeping and analysis.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Date Range</label>
                    <div className="grid grid-cols-2 gap-2 mt-1">
                      <Input type="date" placeholder="Start Date" />
                      <Input type="date" placeholder="End Date" />
                    </div>
                  </div>
                  <Button onClick={handleExportPDF} className="w-full">
                    <Download className="h-4 w-4 mr-2" />
                    Generate PDF
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Add Trade
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="trades" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="trades">Trades</TabsTrigger>
            <TabsTrigger value="stats">Statistics</TabsTrigger>
            <TabsTrigger value="notes">Notes</TabsTrigger>
          </TabsList>

          <TabsContent value="trades" className="space-y-4">
            {/* Filters */}
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative flex-1 min-w-[200px]">
                <OptimizedSearch
                  value={searchTerm}
                  onChange={setSearchTerm}
                  placeholder="Search trades..."
                  className="w-full"
                />
              </div>
              <Select value={filterStrategy} onValueChange={setFilterStrategy}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Strategy" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Strategies</SelectItem>
                  {strategies.map(strategy => (
                    <SelectItem key={strategy} value={strategy}>{strategy}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={filterSide} onValueChange={setFilterSide}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="Side" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="buy">Buy</SelectItem>
                  <SelectItem value="sell">Sell</SelectItem>
                </SelectContent>
              </Select>
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="w-[240px] justify-start text-left font-normal">
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {selectedDate ? format(selectedDate, "PPP") : "Filter by date"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={selectedDate}
                    onSelect={setSelectedDate}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm font-medium text-muted-foreground">Total Trades</div>
                  <div className="text-2xl font-bold">{totalTrades}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm font-medium text-muted-foreground">Total P&L</div>
                  <div className={cn("text-2xl font-bold", totalPnL >= 0 ? "text-green-500" : "text-red-500")}>
                    {formatCurrency(totalPnL)}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm font-medium text-muted-foreground">Win Rate</div>
                  <div className="text-2xl font-bold">{formatPercentage(winRate)}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm font-medium text-muted-foreground">Winning Trades</div>
                  <div className="text-2xl font-bold text-green-500">{winningTrades}</div>
                </CardContent>
              </Card>
            </div>

            {/* Trades Table */}
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Side</TableHead>
                    <TableHead>Entry</TableHead>
                    <TableHead>Exit</TableHead>
                    <TableHead>Quantity</TableHead>
                    <TableHead>P&L</TableHead>
                    <TableHead>Strategy</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoading ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-8">
                        <LoadingSkeleton count={5} className="h-12 w-full" aria-label="Loading trades" />
                      </TableCell>
                    </TableRow>
                  ) : error ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-8">
                        <ErrorRetry
                          title="Failed to load trades"
                          message="Unable to fetch your trading journal. Please try again."
                          onRetry={() => refetch()}
                          error={error as Error}
                        />
                      </TableCell>
                    </TableRow>
                  ) : filteredTrades.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-8">
                        <EmptyState
                          icon={FileText}
                          title="No trades found"
                          description={
                            searchTerm || filterStrategy !== "all" || filterSide !== "all" || selectedDate
                              ? "Try adjusting your filters to see more trades."
                              : "Start trading to see your journal entries."
                          }
                        />
                      </TableCell>
                    </TableRow>
                  ) : (
                    paginatedTrades.map((trade) => (
                      <TableRow key={trade.id} className="cursor-pointer hover:bg-muted/50" onClick={() => {
                        setSelectedTrade(trade);
                        setIsDialogOpen(true);
                      }}>
                        <TableCell>{format(trade.date, "MMM dd, yyyy HH:mm")}</TableCell>
                        <TableCell className="font-medium">{trade.symbol}</TableCell>
                        <TableCell>
                          <Badge variant={trade.side === "buy" ? "default" : "destructive"}>
                            {trade.side.toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell>{formatCurrency(trade.entryPrice)}</TableCell>
                        <TableCell>{trade.exitPrice ? formatCurrency(trade.exitPrice) : "-"}</TableCell>
                        <TableCell>{trade.quantity}</TableCell>
                        <TableCell>
                          <div className={cn("font-medium", trade.pnl && trade.pnl >= 0 ? "text-green-500" : "text-red-500")}>
                            {trade.pnl ? (
                              <>
                                {formatCurrency(trade.pnl)} ({formatPercentage(trade.pnlPercent || 0)})
                              </>
                            ) : (
                              "-"
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{trade.strategy}</Badge>
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm">View</Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
            {totalItems > pageSize && (
              <Pagination
                page={page}
                pageSize={pageSize}
                totalPages={totalPages}
                totalItems={totalItems}
                onPageChange={goToPage}
                onPageSizeChange={setPageSize}
                className="mt-4"
              />
            )}
          </TabsContent>

          <TabsContent value="stats" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Performance by Strategy</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {strategies.map(strategy => {
                      const strategyTrades = filteredTrades.filter(t => t.strategy === strategy);
                      const strategyPnL = strategyTrades.reduce((sum, t) => sum + (t.pnl || 0), 0);
                      const strategyWinRate = strategyTrades.length > 0
                        ? (strategyTrades.filter(t => (t.pnl || 0) > 0).length / strategyTrades.length) * 100
                        : 0;
                      return (
                        <div key={strategy} className="flex items-center justify-between p-2 rounded border">
                          <div>
                            <div className="font-medium">{strategy}</div>
                            <div className="text-sm text-muted-foreground">
                              {strategyTrades.length} trades
                            </div>
                          </div>
                          <div className="text-right">
                            <div className={cn("font-bold", strategyPnL >= 0 ? "text-green-500" : "text-red-500")}>
                              {formatCurrency(strategyPnL)}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {formatPercentage(strategyWinRate)} win rate
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Monthly Performance</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-8 text-muted-foreground">
                    Monthly performance chart coming soon...
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="notes" className="space-y-4">
            <div className="grid gap-4">
              {filteredTrades.filter(t => t.notes).map(trade => (
                <Card key={trade.id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-lg">{trade.symbol}</CardTitle>
                        <CardDescription>
                          {format(trade.date, "PPP")} • {trade.strategy}
                        </CardDescription>
                      </div>
                      <Badge variant={trade.pnl && trade.pnl >= 0 ? "default" : "destructive"}>
                        {trade.pnl ? formatCurrency(trade.pnl) : "Open"}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm whitespace-pre-wrap">{trade.notes}</p>
                    {trade.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-3">
                        {trade.tags.map(tag => (
                          <Badge key={tag} variant="secondary" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
              {filteredTrades.filter(t => t.notes).length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  No notes yet. Add notes to your trades to track insights and learnings.
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>

        {/* Trade Detail Dialog */}
        {selectedTrade && (
          <Dialog open={isDialogOpen && selectedTrade !== null} onOpenChange={(open) => {
            setIsDialogOpen(open);
            if (!open) setSelectedTrade(null);
          }}>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{selectedTrade.symbol} Trade Details</DialogTitle>
                <DialogDescription>
                  {format(selectedTrade.date, "PPP 'at' p")}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Side</label>
                    <div className="mt-1">
                      <Badge variant={selectedTrade.side === "buy" ? "default" : "destructive"}>
                        {selectedTrade.side.toUpperCase()}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Strategy</label>
                    <div className="mt-1">
                      <Badge variant="outline">{selectedTrade.strategy}</Badge>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Entry Price</label>
                    <div className="mt-1 font-medium">{formatCurrency(selectedTrade.entryPrice)}</div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Exit Price</label>
                    <div className="mt-1 font-medium">
                      {selectedTrade.exitPrice ? formatCurrency(selectedTrade.exitPrice) : "Open"}
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Quantity</label>
                    <div className="mt-1 font-medium">{selectedTrade.quantity}</div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Fees</label>
                    <div className="mt-1 font-medium">{formatCurrency(selectedTrade.fees)}</div>
                  </div>
                  {selectedTrade.pnl !== undefined && (
                    <>
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">Profit & Loss</label>
                        <div className={cn("mt-1 font-bold text-lg", selectedTrade.pnl >= 0 ? "text-green-500" : "text-red-500")}>
                          {formatCurrency(selectedTrade.pnl)}
                        </div>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">P&L Percentage</label>
                        <div className={cn("mt-1 font-bold text-lg", selectedTrade.pnl >= 0 ? "text-green-500" : "text-red-500")}>
                          {formatPercentage(selectedTrade.pnlPercent || 0)}
                        </div>
                      </div>
                    </>
                  )}
                </div>
                {selectedTrade.notes && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Notes</label>
                    <div className="mt-1 p-3 rounded-md bg-muted whitespace-pre-wrap">
                      {selectedTrade.notes}
                    </div>
                  </div>
                )}
                {selectedTrade.tags.length > 0 && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Tags</label>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {selectedTrade.tags.map(tag => (
                        <Badge key={tag} variant="secondary">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </DialogContent>
          </Dialog>
        )}
      </CardContent>
    </Card>
  );
}

