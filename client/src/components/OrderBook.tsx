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
    <Card className="glass-premium border-border/50 shadow-2xl overflow-hidden" role="region" aria-label="Order book">
      <CardHeader className="pb-3 border-b border-primary/10 bg-gradient-to-r from-primary/5 to-transparent">
        <CardTitle className="text-base font-black tracking-tight bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent uppercase">Order Book</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="px-4 py-2 border-b border-border/30 bg-muted/20">
          <div className="grid grid-cols-3 text-[10px] text-muted-foreground font-black uppercase tracking-widest">
            <div className="text-left" aria-label="Price in USD">Price</div>
            <div className="text-right" aria-label="Order amount">Amount</div>
            <div className="text-right" aria-label="Total value">Total</div>
          </div>
        </div>

        <ScrollArea className="h-[200px] modern-scrollbar">
          {!hasData || asks.length === 0 ? (
            <div className="px-4 py-8 text-center text-muted-foreground text-sm italic">
              Loading sell orders...
            </div>
          ) : (
            <div className="px-2 space-y-0.5 py-2" role="list">
              {asks.slice().reverse().map((ask, idx) => (
                <div
                  key={`ask-${idx}`}
                  className="grid grid-cols-3 text-xs font-mono py-1 px-2 rounded-lg hover:bg-trading-loss/10 transition-colors cursor-pointer group"
                  data-testid={`orderbook-ask-${idx}`}
                  role="listitem"
                  aria-label={`Ask order ${idx + 1}: ${ask.amount} at $${ask.price.toLocaleString()}, total $${ask.total.toLocaleString()}`}
                  tabIndex={0}
                >
                  <div className="text-trading-loss font-bold group-hover:scale-105 transition-transform origin-left">
                    {ask.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  <div className="text-right text-foreground font-medium">{ask.amount.toFixed(4)}</div>
                  <div className="text-right text-muted-foreground/70">
                    {ask.total.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        <div className="px-4 py-3 border-y border-primary/10 bg-primary/5 backdrop-blur-md">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground font-black uppercase tracking-tighter">Spread</span>
            <span className="font-mono font-black text-primary drop-shadow-glow-sm" data-testid="text-spread">
              ${spread.toFixed(2)}
            </span>
          </div>
        </div>

        <ScrollArea className="h-[200px] modern-scrollbar">
          {!hasData || bids.length === 0 ? (
            <div className="px-4 py-8 text-center text-muted-foreground text-sm italic">
              Loading buy orders...
            </div>
          ) : (
            <div className="px-2 space-y-0.5 py-2" role="list">
              {bids.map((bid, idx) => (
                <div
                  key={`bid-${idx}`}
                  className="grid grid-cols-3 text-xs font-mono py-1 px-2 rounded-lg hover:bg-trading-profit/10 transition-colors cursor-pointer group"
                  data-testid={`orderbook-bid-${idx}`}
                  role="listitem"
                  aria-label={`Bid order ${idx + 1}: ${bid.amount} at $${bid.price.toLocaleString()}, total $${bid.total.toLocaleString()}`}
                  tabIndex={0}
                >
                  <div className="text-trading-profit font-bold group-hover:scale-105 transition-transform origin-left">
                    {bid.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  <div className="text-right text-foreground font-medium">{bid.amount.toFixed(4)}</div>
                  <div className="text-right text-muted-foreground/70">
                    {bid.total.toLocaleString(undefined, { maximumFractionDigits: 0 })}
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
