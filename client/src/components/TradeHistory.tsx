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
    <Card className="glass-premium border-border/50 shadow-2xl overflow-hidden">
      <CardHeader className="pb-4 border-b border-primary/10 bg-gradient-to-r from-primary/5 to-transparent">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <CardTitle className="text-xl font-black tracking-tight bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent uppercase">Trade Ledger</CardTitle>
          <div className="flex items-center gap-2 flex-wrap">
            <Button variant="outline" size="sm" onClick={handleExportCSV} className="border-primary/20 hover:bg-primary/10 transition-colors font-bold">
              <Download className="h-3.5 w-3.5 mr-1.5" /> CSV
            </Button>
            <Button variant="outline" size="sm" onClick={handleExportJSON} className="border-primary/20 hover:bg-primary/10 transition-colors font-bold">
              <Download className="h-3.5 w-3.5 mr-1.5" /> JSON
            </Button>
            <Button variant="outline" size="sm" onClick={handleExportPDF} className="border-primary/20 hover:bg-primary/10 transition-colors font-bold">
              <Download className="h-3.5 w-3.5 mr-1.5" /> PDF
            </Button>
          </div>
        </div>
        {/* Filters */}
        <div className="flex items-center gap-3 mt-6 flex-wrap">
          <div className="flex items-center gap-2 bg-muted/30 p-1 rounded-xl border border-border/50">
            <Select value={filterMode} onValueChange={setFilterMode}>
              <SelectTrigger className="w-[130px] border-none bg-transparent h-8 font-bold text-xs">
                <Filter className="h-3.5 w-3.5 mr-2 text-primary" />
                <SelectValue placeholder="Mode" />
              </SelectTrigger>
              <SelectContent className="glass-premium">
                <SelectItem value="all">All Modes</SelectItem>
                <SelectItem value="paper">Paper Trading</SelectItem>
                <SelectItem value="real">Real Money</SelectItem>
              </SelectContent>
            </Select>
            <div className="h-4 w-px bg-border/50 mx-1" />
            <Select value={filterSide} onValueChange={setFilterSide}>
              <SelectTrigger className="w-[110px] border-none bg-transparent h-8 font-bold text-xs">
                <SelectValue placeholder="Side" />
              </SelectTrigger>
              <SelectContent className="glass-premium">
                <SelectItem value="all">Both Sides</SelectItem>
                <SelectItem value="buy">Buys Only</SelectItem>
                <SelectItem value="sell">Sells Only</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          {chains.length > 0 && (
            <Select value={filterChain} onValueChange={setFilterChain}>
              <SelectTrigger className="w-[150px] bg-muted/30 border-border/50 h-10 font-bold text-xs rounded-xl">
                <SelectValue placeholder="All Networks" />
              </SelectTrigger>
              <SelectContent className="glass-premium">
                <SelectItem value="all">All Networks</SelectItem>
                {chains.map(chain => (
                  <SelectItem key={chain || "unknown"} value={chain || ""}>
                    {chain || "Unknown"}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          
          <div className="ml-auto text-[10px] font-black uppercase tracking-widest text-muted-foreground/70">
            Captured {filteredTrades.length} / {trades.length} trades
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {filteredTrades.length === 0 ? (
          <div className="p-12">
            <EmptyTradesState 
              onRefresh={() => window.location.reload()} 
            />
          </div>
        ) : filteredTrades.length > 50 ? (
          // Use virtual scrolling for large lists (50+ items)
          <div className="p-4">
            <VirtualizedList
              items={filteredTrades}
              itemHeight={80}
              containerHeight={400}
              renderItem={(trade, index) => {
                const tradeSide = trade.side || trade.type;
                const isBuy = tradeSide === "buy";
                
                return (
                  <div
                    className="mx-2 mb-2"
                    data-testid={`trade-${trade.id}`}
                    aria-label={`Trade ${index + 1}: ${tradeSide} ${trade.amount} ${trade.pair} at $${trade.price.toLocaleString()}`}
                    tabIndex={0}
                  >
                    <TradeItem trade={trade} isBuy={isBuy} tradeSide={tradeSide} />
                  </div>
                );
              }}
              emptyState={
                <div className="text-center py-12 text-muted-foreground font-medium italic">
                  No trades found matching your filters
                </div>
              }
            />
          </div>
        ) : (
          <ScrollArea className="h-[400px] modern-scrollbar">
            <div className="p-4 space-y-3">
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
