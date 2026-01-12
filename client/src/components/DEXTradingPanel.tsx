/**
 * DEX Trading Panel Component
 * UI for executing DEX swaps via aggregators
 * Supports both custodial and non-custodial trading
 */
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ArrowUpDown, Wallet, TrendingUp, Info, RefreshCw, ArrowLeftRight, Loader2, AlertTriangle, CheckCircle2 } from "lucide-react";
import { useDEXQuote, useDEXSwap, useSupportedChains } from "@/hooks/useDEXTrading";
import { useWeb3Wallet } from "@/hooks/useWeb3Wallet";
import { WalletConnect } from "@/components/WalletConnect";
import { useToast } from "@/hooks/use-toast";
import { CHAIN_IDS, getChainName } from "@/lib/wagmiConfig";
import logger from "@/lib/logger";
import { SwapConfirmation } from "@/components/SwapConfirmation";
import { TransactionStatus } from "@/components/TransactionStatus";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { ErrorBoundary } from "@/components/ErrorBoundary";

// Common token addresses (can be extended)
const COMMON_TOKENS: Record<number, Array<{ address: string; symbol: string; name: string }>> = {
  [CHAIN_IDS.ETHEREUM]: [
    { address: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", symbol: "WETH", name: "Wrapped Ethereum" },
    { address: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", symbol: "USDC", name: "USD Coin" },
    { address: "0xdAC17F958D2ee523a2206206994597C13D831ec7", symbol: "USDT", name: "Tether USD" },
    { address: "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", symbol: "WBTC", name: "Wrapped Bitcoin" },
  ],
  [CHAIN_IDS.BASE]: [
    { address: "0x4200000000000000000000000000000000000006", symbol: "WETH", name: "Wrapped Ethereum" },
    { address: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", symbol: "USDC", name: "USD Coin" },
  ],
  [CHAIN_IDS.ARBITRUM]: [
    { address: "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1", symbol: "WETH", name: "Wrapped Ethereum" },
    { address: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831", symbol: "USDC", name: "USD Coin" },
  ],
};

function DEXTradingPanelContent() {
  const [sellToken, setSellToken] = useState("");
  const [buyToken, setBuyToken] = useState("");
  const [sellAmount, setSellAmount] = useState("");
  const [chainId, setChainId] = useState<number>(CHAIN_IDS.ETHEREUM);
  const [slippage, setSlippage] = useState("0.5");
  const [deadline, setDeadline] = useState("20"); // minutes
  const [tradingMode, setTradingMode] = useState<"custodial" | "non-custodial">("custodial");
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [transactionHash, setTransactionHash] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const { toast } = useToast();
  const { address, isConnected } = useWeb3Wallet();
  const { data: supportedChains } = useSupportedChains();
  const quoteMutation = useDEXQuote();
  const swapMutation = useDEXSwap();

  const [quote, setQuote] = useState<any>(null);
  const [availableTokens, setAvailableTokens] = useState(COMMON_TOKENS[chainId] || []);
  
  // Get token balances for display
  const sellTokenData = availableTokens.find((t) => t.address === sellToken);
  const buyTokenData = availableTokens.find((t) => t.address === buyToken);

  // Update available tokens when chain changes
  useEffect(() => {
    setAvailableTokens(COMMON_TOKENS[chainId] || []);
    // Reset token selections when chain changes
    setSellToken("");
    setBuyToken("");
  }, [chainId]);

  // Get quote when inputs change
  useEffect(() => {
    if (sellToken && buyToken && sellAmount && parseFloat(sellAmount) > 0) {
      const timeoutId = setTimeout(() => {
        handleGetQuote();
      }, 500); // Debounce quote requests

      return () => clearTimeout(timeoutId);
    } else {
      setQuote(null);
      return undefined;
    }
  }, [sellToken, buyToken, sellAmount, chainId, slippage]);

  const handleSwapDirection = () => {
    const tempToken = sellToken;
    const tempAmount = sellAmount;
    setSellToken(buyToken);
    setBuyToken(tempToken);
    if (quote && quote.buy_amount) {
      setSellAmount(typeof quote.buy_amount === "string" ? quote.buy_amount : String(quote.buy_amount));
    }
    setQuote(null);
  };

  const handleGetQuote = async () => {
    if (!sellToken || !buyToken || !sellAmount || parseFloat(sellAmount) <= 0) {
      return;
    }

    try {
      const result = await quoteMutation.mutateAsync({
        sell_token: sellToken,
        buy_token: buyToken,
        sell_amount: sellAmount,
        chain_id: chainId,
        slippage_percentage: parseFloat(slippage),
      });

      setQuote(result);
    } catch (error) {
      // Error handled by hook
      setQuote(null);
    }
  };

  const handleSwap = async () => {
    if (!sellToken || !buyToken || !sellAmount || parseFloat(sellAmount) <= 0) {
      toast({
        title: "Invalid Input",
        description: "Please fill in all required fields",
        variant: "destructive",
      });
      return;
    }

    if (tradingMode === "non-custodial" && !isConnected) {
      toast({
        title: "Wallet Not Connected",
        description: "Please connect your wallet for non-custodial trading",
        variant: "destructive",
      });
      return;
    }

    try {
      const idempotencyKey = `swap_${Date.now()}_${Math.random().toString(36).substring(7)}`;

      await swapMutation.mutateAsync({
        sell_token: sellToken,
        buy_token: buyToken,
        sell_amount: sellAmount,
        chain_id: chainId,
        slippage_percentage: parseFloat(slippage),
        custodial: tradingMode === "custodial",
        user_wallet_address: tradingMode === "non-custodial" ? address : undefined,
        idempotency_key: idempotencyKey,
      });
    } catch (error) {
      // Error handled by hook
    }
  };

  const formatPrice = (price: number | undefined) => {
    if (!price) return "N/A";
    return new Intl.NumberFormat("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 6,
    }).format(price);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            DEX Trading
          </CardTitle>
          <CardDescription>
            Trade tokens directly on decentralized exchanges via aggregators
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Trading Mode Selection */}
          <Tabs value={tradingMode} onValueChange={(v) => setTradingMode(v as "custodial" | "non-custodial")}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="custodial">
                <Wallet className="h-4 w-4 mr-2" />
                Custodial
              </TabsTrigger>
              <TabsTrigger value="non-custodial">
                <Wallet className="h-4 w-4 mr-2" />
                Non-Custodial
              </TabsTrigger>
            </TabsList>

            <TabsContent value="non-custodial" className="mt-4">
              {!isConnected && (
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertDescription>
                    Connect your wallet to trade non-custodially (you maintain full control of funds)
                  </AlertDescription>
                </Alert>
              )}
              {isConnected && (
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertDescription>
                    Wallet connected: {address?.slice(0, 6)}...{address?.slice(-4)}
                  </AlertDescription>
                </Alert>
              )}
            </TabsContent>
          </Tabs>

          {/* Chain Selection */}
          <div className="space-y-2">
            <Label htmlFor="chain" className="flex items-center gap-2">
              <Wallet className="h-4 w-4" />
              Blockchain Network
            </Label>
            <Select value={String(chainId)} onValueChange={(v) => setChainId(Number(v))}>
              <SelectTrigger id="chain" className="w-full">
                <SelectValue placeholder="Select chain" />
              </SelectTrigger>
              <SelectContent>
                {supportedChains?.map((chain) => (
                  <SelectItem key={chain.chain_id} value={String(chain.chain_id)}>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-3 w-3 text-green-500" />
                      {chain.name} ({chain.symbol})
                    </div>
                  </SelectItem>
                )) || (
                  <SelectItem value={String(CHAIN_IDS.ETHEREUM)}>Ethereum</SelectItem>
                )}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Selected: {getChainName(chainId)} - No API keys required for DEX trading
            </p>
          </div>

          {/* Token Selection with Swap Direction Toggle */}
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="sell-token">Sell Token</Label>
                  {sellTokenData && (
                    <span className="text-xs text-muted-foreground">
                      Balance: {sellTokenData.symbol}
                    </span>
                  )}
                </div>
                <Select value={sellToken} onValueChange={setSellToken}>
                  <SelectTrigger id="sell-token">
                    <SelectValue placeholder="Select token" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableTokens.map((token) => (
                      <SelectItem key={token.address} value={token.address}>
                        {token.symbol} - {token.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-end justify-center pb-2">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleSwapDirection}
                  title="Swap direction"
                  aria-label="Swap buy and sell tokens"
                >
                  <ArrowLeftRight className="h-4 w-4" />
                </Button>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="buy-token">Buy Token</Label>
                  {buyTokenData && (
                    <span className="text-xs text-muted-foreground">
                      Balance: {buyTokenData.symbol}
                    </span>
                  )}
                </div>
                <Select value={buyToken} onValueChange={setBuyToken}>
                  <SelectTrigger id="buy-token">
                    <SelectValue placeholder="Select token" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableTokens
                      .filter((token) => token.address !== sellToken)
                      .map((token) => (
                        <SelectItem key={token.address} value={token.address}>
                          {token.symbol} - {token.name}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Amount Input */}
          <div className="space-y-2">
            <Label htmlFor="amount">Amount to Sell</Label>
            <Input
              id="amount"
              type="number"
              placeholder="0.0"
              value={sellAmount}
              onChange={(e) => setSellAmount(e.target.value)}
              min="0"
              step="any"
            />
          </div>

          {/* Slippage Tolerance */}
          <div className="space-y-2">
            <Label htmlFor="slippage" className="flex items-center gap-2">
              Slippage Tolerance (%)
              {parseFloat(slippage) > 1.0 && (
                <AlertTriangle className="h-4 w-4 text-yellow-500" />
              )}
            </Label>
            <Input
              id="slippage"
              type="number"
              placeholder="0.5"
              value={slippage}
              onChange={(e) => setSlippage(e.target.value)}
              min="0"
              max="50"
              step="0.1"
            />
            {parseFloat(slippage) > 1.0 && (
              <div className="flex items-start gap-2 p-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md">
                <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-400 mt-0.5 flex-shrink-0" />
                <div className="text-xs text-yellow-800 dark:text-yellow-200">
                  <p className="font-semibold">High Slippage Warning</p>
                  <p>Slippage above 1% may result in unfavorable execution prices. Consider reducing slippage tolerance for better price protection.</p>
                </div>
              </div>
            )}
          </div>

          {/* Quote Display with Refresh */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Quote</Label>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleGetQuote}
                disabled={quoteMutation.isPending || !sellToken || !buyToken || !sellAmount}
                aria-label="Refresh quote"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${quoteMutation.isPending ? "animate-spin" : ""}`} />
                Refresh
              </Button>
            </div>
            
            {quoteMutation.isPending && (
              <div className="p-4 bg-muted/50 rounded-lg text-center">
                <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">Getting best quote...</p>
              </div>
            )}
            
            {quote && !quoteMutation.isPending && (
              <Card className="bg-muted/50">
                <CardContent className="pt-6">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Best Aggregator</span>
                      <Badge variant="outline">{quote.aggregator?.toUpperCase() || "N/A"}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">You Sell</span>
                      <span className="font-medium">
                        {parseFloat(sellAmount).toFixed(6)} {sellTokenData?.symbol || "TOKEN"}
                      </span>
                    </div>
                    <div className="flex items-center justify-center">
                      <ArrowUpDown className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">You Receive</span>
                      <span className="font-medium">
                        {quote.buy_amount
                          ? typeof quote.buy_amount === "string"
                            ? formatPrice(parseFloat(quote.buy_amount))
                            : formatPrice(quote.buy_amount)
                          : "Calculating..."} {buyTokenData?.symbol || "TOKEN"}
                      </span>
                    </div>
                    {quote.price && (
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Price</span>
                        <span className="font-medium">{formatPrice(quote.price)}</span>
                      </div>
                    )}
                    {quote.estimated_gas && (
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Estimated Gas</span>
                        <span className="font-medium">{quote.estimated_gas}</span>
                      </div>
                    )}
                    {quote.price_impact && (
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Price Impact</span>
                        <span className={`font-medium ${
                          quote.price_impact > 5 ? "text-red-500" :
                          quote.price_impact > 2 ? "text-yellow-500" :
                          "text-green-500"
                        }`}>
                          {quote.price_impact.toFixed(2)}%
                        </span>
                      </div>
                    )}
                    {quote.route && (
                      <div className="pt-2 border-t">
                        <div className="text-xs text-muted-foreground mb-1">Route</div>
                        <div className="text-xs font-mono">
                          {quote.route.length > 0
                            ? quote.route.join(" → ")
                            : "Direct swap"}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Swap Button */}
          <Button
            onClick={handleSwap}
            disabled={
              !sellToken ||
              !buyToken ||
              !sellAmount ||
              parseFloat(sellAmount) <= 0 ||
              swapMutation.isPending ||
              (tradingMode === "non-custodial" && !isConnected)
            }
            className="w-full"
            size="lg"
            aria-label="Execute swap"
          >
            {swapMutation.isPending ? "Processing..." : "Execute Swap"}
          </Button>

          {tradingMode === "non-custodial" && !isConnected && (
            <div className="mt-4">
              <WalletConnect />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export function DEXTradingPanel() {
  return (
    <ErrorBoundary
      fallback={
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Error loading DEX trading panel. Please refresh the page.</p>
          </CardContent>
        </Card>
      }
      onError={(error, errorInfo) => {
        logger.error("DEXTradingPanel error", { error, errorInfo });
      }}
    >
      <DEXTradingPanelContent />
    </ErrorBoundary>
  );
}
