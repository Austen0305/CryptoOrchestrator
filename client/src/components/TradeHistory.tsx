import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  return (
    <Card>
      <CardHeader>
        <CardTitle>Trade History</CardTitle>
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
