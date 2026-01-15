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
    <Card className="border-border/50 shadow-none overflow-hidden h-full" role="region" aria-label="Order book">
      <CardHeader className="pb-3 border-b-2 border-primary/20 bg-background/50">
        <CardTitle className="text-base font-black tracking-tight text-primary uppercase font-mono">&gt; Order Book_</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="px-4 py-2 border-b border-border/30 bg-muted/20">
          <div className="grid grid-cols-3 text-[10px] text-muted-foreground font-black uppercase tracking-widest font-mono">
            <div className="text-left" aria-label="Price in USD">Price</div>
            <div className="text-right" aria-label="Order amount">Amount</div>
            <div className="text-right" aria-label="Total value">Total</div>
          </div>
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
