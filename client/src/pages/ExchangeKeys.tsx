/**
 * Exchange API Keys Settings Page - DEPRECATED
 * 
 * This page has been deprecated in favor of blockchain wallet management.
 * Exchange API keys are no longer required - users can trade directly on DEX (blockchain)
 * using custodial or non-custodial wallets.
 * 
 * This page now redirects users to wallet management.
 */

import { useEffect } from 'react';
import { useLocation } from 'wouter';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Wallet, ArrowRight, Info } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export default function ExchangeKeys() {
  const [, setLocation] = useLocation();

  // Auto-redirect to wallet management after 3 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      setLocation('/settings?tab=wallet');
    }, 3000);

    return () => clearTimeout(timer);
  }, [setLocation]);

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            Exchange API Keys
            <Badge variant="destructive" className="ml-2">Deprecated</Badge>
          </h1>
          <p className="text-muted-foreground mt-2">
            This page has been replaced with blockchain wallet management
          </p>
        </div>
      </div>

      <Card className="border-yellow-500 border-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-500" />
            Exchange API Keys No Longer Required
          </CardTitle>
          <CardDescription>
            We've moved to a blockchain-only trading model
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <Info className="h-5 w-5 text-blue-500 mt-0.5 flex-shrink-0" />
              <div className="space-y-2">
                <p className="font-semibold text-blue-900 dark:text-blue-200">
                  🎉 New: DEX Trading Available
                </p>
                <p className="text-sm text-blue-800 dark:text-blue-300">
                  You can now trade directly on decentralized exchanges (DEX) using blockchain wallets.
                  No API keys required! Lower fees, more control, and better privacy.
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="font-semibold">What Changed?</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-1">✓</span>
                <span>
                  <strong>Blockchain Wallets:</strong> Use custodial (platform-managed) or non-custodial (your own) wallets
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-1">✓</span>
                <span>
                  <strong>DEX Trading:</strong> Trade directly on Uniswap, SushiSwap, and other DEXs via aggregators
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-1">✓</span>
                <span>
                  <strong>No API Keys:</strong> No need to connect exchange accounts or manage API credentials
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-1">✓</span>
                <span>
                  <strong>Lower Fees:</strong> Only pay blockchain gas fees + DEX fees (no exchange fees)
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-1">✓</span>
                <span>
                  <strong>Multi-Chain:</strong> Trade on Ethereum, Base, Arbitrum, Polygon, and more
                </span>
              </li>
            </ul>
          </div>

          <div className="pt-4 border-t">
            <h3 className="font-semibold mb-3">Next Steps</h3>
            <div className="space-y-3">
              <Button
                onClick={() => setLocation('/settings?tab=wallet')}
                className="w-full justify-between"
                size="lg"
              >
                <span className="flex items-center gap-2">
                  <Wallet className="h-4 w-4" />
                  Go to Wallet Management
                </span>
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                onClick={() => setLocation('/dex-trading')}
                className="w-full justify-between"
                size="lg"
              >
                <span>Try DEX Trading</span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div className="pt-4 border-t">
            <p className="text-xs text-muted-foreground">
              You will be automatically redirected to wallet management in a few seconds...
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Existing Exchange API Keys</CardTitle>
          <CardDescription>
            If you have existing exchange API keys, they are still stored securely but are no longer used for trading.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Your existing exchange API keys remain encrypted and stored securely. However, they are no longer used
            for trading as we've moved to a blockchain-only model. You can delete them from the Settings page if desired,
            but they will remain in the database for audit purposes.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
