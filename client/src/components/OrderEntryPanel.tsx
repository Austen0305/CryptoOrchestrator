import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Keyboard, AlertTriangle, Shield } from "lucide-react";
import { useTradingMode } from "@/contexts/TradingModeContext";
import { apiRequest } from "@/lib/queryClient";
import { toast } from "@/components/ui/use-toast";
import { validateOrder, formatValidationErrors } from "@/lib/validation";
import { FormFieldError } from "@/components/FormFieldError";
import { useQuery } from "@tanstack/react-query";

interface OrderEntryPanelProps {
  /** Trading pair (e.g., "BTC/USD"). Defaults to "BTC/USD" if not provided. */
  pair?: string;
}

export function OrderEntryPanel({ pair = "BTC/USD" }: OrderEntryPanelProps) {
  const { mode, isRealMoney, isPaperTrading } = useTradingMode();
  const [orderType, setOrderType] = useState<"market" | "limit" | "stop" | "stop-limit" | "take-profit" | "trailing-stop">("market");
  const [stopPrice, setStopPrice] = useState("");
  const [takeProfitPrice, setTakeProfitPrice] = useState("");
  const [trailingStopPercent, setTrailingStopPercent] = useState("");
  const [timeInForce, setTimeInForce] = useState<"GTC" | "IOC" | "FOK">("GTC");
  const [amount, setAmount] = useState("");
  const [price, setPrice] = useState("");
  const [percentage, setPercentage] = useState([0]);
  const [exchange, setExchange] = useState<string>("");
  const [mfaToken, setMfaToken] = useState<string>("");
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [pendingOrder, setPendingOrder] = useState<{ side: "buy" | "sell"; amount: string; price: string; exchange?: string; mfaToken?: string } | null>(null);
  const [isPlacingOrder, setIsPlacingOrder] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const amountInputRef = useRef<HTMLInputElement>(null);
  const priceInputRef = useRef<HTMLInputElement>(null);

  // Load available exchanges using React Query
  const { data: exchangeKeys, isLoading: exchangesLoading } = useQuery<Array<{exchange: string, label: string | null}>>({
    queryKey: ['exchange-keys'],
    queryFn: async () => {
      return await apiRequest<Array<{exchange: string, label: string | null}>>("/api/exchange-keys", {
        method: "GET",
      });
    },
    enabled: isRealMoney,
    retry: 2,
  });

  // Transform exchange keys to the format expected by the component
  const availableExchanges = exchangeKeys
    ?.filter(k => k)
    .map(k => ({
      exchange: k.exchange,
      label: k.label || k.exchange.charAt(0).toUpperCase() + k.exchange.slice(1)
    })) || [];

  // Set default exchange when available exchanges load
  useEffect(() => {
    if (availableExchanges.length > 0 && !exchange) {
      setExchange(availableExchanges[0].exchange);
    }
  }, [availableExchanges, exchange]);

  const handlePercentage = (value: number) => {
    setPercentage([value]);
    // Percentage set via slider - no logging needed
  };

  const handleOrder = async (side: "buy" | "sell") => {
    // Validate inputs
    if (!amount || parseFloat(amount) <= 0) {
      toast({
        title: "Invalid Amount",
        description: "Please enter a valid amount",
        variant: "destructive",
      });
      return;
    }

    if ((orderType === "limit" || orderType === "stop-limit" || orderType === "take-profit") && (!price || parseFloat(price) <= 0)) {
      toast({
        title: "Invalid Price",
        description: "Please enter a valid price for this order type",
        variant: "destructive",
      });
      return;
    }

    if ((orderType === "stop" || orderType === "stop-limit") && (!stopPrice || parseFloat(stopPrice) <= 0)) {
      toast({
        title: "Invalid Stop Price",
        description: "Please enter a valid stop price",
        variant: "destructive",
      });
      return;
    }

    if (orderType === "trailing-stop" && (!trailingStopPercent || parseFloat(trailingStopPercent) <= 0)) {
      toast({
        title: "Invalid Trailing Stop",
        description: "Please enter a valid trailing stop percentage",
        variant: "destructive",
      });
      return;
    }

    // If real money, validate exchange is selected
    if (isRealMoney && !exchange && availableExchanges.length > 0) {
      toast({
        title: "Exchange Required",
        description: "Please select an exchange for real money trading",
        variant: "destructive",
      });
      return;
    }

    // If real money, show confirmation dialog
    if (isRealMoney) {
      setPendingOrder({ side, amount, price, exchange, mfaToken });
      setShowConfirmDialog(true);
      return;
    }

    // Paper trading - execute immediately
    await executeOrder(side, amount, price);
  };

  const executeOrder = async (side: "buy" | "sell", orderAmount: string, orderPrice: string, orderExchange?: string, orderMfaToken?: string) => {
    setIsPlacingOrder(true);
    try {
      interface OrderBody {
        pair: string;
        side: "buy" | "sell";
        type: string;
        amount: number;
        mode: string;
        exchange?: string;
        mfa_token?: string;
        price?: number;
        stop?: number;
        take_profit?: number;
        trailing_stop_percent?: number;
        time_in_force?: string;
      }

      const orderBody: OrderBody = {
        pair: pair,
        side,
        type: orderType,
        amount: parseFloat(orderAmount),
        mode: mode,
        exchange: orderExchange || exchange || undefined,
        mfa_token: orderMfaToken || mfaToken || undefined,
      };

      // Add price for limit orders
      if (orderPrice) {
        orderBody.price = parseFloat(orderPrice);
      }

      // Add stop price for stop orders
      if (stopPrice) {
        orderBody.stop = parseFloat(stopPrice);
      }

      // Add take profit price
      if (takeProfitPrice) {
        orderBody.take_profit = parseFloat(takeProfitPrice);
      }

      // Add trailing stop percentage
      if (trailingStopPercent) {
        orderBody.trailing_stop_percent = parseFloat(trailingStopPercent);
      }

      // Add time in force for limit orders
      if (orderType === "limit" || orderType === "stop-limit") {
        orderBody.time_in_force = timeInForce;
      }

      const response = await apiRequest("/api/trades", {
        method: "POST",
        body: orderBody,
      });

      toast({
        title: "Order Placed",
        description: `${side.toUpperCase()} order placed successfully`,
      });

      // Reset form
      setAmount("");
      setPrice("");
      setPercentage([0]);
    } catch (error) {
      toast({
        title: "Order Failed",
        description: error instanceof Error ? error.message : "Failed to place order",
        variant: "destructive",
      });
    } finally {
      setIsPlacingOrder(false);
      setShowConfirmDialog(false);
      setPendingOrder(null);
    }
  };

  const handleConfirmOrder = async () => {
    if (!pendingOrder) return;
    await executeOrder(pendingOrder.side, pendingOrder.amount, pendingOrder.price, pendingOrder.exchange, pendingOrder.mfaToken);
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs or textareas
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        (e.target as HTMLElement).isContentEditable
      ) {
        return;
      }

      // Buy: B key
      if (e.key === "b" || e.key === "B") {
        e.preventDefault();
        if (!isPlacingOrder) {
          handleOrder("buy");
        }
      }
      // Sell: S key
      if (e.key === "s" || e.key === "S") {
        e.preventDefault();
        if (!isPlacingOrder) {
          handleOrder("sell");
        }
      }
      // Focus amount: A key
      if (e.key === "a" || e.key === "A") {
        e.preventDefault();
        amountInputRef.current?.focus();
      }
      // Focus price: P key
      if (e.key === "p" || e.key === "P") {
        e.preventDefault();
        priceInputRef.current?.focus();
      }
      // Market order: M key
      if (e.key === "m" || e.key === "M") {
        e.preventDefault();
        setOrderType("market");
      }
      // Limit order: L key
      if (e.key === "l" || e.key === "L") {
        e.preventDefault();
        setOrderType("limit");
      }
      // Stop order: T key
      if (e.key === "t" || e.key === "T") {
        e.preventDefault();
        setOrderType("stop");
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, [isPlacingOrder, amount, price, orderType]);

  return (
    <Card className="border-2 border-card-border/70 shadow-2xl bg-gradient-to-br from-card via-card/98 to-card/95" style={{ borderWidth: '3px', borderStyle: 'solid', boxShadow: '0px 20px 40px -10px hsl(220 8% 2% / 0.60), 0px 10px 20px -10px hsl(220 8% 2% / 0.60)' }}>
      <CardHeader className="pb-5 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border-b-2 border-primary/20">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg font-extrabold">Place Order</CardTitle>
            <CardDescription className="text-xs mt-1 font-medium">One-click trading with keyboard shortcuts</CardDescription>
          </div>
          <Badge variant="outline" className="text-xs badge-enhanced border-primary/30 bg-primary/10">
            <Keyboard className="h-3 w-3 mr-1" />
            Shortcuts
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <Tabs value={orderType} onValueChange={(v) => {
          type OrderType = "market" | "limit" | "stop" | "stop-limit" | "take-profit" | "trailing-stop";
          const validTypes: OrderType[] = ["market", "limit", "stop", "stop-limit", "take-profit", "trailing-stop"];
          if (validTypes.includes(v as OrderType)) {
            setOrderType(v as OrderType);
          }
        }}>
          <TabsList className="grid w-full grid-cols-3 bg-muted/50">
            <TabsTrigger value="market" data-testid="button-order-market" className="rounded-md font-medium">Market</TabsTrigger>
            <TabsTrigger value="limit" data-testid="button-order-limit" className="rounded-md font-medium">Limit</TabsTrigger>
            <TabsTrigger value="stop" data-testid="button-order-stop" className="rounded-md font-medium">Stop</TabsTrigger>
          </TabsList>
        </Tabs>
        
        {/* Advanced Order Types */}
        <div className="flex flex-wrap gap-2">
          <Button
            variant={orderType === "stop-limit" ? "default" : "outline"}
            size="sm"
            onClick={() => setOrderType("stop-limit")}
            className="text-xs"
          >
            Stop-Limit
          </Button>
          <Button
            variant={orderType === "take-profit" ? "default" : "outline"}
            size="sm"
            onClick={() => setOrderType("take-profit")}
            className="text-xs"
          >
            Take-Profit
          </Button>
          <Button
            variant={orderType === "trailing-stop" ? "default" : "outline"}
            size="sm"
            onClick={() => setOrderType("trailing-stop")}
            className="text-xs"
          >
            Trailing Stop
          </Button>
        </div>

        {(orderType === "limit" || orderType === "stop-limit" || orderType === "take-profit") && (
          <div className="space-y-2">
            <Label htmlFor="price">Price</Label>
            <Input
              ref={priceInputRef}
              id="price"
              type="number"
              placeholder="0.00"
              value={price}
              onChange={(e) => {
                setPrice(e.target.value);
                // Clear validation error when user types
                if (validationErrors.price) {
                  setValidationErrors(prev => {
                    const next = { ...prev };
                    delete next.price;
                    return next;
                  });
                }
              }}
              className={`font-mono ${validationErrors.price ? 'border-destructive' : ''}`}
              data-testid="input-price"
              aria-label="Order price"
              aria-describedby="price-description"
              aria-invalid={!!validationErrors.price}
            />
            <span id="price-description" className="sr-only">Enter the price at which to execute the order</span>
            <FormFieldError error={validationErrors.price} />
          </div>
        )}

        {(orderType === "stop" || orderType === "stop-limit") && (
          <div className="space-y-2">
            <Label htmlFor="stop-price">Stop Price</Label>
            <Input
              id="stop-price"
              type="number"
              placeholder="0.00"
              value={stopPrice}
              onChange={(e) => {
                setStopPrice(e.target.value);
                if (validationErrors.stop) {
                  setValidationErrors(prev => {
                    const next = { ...prev };
                    delete next.stop;
                    return next;
                  });
                }
              }}
              className={`font-mono ${validationErrors.stop ? 'border-destructive' : ''}`}
              aria-label="Stop price"
              aria-describedby="stop-price-description"
              aria-invalid={!!validationErrors.stop}
            />
            <span id="stop-price-description" className="sr-only">Price level at which the stop order will trigger</span>
            <FormFieldError error={validationErrors.stop} />
            <p className="text-xs text-muted-foreground">
              Order triggers when price reaches this level
            </p>
          </div>
        )}

        {orderType === "take-profit" && (
          <div className="space-y-2">
            <Label htmlFor="take-profit-price">Take Profit Price</Label>
            <Input
              id="take-profit-price"
              type="number"
              placeholder="0.00"
              value={takeProfitPrice}
              onChange={(e) => {
                setTakeProfitPrice(e.target.value);
                if (validationErrors.take_profit) {
                  setValidationErrors(prev => {
                    const next = { ...prev };
                    delete next.take_profit;
                    return next;
                  });
                }
              }}
              className={`font-mono ${validationErrors.take_profit ? 'border-destructive' : ''}`}
              aria-label="Take profit price"
              aria-describedby="take-profit-description"
              aria-invalid={!!validationErrors.take_profit}
            />
            <span id="take-profit-description" className="sr-only">Price target at which to take profit</span>
            <FormFieldError error={validationErrors.take_profit} />
            <p className="text-xs text-muted-foreground">
              Order executes when price reaches this profit target
            </p>
          </div>
        )}

        {orderType === "trailing-stop" && (
          <div className="space-y-2">
            <Label htmlFor="trailing-stop-percent">Trailing Stop %</Label>
            <Input
              id="trailing-stop-percent"
              type="number"
              placeholder="2.5"
              value={trailingStopPercent}
              onChange={(e) => {
                setTrailingStopPercent(e.target.value);
                if (validationErrors.trailing_stop_percent) {
                  setValidationErrors(prev => {
                    const next = { ...prev };
                    delete next.trailing_stop_percent;
                    return next;
                  });
                }
              }}
              className={`font-mono ${validationErrors.trailing_stop_percent ? 'border-destructive' : ''}`}
              aria-label="Trailing stop percentage"
              aria-describedby="trailing-stop-description"
              aria-invalid={!!validationErrors.trailing_stop_percent}
            />
            <span id="trailing-stop-description" className="sr-only">Percentage distance for trailing stop loss</span>
            <FormFieldError error={validationErrors.trailing_stop_percent} />
            <p className="text-xs text-muted-foreground">
              Stop loss follows price by this percentage
            </p>
          </div>
        )}

        {(orderType === "limit" || orderType === "stop-limit") && (
          <div className="space-y-2">
            <Label htmlFor="time-in-force">Time in Force</Label>
            <Select value={timeInForce} onValueChange={(v) => {
              if (v === "GTC" || v === "IOC" || v === "FOK") {
                setTimeInForce(v);
              }
            }}>
              <SelectTrigger 
                id="time-in-force"
                aria-label="Time in force"
                aria-describedby="time-in-force-description"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="GTC">GTC (Good Till Cancel)</SelectItem>
                <SelectItem value="IOC">IOC (Immediate Or Cancel)</SelectItem>
                <SelectItem value="FOK">FOK (Fill Or Kill)</SelectItem>
              </SelectContent>
            </Select>
            <span id="time-in-force-description" className="sr-only">Order execution time constraint</span>
          </div>
        )}

        <div className="space-y-2">
          <Label htmlFor="amount">Amount</Label>
          <Input
            ref={amountInputRef}
            id="amount"
            type="number"
            placeholder="0.00"
            value={amount}
            onChange={(e) => {
              setAmount(e.target.value);
              // Clear validation error when user types
              if (validationErrors.amount) {
                setValidationErrors(prev => {
                  const next = { ...prev };
                  delete next.amount;
                  return next;
                });
              }
            }}
            className={`font-mono ${validationErrors.amount ? 'border-destructive' : ''}`}
            data-testid="input-amount"
            aria-label="Order amount"
            aria-describedby="amount-description"
            aria-invalid={!!validationErrors.amount}
          />
          <span id="amount-description" className="sr-only">Amount of cryptocurrency to trade</span>
          <FormFieldError error={validationErrors.amount} />
        </div>

        {isRealMoney && availableExchanges.length > 0 && (
          <div className="space-y-2">
            <Label htmlFor="exchange">Exchange</Label>
            <Select value={exchange} onValueChange={setExchange}>
              <SelectTrigger 
                id="exchange"
                aria-label="Trading exchange"
                aria-describedby="exchange-description"
              >
                <SelectValue placeholder="Select Exchange" />
              </SelectTrigger>
              <SelectContent>
                {availableExchanges.map((ex) => (
                  <SelectItem key={ex.exchange} value={ex.exchange}>
                    {ex.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <span id="exchange-description" className="sr-only">Select the exchange to execute the trade on</span>
          </div>
        )}

        {isRealMoney && (
          <div className="space-y-2">
            <Label htmlFor="mfa-token" className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              2FA Token (Optional)
            </Label>
            <Input
              id="mfa-token"
              type="text"
              placeholder="Enter 2FA token"
              value={mfaToken}
              onChange={(e) => setMfaToken(e.target.value)}
              className="font-mono"
              aria-label="Two-factor authentication token"
              aria-describedby="mfa-token-description"
            />
            <span id="mfa-token-description" className="sr-only">Optional 2FA token if two-factor authentication is enabled</span>
            <p className="text-xs text-muted-foreground">
              Required if 2FA is enabled on your account
            </p>
          </div>
        )}

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

        {/* Confirmation Dialog for Real Money Trades */}
        <AlertDialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-500" />
                Confirm {isRealMoney ? "Real Money" : "Paper"} Trade
              </AlertDialogTitle>
              <AlertDialogDescription className="space-y-4">
                {isRealMoney && (
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                    <p className="font-semibold text-red-900 dark:text-red-200 mb-2">
                      ⚠️ WARNING: This is a REAL MONEY trade
                    </p>
                    <p className="text-sm text-red-800 dark:text-red-300">
                      This order will be executed using your actual funds on connected exchanges.
                      You could lose money if the trade goes against you.
                    </p>
                  </div>
                )}
                {pendingOrder && (
                  <div className="space-y-2">
                    <p><strong>Side:</strong> {pendingOrder.side.toUpperCase()}</p>
                    <p><strong>Type:</strong> {orderType.toUpperCase()}</p>
                    <p><strong>Amount:</strong> {pendingOrder.amount}</p>
                    {pendingOrder.price && <p><strong>Price:</strong> {pendingOrder.price}</p>}
                    {pendingOrder.exchange && <p><strong>Exchange:</strong> {pendingOrder.exchange.toUpperCase()}</p>}
                    <p><strong>Mode:</strong> {isRealMoney ? "Real Money" : "Paper Trading"}</p>
                  </div>
                )}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleConfirmOrder}
                disabled={isPlacingOrder}
                className={isRealMoney ? "bg-red-500 hover:bg-red-600 text-white" : ""}
              >
                {isPlacingOrder ? "Placing..." : "Confirm Order"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        <div className="grid grid-cols-2 gap-3 pt-2">
          <Button
            className="bg-gradient-to-r from-trading-buy to-trading-buy-hover hover:from-trading-buy-hover hover:to-trading-buy text-white font-bold shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 border-2 border-trading-buy/30"
            onClick={() => handleOrder("buy")}
            disabled={isPlacingOrder}
            data-testid="button-buy"
            aria-label="Place buy order"
            aria-describedby="buy-button-description"
          >
            {isPlacingOrder ? "Placing..." : "Buy"} <span className="ml-2 text-xs opacity-90">(B)</span>
          </Button>
          <span id="buy-button-description" className="sr-only">Place a buy order. Press B key for keyboard shortcut.</span>
          <Button
            className="bg-gradient-to-r from-trading-sell to-trading-sell-hover hover:from-trading-sell-hover hover:to-trading-sell text-white font-bold shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 border-2 border-trading-sell/30"
            onClick={() => handleOrder("sell")}
            disabled={isPlacingOrder}
            data-testid="button-sell"
            aria-label="Place sell order"
            aria-describedby="sell-button-description"
          >
            {isPlacingOrder ? "Placing..." : "Sell"} <span className="ml-2 text-xs opacity-90">(S)</span>
          </Button>
          <span id="sell-button-description" className="sr-only">Place a sell order. Press S key for keyboard shortcut.</span>
        </div>

        {isRealMoney && (
          <div className="pt-2">
            <Badge variant="destructive" className="w-full justify-center">
              <AlertTriangle className="h-3 w-3 mr-1" />
              Real Money Trading Enabled
            </Badge>
          </div>
        )}

        {/* Keyboard Shortcuts Help */}
        <div className="pt-4 border-t space-y-1 text-xs text-muted-foreground">
          <div className="font-semibold mb-2">Keyboard Shortcuts:</div>
          <div className="grid grid-cols-2 gap-1">
            <div>B - Buy</div>
            <div>S - Sell</div>
            <div>A - Focus Amount</div>
            <div>P - Focus Price</div>
            <div>M - Market Order</div>
            <div>L - Limit Order</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
