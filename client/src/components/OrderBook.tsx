import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

interface OrderBookEntry {
  price: number;
  amount: number;
  total: number;
}

interface OrderBookProps {
  bids: OrderBookEntry[];
  asks: OrderBookEntry[];
  spread: number;
}

export function OrderBook({ bids, asks, spread }: OrderBookProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Order Book</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="px-4 pb-2">
          <div className="grid grid-cols-3 text-xs text-muted-foreground font-medium">
            <div className="text-left">Price (USD)</div>
            <div className="text-right">Amount</div>
            <div className="text-right">Total</div>
          </div>
        </div>

        <ScrollArea className="h-[200px]">
          <div className="px-4 space-y-0.5">
            {asks.slice().reverse().map((ask, idx) => (
              <div
                key={`ask-${idx}`}
                className="grid grid-cols-3 text-xs font-mono hover-elevate py-0.5 rounded-sm"
                data-testid={`orderbook-ask-${idx}`}
              >
                <div className="text-trading-sell font-semibold">
                  {ask.price.toLocaleString()}
                </div>
                <div className="text-right">{ask.amount.toFixed(4)}</div>
                <div className="text-right text-muted-foreground">
                  {ask.total.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>

        <div className="px-4 py-2 border-y bg-muted/50">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Spread</span>
            <span className="font-mono font-semibold" data-testid="text-spread">
              ${spread.toFixed(2)}
            </span>
          </div>
        </div>

        <ScrollArea className="h-[200px]">
          <div className="px-4 space-y-0.5 pt-2">
            {bids.map((bid, idx) => (
              <div
                key={`bid-${idx}`}
                className="grid grid-cols-3 text-xs font-mono hover-elevate py-0.5 rounded-sm"
                data-testid={`orderbook-bid-${idx}`}
              >
                <div className="text-trading-buy font-semibold">
                  {bid.price.toLocaleString()}
                </div>
                <div className="text-right">{bid.amount.toFixed(4)}</div>
                <div className="text-right text-muted-foreground">
                  {bid.total.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
