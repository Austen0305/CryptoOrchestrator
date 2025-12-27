import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { EmptyState } from "@/components/EmptyState";
import { BookOpen } from "lucide-react";

interface OrderBookEntry {
  price: number;
  amount: number;
  total: number;
}

interface OrderBookProps {
  bids: OrderBookEntry[];
  asks: OrderBookEntry[];
  spread: number;
  isLoading?: boolean;
  error?: Error | null;
}

export const OrderBook = React.memo(function OrderBook({ bids, asks, spread, isLoading = false, error = null }: OrderBookProps) {
  if (isLoading) {
    return (
      <Card className="border-card-border" role="region" aria-label="Order book">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-bold">Order Book</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <LoadingSkeleton count={10} className="h-6 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-card-border" role="region" aria-label="Order book">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-bold">Order Book</CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <EmptyState
            icon={BookOpen}
            title="Failed to load order book"
            description={error.message || "Unable to fetch order book data. Please try again later."}
          />
        </CardContent>
      </Card>
    );
  }

  const hasData = bids.length > 0 || asks.length > 0;

  return (
    <Card className="border-card-border" role="region" aria-label="Order book">
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-bold">Order Book</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="px-4 pb-2.5 border-b border-border/50">
          <div className="grid grid-cols-3 text-xs text-muted-foreground font-semibold uppercase tracking-wide">
            <div className="text-left" aria-label="Price in USD">Price (USD)</div>
            <div className="text-right" aria-label="Order amount">Amount</div>
            <div className="text-right" aria-label="Total value">Total</div>
          </div>
        </div>

        <ScrollArea className="h-[200px]">
          {!hasData || asks.length === 0 ? (
            <div className="px-4 py-8 text-center text-muted-foreground text-sm">
              No ask orders available
            </div>
          ) : (
            <div className="px-4 space-y-0.5 py-1" role="list">
              {asks.slice().reverse().map((ask, idx) => (
                <div
                  key={`ask-${idx}`}
                  className="grid grid-cols-3 text-xs font-mono py-1 px-2 rounded-md hover:bg-trading-sell/5 transition-colors cursor-pointer"
                  data-testid={`orderbook-ask-${idx}`}
                  role="listitem"
                  aria-label={`Ask order ${idx + 1}: ${ask.amount} at $${ask.price.toLocaleString()}, total $${ask.total.toLocaleString()}`}
                  tabIndex={0}
                >
                  <div className="text-trading-sell font-semibold">
                    {ask.price.toLocaleString()}
                  </div>
                  <div className="text-right text-foreground">{ask.amount.toFixed(4)}</div>
                  <div className="text-right text-muted-foreground">
                    {ask.total.toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        <div className="px-4 py-2.5 border-y border-border/50 bg-muted/30">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground font-medium">Spread</span>
            <span className="font-mono font-bold text-foreground" data-testid="text-spread">
              ${spread.toFixed(2)}
            </span>
          </div>
        </div>

        <ScrollArea className="h-[200px]">
          {!hasData || bids.length === 0 ? (
            <div className="px-4 py-8 text-center text-muted-foreground text-sm">
              No bid orders available
            </div>
          ) : (
            <div className="px-4 space-y-0.5 py-1 pt-2" role="list">
              {bids.map((bid, idx) => (
                <div
                  key={`bid-${idx}`}
                  className="grid grid-cols-3 text-xs font-mono py-1 px-2 rounded-md hover:bg-trading-buy/5 transition-colors cursor-pointer"
                  data-testid={`orderbook-bid-${idx}`}
                  role="listitem"
                  aria-label={`Bid order ${idx + 1}: ${bid.amount} at $${bid.price.toLocaleString()}, total $${bid.total.toLocaleString()}`}
                  tabIndex={0}
                >
                  <div className="text-trading-buy font-semibold">
                    {bid.price.toLocaleString()}
                  </div>
                  <div className="text-right text-foreground">{bid.amount.toFixed(4)}</div>
                  <div className="text-right text-muted-foreground">
                    {bid.total.toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
});
