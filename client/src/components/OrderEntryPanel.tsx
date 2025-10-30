import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Slider } from "@/components/ui/slider";

export function OrderEntryPanel() {
  const [orderType, setOrderType] = useState<"market" | "limit" | "stop">("market");
  const [amount, setAmount] = useState("");
  const [price, setPrice] = useState("");
  const [percentage, setPercentage] = useState([0]);

  const handlePercentage = (value: number) => {
    setPercentage([value]);
    console.log(`Setting ${value}% of available balance`);
  };

  const handleOrder = (side: "buy" | "sell") => {
    console.log(`Placing ${side} order:`, { orderType, amount, price, percentage: percentage[0] });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Place Order</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Tabs value={orderType} onValueChange={(v) => setOrderType(v as any)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="market" data-testid="button-order-market">Market</TabsTrigger>
            <TabsTrigger value="limit" data-testid="button-order-limit">Limit</TabsTrigger>
            <TabsTrigger value="stop" data-testid="button-order-stop">Stop-Loss</TabsTrigger>
          </TabsList>
        </Tabs>

        {orderType === "limit" && (
          <div className="space-y-2">
            <Label htmlFor="price">Price</Label>
            <Input
              id="price"
              type="number"
              placeholder="0.00"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="font-mono"
              data-testid="input-price"
            />
          </div>
        )}

        <div className="space-y-2">
          <Label htmlFor="amount">Amount</Label>
          <Input
            id="amount"
            type="number"
            placeholder="0.00"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="font-mono"
            data-testid="input-amount"
          />
        </div>

        <div className="space-y-3">
          <Label>Quick Amount</Label>
          <div className="grid grid-cols-4 gap-2">
            {[25, 50, 75, 100].map((pct) => (
              <Button
                key={pct}
                variant="outline"
                size="sm"
                onClick={() => handlePercentage(pct)}
                data-testid={`button-percentage-${pct}`}
              >
                {pct}%
              </Button>
            ))}
          </div>
          <Slider
            value={percentage}
            onValueChange={setPercentage}
            max={100}
            step={1}
            className="mt-2"
          />
        </div>

        <div className="pt-2 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Available:</span>
            <span className="font-mono font-semibold">$10,500</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Total:</span>
            <span className="font-mono font-semibold">
              ${amount ? (parseFloat(amount) * (price ? parseFloat(price) : 47350)).toLocaleString() : "0.00"}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 pt-2">
          <Button
            className="bg-trading-buy hover:bg-trading-buy-hover text-white"
            onClick={() => handleOrder("buy")}
            data-testid="button-buy"
          >
            Buy
          </Button>
          <Button
            className="bg-trading-sell hover:bg-trading-sell-hover text-white"
            onClick={() => handleOrder("sell")}
            data-testid="button-sell"
          >
            Sell
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
