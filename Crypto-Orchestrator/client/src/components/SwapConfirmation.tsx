/**
 * Swap Confirmation Component
 * Shows swap details before execution with price impact and fees
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info, TrendingUp, TrendingDown, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface SwapConfirmationProps {
  sellToken: string;
  sellTokenSymbol: string;
  buyToken: string;
  buyTokenSymbol: string;
  sellAmount: string;
  buyAmount: string;
  priceImpact?: number;
  fees?: {
    platform: number;
    aggregator: number;
    total: number;
  };
  aggregator?: string;
  slippage: number;
  onConfirm: () => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function SwapConfirmation({
  sellToken,
  sellTokenSymbol,
  buyToken,
  buyTokenSymbol,
  sellAmount,
  buyAmount,
  priceImpact = 0,
  fees,
  aggregator,
  slippage,
  onConfirm,
  onCancel,
  isLoading = false,
}: SwapConfirmationProps) {
  const priceImpactColor =
    priceImpact > 5
      ? "text-red-500"
      : priceImpact > 2
      ? "text-yellow-500"
      : "text-green-500";

  const priceImpactSeverity =
    priceImpact > 5
      ? "high"
      : priceImpact > 2
      ? "medium"
      : "low";

  return (
    <Card>
      <CardHeader>
        <CardTitle>Confirm Swap</CardTitle>
        <CardDescription>Review swap details before confirming</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Swap Summary */}
        <div className="space-y-3 p-4 bg-muted/50 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">You Sell</span>
            <span className="font-semibold">
              {parseFloat(sellAmount).toFixed(6)} {sellTokenSymbol}
            </span>
          </div>
          <div className="flex items-center justify-center">
            <div className="h-px w-full bg-border" />
            <div className="px-2 text-muted-foreground">↓</div>
            <div className="h-px w-full bg-border" />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">You Receive</span>
            <span className="font-semibold">
              {parseFloat(buyAmount).toFixed(6)} {buyTokenSymbol}
            </span>
          </div>
        </div>

        {/* Price Impact */}
        {priceImpact > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Price Impact</span>
              <span className={`font-medium ${priceImpactColor}`}>
                {priceImpact > 0 ? "+" : ""}
                {priceImpact.toFixed(2)}%
              </span>
            </div>
            {priceImpactSeverity === "high" && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  High price impact detected. Consider splitting this trade into smaller amounts.
                </AlertDescription>
              </Alert>
            )}
            {priceImpactSeverity === "medium" && (
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  Moderate price impact. The final amount may differ from the estimate.
                </AlertDescription>
              </Alert>
            )}
          </div>
        )}

        {/* Fees Breakdown */}
        {fees && (
          <div className="space-y-2 p-4 bg-muted/50 rounded-lg">
            <div className="text-sm font-semibold mb-2">Fees</div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Platform Fee</span>
              <span>{fees.platform.toFixed(6)} {sellTokenSymbol}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Aggregator Fee</span>
              <span>{fees.aggregator.toFixed(6)} {sellTokenSymbol}</span>
            </div>
            <div className="flex items-center justify-between pt-2 border-t">
              <span className="font-semibold">Total Fee</span>
              <span className="font-semibold">{fees.total.toFixed(6)} {sellTokenSymbol}</span>
            </div>
          </div>
        )}

        {/* Aggregator Info */}
        {aggregator && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Best Route Via</span>
            <Badge variant="outline">{aggregator.toUpperCase()}</Badge>
          </div>
        )}

        {/* Slippage Tolerance */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Max Slippage</span>
          <span>{slippage}%</span>
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-4">
          <Button variant="outline" onClick={onCancel} className="flex-1" disabled={isLoading}>
            Cancel
          </Button>
          <Button onClick={onConfirm} className="flex-1" disabled={isLoading}>
            {isLoading ? "Confirming..." : "Confirm Swap"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
