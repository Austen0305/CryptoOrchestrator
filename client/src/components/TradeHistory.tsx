import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, Filter } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { exportToCSV, exportToJSON, exportTradesToPDF, formatTradesForExport, exportWithNotification } from "@/lib/export";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useTradingMode } from "@/contexts/TradingModeContext";
import { useState } from "react";

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

export function TradeHistory({ trades }: TradeHistoryProps) {
  const { toast } = useToast();
  const { mode } = useTradingMode();
  const [filterMode, setFilterMode] = useState<string>("all"); // 'all', 'paper', 'real'
  const [filterSide, setFilterSide] = useState<string>("all"); // 'all', 'buy', 'sell'
  const [filterExchange, setFilterExchange] = useState<string>("all");

  // Get unique exchanges from trades
  const exchanges = Array.from(new Set(trades.map(t => t.exchange).filter(Boolean)));

  // Filter trades
  const filteredTrades = trades.filter(trade => {
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
  });

  const handleExportCSV = () => {
    const rows = formatTradesForExport(filteredTrades);
    exportWithNotification(() => exportToCSV(rows, { filename: `trades-${Date.now()}.csv` }), toast, 'Trades exported to CSV');
  };

  const handleExportJSON = () => {
    exportWithNotification(() => exportToJSON(filteredTrades, { filename: `trades-${Date.now()}.json` }), toast, 'Trades exported to JSON');
  };

  const handleExportPDF = () => {
    exportWithNotification(() => exportTradesToPDF(filteredTrades, { filename: `trades-${Date.now()}.pdf` }), toast, 'Trades exported to PDF');
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Trade History</CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleExportCSV} data-testid="button-export-trades-csv">
              <Download className="h-4 w-4 mr-1" /> CSV
            </Button>
            <Button variant="outline" size="sm" onClick={handleExportJSON} data-testid="button-export-trades-json">
              <Download className="h-4 w-4 mr-1" /> JSON
            </Button>
            <Button variant="outline" size="sm" onClick={handleExportPDF} data-testid="button-export-trades-pdf">
              <Download className="h-4 w-4 mr-1" /> PDF
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
        <ScrollArea className="h-[400px] pr-4">
          <div className="space-y-3">
            {filteredTrades.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No trades found matching your filters
              </div>
            ) : (
              filteredTrades.map((trade) => {
                const tradeSide = trade.side || trade.type;
                const isBuy = tradeSide === "buy";
                
                return (
                  <div
                    key={trade.id}
                    className="flex items-center justify-between p-3 rounded-md border hover-elevate"
                    data-testid={`trade-${trade.id}`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`p-2 rounded-md ${
                          isBuy
                            ? "bg-trading-buy/10 text-trading-buy"
                            : "bg-trading-sell/10 text-trading-sell"
                        }`}
                      >
                        {isBuy ? (
                          <ArrowDownRight className="h-4 w-4" />
                        ) : (
                          <ArrowUpRight className="h-4 w-4" />
                        )}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold">{trade.pair}</span>
                          <Badge
                            variant={isBuy ? "default" : "destructive"}
                            className="text-xs"
                          >
                            {tradeSide.toUpperCase()}
                          </Badge>
                          {trade.mode && (
                            <Badge
                              variant={trade.mode === "real" ? "destructive" : "secondary"}
                              className="text-xs"
                            >
                              {trade.mode === "real" ? "Real" : "Paper"}
                            </Badge>
                          )}
                          {trade.exchange && (
                            <Badge variant="outline" className="text-xs">
                              {trade.exchange}
                            </Badge>
                          )}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {trade.timestamp}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono font-semibold">
                        ${(trade.total || (trade.amount * trade.price)).toLocaleString()}
                      </div>
                      <div className="text-sm text-muted-foreground font-mono">
                        {trade.amount} @ ${trade.price.toLocaleString()}
                      </div>
                      {trade.pnl !== undefined && trade.pnl !== null && (
                        <div className={`text-sm font-semibold ${trade.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                          {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
