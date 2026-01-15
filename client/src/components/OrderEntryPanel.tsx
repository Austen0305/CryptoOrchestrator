import { useState, useEffect, useRef, useActionState } from "react";
import React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Keyboard, AlertTriangle, Shield, Wallet } from "lucide-react";
import { useTradingMode } from "@/contexts/TradingModeContext";
import { apiRequest } from "@/lib/queryClient";
import { toast } from "@/components/ui/use-toast";
import { validateOrder, formatValidationErrors } from "@/lib/validation";
import { FormFieldError } from "@/components/FormFieldError";
import { useQuery } from "@tanstack/react-query";
import { CHAIN_IDS, getChainName } from "@/lib/wagmiConfig";
import { usePortfolio } from "@/hooks/useApi";
import type { Portfolio } from "@shared/schema";

interface OrderEntryPanelProps {
  /** Trading pair (e.g., "BTC/USD"). Defaults to "BTC/USD" if not provided. */
  pair?: string;
}

export const OrderEntryPanel = React.memo(function OrderEntryPanel({ pair = "BTC/USD" }: OrderEntryPanelProps) {
  const { mode, isRealMoney, isPaperTrading } = useTradingMode();
  const [orderType, setOrderType] = useState<"market" | "limit" | "stop" | "stop-limit" | "take-profit" | "trailing-stop">("market");
  const [stopPrice, setStopPrice] = useState("");
  const [takeProfitPrice, setTakeProfitPrice] = useState("");
  const [trailingStopPercent, setTrailingStopPercent] = useState("");
  const [timeInForce, setTimeInForce] = useState<"GTC" | "IOC" | "FOK">("GTC");
  const [amount, setAmount] = useState("");
  const [price, setPrice] = useState("");
  const [percentage, setPercentage] = useState([0]);
  const [chainId, setChainId] = useState<number>(CHAIN_IDS.ETHEREUM);
  const [mfaToken, setMfaToken] = useState<string>("");
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [pendingOrder, setPendingOrder] = useState<{ side: "buy" | "sell"; amount: string; price: string; chainId?: number; mfaToken?: string } | null>(null);
  
  // Get portfolio balance for validation
  const { data: portfolio } = usePortfolio(mode) as { data: Portfolio | undefined };
  // React 19 Action State
  type OrderState = { success?: boolean; error?: string; timestamp?: number };
  
  const placeOrderAction = async (_prev: OrderState, formData: FormData): Promise<OrderState> => {
    const side = formData.get("side") as "buy" | "sell";
    const amountStr = formData.get("amount") as string;
    const priceStr = formData.get("price") as string;
    const mfaToken = formData.get("mfa_token") as string;
    const chainId = formData.get("chain_id") ? parseInt(formData.get("chain_id") as string) : undefined;
    
    try {
       const orderBody: any = {
        pair,
        side,
        type: orderType,
        amount: parseFloat(amountStr),
        mode,
        chain_id: chainId,
        mfa_token: mfaToken || undefined
      };
      
      if (priceStr) orderBody.price = parseFloat(priceStr);
      if (stopPrice) orderBody.stop = parseFloat(stopPrice);
      if (takeProfitPrice) orderBody.take_profit = parseFloat(takeProfitPrice);
      if (trailingStopPercent) orderBody.trailing_stop_percent = parseFloat(trailingStopPercent);
      if ((orderType === "limit" || orderType === "stop-limit") && timeInForce) {
        orderBody.time_in_force = timeInForce;
      }

      await apiRequest("/api/trades", { method: "POST", body: orderBody });
      return { success: true, timestamp: Date.now() };
    } catch (error) {
       return { success: false, error: error instanceof Error ? error.message : "Order failed" };
    }
  };

  const [formState, submitOrder, isPending] = useActionState(placeOrderAction, {});

  // Response Effect
  useEffect(() => {
    if (formState.success) {
      toast({ title: "Order Placed", description: "Order executed successfully" });
      setAmount("");
      setPrice("");
      setPercentage([0]);
      setShowConfirmDialog(false);
      setPendingOrder(null);
    } else if (formState.error) {
      toast({ title: "Order Failed", description: formState.error, variant: "destructive" });
      setShowConfirmDialog(false);
    }
  }, [formState]);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const amountInputRef = useRef<HTMLInputElement>(null);
  const priceInputRef = useRef<HTMLInputElement>(null);

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

    // If real money, validate wallet/chain is configured
    if (isRealMoney) {
      // Check if user has wallet configured (portfolio exists with balances)
      if (!portfolio || (portfolio.totalBalance === 0 && Object.keys(portfolio.positions || {}).length === 0)) {
        toast({
          title: "Wallet Required",
          description: "Please set up a wallet for real money trading. Go to Settings > Wallets to create one.",
          variant: "destructive",
        });
        return;
      }
      
      // Check balance if available
      if (portfolio && side === "buy") {
        const tradeValue = parseFloat(amount) * (price ? parseFloat(price) : 0);
        const availableBalance = portfolio.availableBalance || portfolio.totalBalance || 0;
        if (tradeValue > availableBalance) {
          toast({
            title: "Insufficient Balance",
            description: `Available: $${availableBalance.toLocaleString()}, Required: $${tradeValue.toLocaleString()}`,
            variant: "destructive",
          });
          return;
        }
      }
    }

    // If real money, show confirmation dialog
    if (isRealMoney) {
      setPendingOrder({ side, amount, price, chainId, mfaToken });
      setShowConfirmDialog(true);
      return;
    }

    // Paper trading - execute immediately
    // Paper trading - execute via Action
    const formData = new FormData();
    formData.append("side", side);
    formData.append("amount", amount);
    if (price) formData.append("price", price);
    
    React.startTransition(() => {
      submitOrder(formData);
    });
  };



  const handleConfirmOrder = async () => {
    if (!pendingOrder) return;
    const formData = new FormData();
    formData.append("side", pendingOrder.side);
    formData.append("amount", pendingOrder.amount);
    if (pendingOrder.price) formData.append("price", pendingOrder.price);
    if (pendingOrder.chainId) formData.append("chain_id", pendingOrder.chainId.toString());
    if (pendingOrder.mfaToken) formData.append("mfa_token", pendingOrder.mfaToken);
    
    React.startTransition(() => {
      submitOrder(formData);
    });
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
        if (!isPending) {
          handleOrder("buy");
        }
      }
      // Sell: S key
      if (e.key === "s" || e.key === "S") {
        e.preventDefault();
        if (!isPending) {
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
  }, [isPending, amount, price, orderType]);

  return (
    <Card className="glass-premium border-border/50 shadow-2xl overflow-hidden hover-lift transition-all duration-300">
      <CardHeader className="pb-5 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border-b border-primary/10">
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
            name="price"
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
            name="amount"
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

        {isRealMoney && (
          <div className="space-y-2">
            <Label htmlFor="chain-id" className="flex items-center gap-2">
              <Wallet className="h-4 w-4" />
              Blockchain Network
            </Label>
            <Select value={String(chainId)} onValueChange={(v) => setChainId(Number(v))}>
              <SelectTrigger 
                id="chain-id"
                aria-label="Blockchain network"
                aria-describedby="chain-description"
              >
                <SelectValue placeholder="Select Network" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={String(CHAIN_IDS.ETHEREUM)}>Ethereum</SelectItem>
                <SelectItem value={String(CHAIN_IDS.BASE)}>Base</SelectItem>
                <SelectItem value={String(CHAIN_IDS.ARBITRUM)}>Arbitrum One</SelectItem>
                <SelectItem value={String(CHAIN_IDS.POLYGON)}>Polygon</SelectItem>
                <SelectItem value={String(CHAIN_IDS.OPTIMISM)}>Optimism</SelectItem>
                <SelectItem value={String(CHAIN_IDS.AVALANCHE)}>Avalanche</SelectItem>
                <SelectItem value={String(CHAIN_IDS.BSC)}>BNB Chain</SelectItem>
              </SelectContent>
            </Select>
            <span id="chain-description" className="sr-only">Select the blockchain network for DEX trading</span>
            <p className="text-xs text-muted-foreground">
              DEX trading uses {getChainName(chainId)} network. No API keys required - trades execute directly on blockchain.
            </p>
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
          {portfolio && (
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Available Balance:</span>
              <span className="font-mono font-semibold">
                ${(portfolio.availableBalance || portfolio.totalBalance || 0).toLocaleString()}
              </span>
            </div>
          )}
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Order Total:</span>
            <span className="font-mono font-semibold">
              ${amount ? (parseFloat(amount) * (price ? parseFloat(price) : 47350)).toLocaleString() : "0.00"}
            </span>
          </div>
          {portfolio && amount && (
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>After Trade:</span>
              <span className="font-mono">
                ${((portfolio.availableBalance || portfolio.totalBalance || 0) - (parseFloat(amount) * (price ? parseFloat(price) : 47350))).toLocaleString()}
              </span>
            </div>
          )}
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
                      This order will be executed using your actual funds via DEX (blockchain) trading.
                      You could lose money if the trade goes against you.
                    </p>
                  </div>
                )}
                {pendingOrder && (
                  <div className="space-y-2 bg-muted/50 rounded-lg p-4">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-muted-foreground">Side:</span>
                        <span className="ml-2 font-semibold">{pendingOrder.side.toUpperCase()}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Type:</span>
                        <span className="ml-2 font-semibold">{orderType.toUpperCase()}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Pair:</span>
                        <span className="ml-2 font-semibold">{pair}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Amount:</span>
                        <span className="ml-2 font-semibold">{pendingOrder.amount}</span>
                      </div>
                      {pendingOrder.price && (
                        <div>
                          <span className="text-muted-foreground">Price:</span>
                          <span className="ml-2 font-semibold">${parseFloat(pendingOrder.price).toLocaleString()}</span>
                        </div>
                      )}
                      <div>
                        <span className="text-muted-foreground">Total:</span>
                        <span className="ml-2 font-semibold">
                          ${(parseFloat(pendingOrder.amount) * (pendingOrder.price ? parseFloat(pendingOrder.price) : 0)).toLocaleString()}
                        </span>
                      </div>
                      {pendingOrder.chainId && (
                        <div>
                          <span className="text-muted-foreground">Network:</span>
                          <span className="ml-2 font-semibold">{getChainName(pendingOrder.chainId)}</span>
                        </div>
                      )}
                      <div>
                        <span className="text-muted-foreground">Mode:</span>
                        <span className="ml-2 font-semibold">{isRealMoney ? "Real Money" : "Paper Trading"}</span>
                      </div>
                    </div>
                    {portfolio && pendingOrder.side === "buy" && (
                      <div className="mt-3 pt-3 border-t">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Available Balance:</span>
                          <span className="font-semibold">${(portfolio.availableBalance || portfolio.totalBalance || 0).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between text-sm mt-1">
                          <span className="text-muted-foreground">After Trade:</span>
                          <span className="font-semibold">
                            ${((portfolio.availableBalance || portfolio.totalBalance || 0) - (parseFloat(pendingOrder.amount) * (pendingOrder.price ? parseFloat(pendingOrder.price) : 0))).toLocaleString()}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleConfirmOrder}
                disabled={isPending}
                className={isRealMoney ? "bg-red-500 hover:bg-red-600 text-white" : ""}
              >
                {isPending ? "Placing..." : "Confirm Order"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        <div className="grid grid-cols-2 gap-3 pt-2">
          <Button
            className="bg-gradient-to-r from-trading-buy to-trading-buy-hover hover:from-trading-buy-hover hover:to-trading-buy text-white font-bold shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 border-2 border-trading-buy/30"
            onClick={() => handleOrder("buy")}
            disabled={isPending}
            data-testid="button-buy"
            aria-label="Place buy order"
            aria-describedby="buy-button-description"
          >
            {isPending ? "Placing..." : "Buy"} <span className="ml-2 text-xs opacity-90">(B)</span>
          </Button>
          <span id="buy-button-description" className="sr-only">Place a buy order. Press B key for keyboard shortcut.</span>
          <Button
            className="bg-gradient-to-r from-trading-sell to-trading-sell-hover hover:from-trading-sell-hover hover:to-trading-sell text-white font-bold shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 border-2 border-trading-sell/30"
            onClick={() => handleOrder("sell")}
            disabled={isPending}
            data-testid="button-sell"
            aria-label="Place sell order"
            aria-describedby="sell-button-description"
          >
            {isPending ? "Placing..." : "Sell"} <span className="ml-2 text-xs opacity-90">(S)</span>
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
});
