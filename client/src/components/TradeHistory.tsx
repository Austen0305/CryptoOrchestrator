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
  const [filterMode, setFilterMode] = useState<string>("all"); // 'all', 'paper', 'real'
  const [filterSide, setFilterSide] = useState<string>("all"); // 'all', 'buy', 'sell'
  const [filterExchange, setFilterExchange] = useState<string>("all");

  // Get unique exchanges from trades - memoized
  const exchanges = useMemo(() => 
    Array.from(new Set(trades.map(t => t.exchange).filter(Boolean))),
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
    
    // Filter by exchange
    if (filterExchange !== "all" && trade.exchange !== filterExchange) {
      return false;
    }
    
    return true;
  }), [trades, filterMode, filterSide, filterExchange]);

  const handleExportCSV = useCallback(() => {
    const rows = formatTradesForExport(filteredTrades);
    exportWithNotification(() => exportToCSV(rows, { filename: `trades-${Date.now()}.csv` }), toast, 'Trades exported to CSV');
  }, [filteredTrades, toast]);

  const handleExportJSON = useCallback(() => {
    exportWithNotification(() => exportToJSON(filteredTrades, { filename: `trades-${Date.now()}.json` }), toast, 'Trades exported to JSON');
  }, [filteredTrades, toast]);

  const handleExportPDF = useCallback(() => {
    exportWithNotification(() => exportTradesToPDF(filteredTrades, { filename: `trades-${Date.now()}.pdf` }), toast, 'Trades exported to PDF');
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
          {exchanges.length > 0 && (
            <Select value={filterExchange} onValueChange={setFilterExchange}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Exchange" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Exchanges</SelectItem>
                {exchanges.map(exchange => (
                  <SelectItem key={exchange} value={exchange}>
                    {exchange}
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
