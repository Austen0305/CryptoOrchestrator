import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, Filter } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { exportToCSV, exportToJSON, exportTradesToPDF, formatTradesForExport, exportWithNotification } from "@/lib/export";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useTradingMode } from "@/contexts/TradingModeContext";
import { EmptyTradesState } from "@/components/EmptyState";
import { useState, useMemo, useCallback } from "react";
import React from "react";
import { VirtualizedList } from "@/components/VirtualizedList";
import { TradeItem } from "@/components/memoized/TradeItem";

interface Trade {
  id: string;
  pair: string;
  type: "buy" | "sell";
  side?: "buy" | "sell";
  amount: number;
  price: number;
  total: number;
  timestamp: string;
  status: "completed" | "pending" | "failed";
  mode?: "paper" | "real";
  exchange?: string;
  pnl?: number;
}

interface TradeHistoryProps {
  trades: Trade[];
}

// Removed renderTradeItem - now using memoized TradeItem component

export const TradeHistory = React.memo(function TradeHistory({ trades }: TradeHistoryProps) {
  const { toast } = useToast();
  const { mode } = useTradingMode();
  // Default to current trading mode instead of "all"
  const [filterMode, setFilterMode] = useState<string>(mode); // 'all', 'paper', 'real'
  const [filterSide, setFilterSide] = useState<string>("all"); // 'all', 'buy', 'sell'
  const [filterChain, setFilterChain] = useState<string>("all");

  // Get unique chains/aggregators from trades - memoized
  const chains = useMemo(() => 
    Array.from(new Set(trades.map(t => t.exchange || (t as any).chain_id ? `Chain ${(t as any).chain_id}` : null).filter(Boolean))),
    [trades]
  );

  // Filter trades - memoized for performance
  const filteredTrades = useMemo(() => trades.filter(trade => {
    // Filter by mode
    if (filterMode !== "all" && trade.mode !== filterMode) {
      return false;
    }
    
    // Filter by side
    const tradeSide = trade.side || trade.type;
    if (filterSide !== "all" && tradeSide !== filterSide) {
      return false;
    }
    
    // Filter by chain/aggregator
    if (filterChain !== "all") {
      const tradeChain = trade.exchange || ((trade as any).chain_id ? `Chain ${(trade as any).chain_id}` : null);
      if (tradeChain !== filterChain) {
        return false;
      }
    }
    
    return true;
  }), [trades, filterMode, filterSide, filterChain]);

  const handleExportCSV = useCallback(() => {
    // Convert Trade[] to TradeExport[] ensuring side is always a string
    const exportTrades = filteredTrades.map(trade => ({
      ...trade,
      side: trade.side || trade.type || "buy",
      type: trade.type || trade.side || "buy"
    }));
    const rows = formatTradesForExport(exportTrades);
    exportWithNotification(() => exportToCSV(rows, { filename: `trades-${Date.now()}.csv` }), toast, 'Trades exported to CSV');
  }, [filteredTrades, toast]);

  const handleExportJSON = useCallback(() => {
    // Convert Trade[] to TradeExport[] ensuring side is always a string
    const exportTrades = filteredTrades.map(trade => ({
      ...trade,
      side: trade.side || trade.type || "buy",
      type: trade.type || trade.side || "buy"
    }));
    exportWithNotification(() => exportToJSON(exportTrades, { filename: `trades-${Date.now()}.json` }), toast, 'Trades exported to JSON');
  }, [filteredTrades, toast]);

  const handleExportPDF = useCallback(() => {
    // Convert Trade[] to TradeExport[] ensuring side is always a string
    const exportTrades = filteredTrades.map(trade => ({
      ...trade,
      side: trade.side || trade.type || "buy",
      type: trade.type || trade.side || "buy"
    }));
    exportWithNotification(() => exportTradesToPDF(exportTrades, { filename: `trades-${Date.now()}.pdf` }), toast, 'Trades exported to PDF');
  }, [filteredTrades, toast]);

  return (
    <Card className="border-card-border shadow-md">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <CardTitle className="text-lg font-bold">Trade History</CardTitle>
          <div className="flex items-center gap-2 flex-wrap">
            <Button variant="outline" size="sm" onClick={handleExportCSV} data-testid="button-export-trades-csv" className="rounded-md">
              <Download className="h-3.5 w-3.5 mr-1.5" /> CSV
            </Button>
            <Button variant="outline" size="sm" onClick={handleExportJSON} data-testid="button-export-trades-json" className="rounded-md">
              <Download className="h-3.5 w-3.5 mr-1.5" /> JSON
            </Button>
            <Button variant="outline" size="sm" onClick={handleExportPDF} data-testid="button-export-trades-pdf" className="rounded-md">
              <Download className="h-3.5 w-3.5 mr-1.5" /> PDF
            </Button>
          </div>
        </div>
        {/* Filters */}
        <div className="flex items-center gap-2 mt-4">
          <Select value={filterMode} onValueChange={setFilterMode}>
            <SelectTrigger className="w-[120px]">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Mode" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Modes</SelectItem>
              <SelectItem value="paper">Paper</SelectItem>
              <SelectItem value="real">Real Money</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filterSide} onValueChange={setFilterSide}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="Side" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Sides</SelectItem>
              <SelectItem value="buy">Buy</SelectItem>
              <SelectItem value="sell">Sell</SelectItem>
            </SelectContent>
          </Select>
          {chains.length > 0 && (
            <Select value={filterChain} onValueChange={setFilterChain}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Chain" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Chains</SelectItem>
                {chains.map(chain => (
                  <SelectItem key={chain || "unknown"} value={chain || ""}>
                    {chain || "Unknown"}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <div className="ml-auto text-sm text-muted-foreground">
            Showing {filteredTrades.length} of {trades.length} trades
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {filteredTrades.length === 0 ? (
          <EmptyTradesState 
            onRefresh={() => window.location.reload()} 
          />
        ) : filteredTrades.length > 50 ? (
          // Use virtual scrolling for large lists (50+ items)
          <VirtualizedList
            items={filteredTrades}
            itemHeight={80}
            containerHeight={400}
            renderItem={(trade, index) => {
              const tradeSide = trade.side || trade.type;
              const isBuy = tradeSide === "buy";
              
              return (
                <div
                  className="mx-2"
                  data-testid={`trade-${trade.id}`}
                  aria-label={`Trade ${index + 1}: ${tradeSide} ${trade.amount} ${trade.pair} at $${trade.price.toLocaleString()}`}
                  tabIndex={0}
                >
                  <TradeItem trade={trade} isBuy={isBuy} tradeSide={tradeSide} />
                </div>
              );
            }}
            emptyState={
              <div className="text-center py-8 text-muted-foreground">
                No trades found matching your filters
              </div>
            }
          />
        ) : (
          <ScrollArea className="h-[400px] pr-4">
            <div className="space-y-3">
              {filteredTrades.map((trade) => {
                const tradeSide = trade.side || trade.type;
                const isBuy = tradeSide === "buy";
                
                return (
                  <TradeItem
                    key={trade.id}
                    trade={trade}
                    isBuy={isBuy}
                    tradeSide={tradeSide}
                  />
                );
              })}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
});
