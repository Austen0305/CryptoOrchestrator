import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { exportToCSV, exportToJSON, formatTradesForExport, exportWithNotification } from "@/lib/export";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";

interface Trade {
  id: string;
  pair: string;
  type: "buy" | "sell";
  amount: number;
  price: number;
  total: number;
  timestamp: string;
  status: "completed" | "pending" | "failed";
}

interface TradeHistoryProps {
  trades: Trade[];
}

export function TradeHistory({ trades }: TradeHistoryProps) {
  const { toast } = useToast();

  const handleExportCSV = () => {
    const rows = formatTradesForExport(trades);
    exportWithNotification(() => exportToCSV(rows, { filename: `trades-${Date.now()}.csv` }), toast, 'Trades exported to CSV');
  };

  const handleExportJSON = () => {
    exportWithNotification(() => exportToJSON(trades, { filename: `trades-${Date.now()}.json` }), toast, 'Trades exported to JSON');
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
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px] pr-4">
          <div className="space-y-3">
            {trades.map((trade) => (
              <div
                key={trade.id}
                className="flex items-center justify-between p-3 rounded-md border hover-elevate"
                data-testid={`trade-${trade.id}`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`p-2 rounded-md ${
                      trade.type === "buy"
                        ? "bg-trading-buy/10 text-trading-buy"
                        : "bg-trading-sell/10 text-trading-sell"
                    }`}
                  >
                    {trade.type === "buy" ? (
                      <ArrowDownRight className="h-4 w-4" />
                    ) : (
                      <ArrowUpRight className="h-4 w-4" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{trade.pair}</span>
                      <Badge
                        variant={trade.type === "buy" ? "default" : "destructive"}
                        className="text-xs"
                      >
                        {trade.type.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {trade.timestamp}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-mono font-semibold">
                    ${trade.total.toLocaleString()}
                  </div>
                  <div className="text-sm text-muted-foreground font-mono">
                    {trade.amount} @ ${trade.price.toLocaleString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
