/**
 * DEX Trading Page
 * Main page for decentralized exchange trading
 */
import { DEXTradingPanel } from "@/components/DEXTradingPanel";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Info, TrendingUp, Shield, Zap } from "lucide-react";
import { EnhancedErrorBoundary } from "@/components/EnhancedErrorBoundary";
import logger from "@/lib/logger";

function DEXTradingContent() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold" data-testid="dex-trading-page">DEX Trading</h1>
        <p className="text-muted-foreground mt-1">
          Trade tokens directly on decentralized exchanges via aggregators. No API keys required.
        </p>
      </div>

      {/* Benefits Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Zap className="h-5 w-5 text-primary" />
              Best Prices
            </CardTitle>
          </CardHeader>
          <CardContent>
            <CardDescription>
              Aggregates 500+ DEXs across multiple chains to find the best rates for your trades.
            </CardDescription>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Shield className="h-5 w-5 text-primary" />
              Secure Trading
            </CardTitle>
          </CardHeader>
          <CardContent>
            <CardDescription>
              Choose between custodial (platform-managed) or non-custodial (you control funds) trading.
            </CardDescription>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <TrendingUp className="h-5 w-5 text-primary" />
              Lower Fees
            </CardTitle>
          </CardHeader>
          <CardContent>
            <CardDescription>
              Save money with competitive trading fees (0.15-0.3%) compared to traditional exchanges.
            </CardDescription>
          </CardContent>
        </Card>
      </div>

      {/* Trading Panel */}
      <DEXTradingPanel />

      {/* Info Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="h-5 w-5" />
            How DEX Trading Works
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="font-semibold mb-2">Custodial Trading</h3>
            <p className="text-sm text-muted-foreground">
              Deposit funds to the platform and trade directly. The platform executes trades on your behalf via DEX
              aggregators. You pay a 0.2% trading fee.
            </p>
          </div>
          <div>
            <h3 className="font-semibold mb-2">Non-Custodial Trading</h3>
            <p className="text-sm text-muted-foreground">
              Connect your Web3 wallet (MetaMask, WalletConnect, etc.) and trade directly from your wallet. You
              maintain full control of your funds. You pay a 0.15% trading fee.
            </p>
          </div>
          <div>
            <h3 className="font-semibold mb-2">Supported Chains</h3>
            <p className="text-sm text-muted-foreground">
              Trade on Ethereum, Base, Arbitrum, Polygon, Optimism, Avalanche, BNB Chain, and more. Cross-chain swaps
              are supported via Rubic aggregator.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function DEXTrading() {
  return (
    <EnhancedErrorBoundary
      onError={(error, errorInfo) => {
        logger.error("DEX Trading page error", { error, errorInfo });
      }}
    >
      <DEXTradingContent />
    </EnhancedErrorBoundary>
  );
}
