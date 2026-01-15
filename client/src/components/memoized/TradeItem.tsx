/**
 * Memoized Trade Item Component
 * Optimized trade item rendering to prevent unnecessary re-renders
 */

import { memo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowUpRight, ArrowDownRight, ExternalLink } from 'lucide-react';
import { formatCurrency, formatPercentage, formatDateTime } from '@/lib/formatters';
import { cn } from '@/lib/utils';
import { getChainName } from '@/lib/wagmiConfig';

interface TradeItemProps {
  trade: {
    id: string;
    pair: string;
    side?: string;
    type: string;
    amount: number;
    price: number;
    timestamp: string;
    pnl?: number;
    pnlPercent?: number;
    exchange?: string;
    status?: string;
    mode?: "paper" | "real" | "live";
    chain_id?: number;
  };
  isBuy: boolean;
  tradeSide: string;
}

export const TradeItem = memo(function TradeItem({ trade, isBuy, tradeSide }: TradeItemProps) {
  return (
    <div className="flex items-center justify-between p-3 md:p-4 rounded-none border-b border-border/50 bg-card hover:bg-primary/5 transition-all duration-200 hover:border-primary/30 group">
      <div className="flex items-center gap-4 flex-1 min-w-0">
        {/* Trade Side Indicator */}
        <div className={cn(
          "flex items-center justify-center w-10 h-10 rounded-none border border-transparent",
          isBuy ? "bg-green-500/10 text-green-500 border-green-500/20" : "bg-red-500/10 text-red-500 border-red-500/20"
        )}>
          {isBuy ? (
            <ArrowUpRight className="h-5 w-5" />
          ) : (
            <ArrowDownRight className="h-5 w-5" />
          )}
        </div>

        {/* Trade Details */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="font-bold text-sm font-mono tracking-tight">{trade.pair}</span>
            <Badge variant="outline" className="text-xs rounded-none border-primary/20 font-mono">
              {tradeSide.toUpperCase()}
            </Badge>
            {trade.mode && (
              <Badge 
                variant={trade.mode === "real" || trade.mode === "live" ? "destructive" : "secondary"} 
                className={cn(
                  "text-xs rounded-none font-mono",
                  (trade.mode === "real" || trade.mode === "live") && "bg-red-500/10 text-red-500 border-red-500/20 border"
                )}
              >
                {trade.mode === "real" || trade.mode === "live" ? "REAL MONEY" : "PAPER"}
              </Badge>
            )}
            {trade.chain_id && (
              <Badge variant="outline" className="text-xs rounded-none border-primary/20 font-mono">
                {getChainName(trade.chain_id)}
              </Badge>
            )}
            {trade.exchange && !trade.chain_id && (
              <Badge variant="secondary" className="text-xs rounded-none font-mono">
                {trade.exchange.toUpperCase()}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span>{trade.amount.toFixed(4)} @ {formatCurrency(trade.price)}</span>
            <span>{formatDateTime(trade.timestamp)}</span>
          </div>
        </div>

        {/* P&L */}
        {trade.pnl !== undefined && (
          <div className={cn(
            "text-right",
            trade.pnl >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
          )}>
            <div className="font-semibold">
              {trade.pnl >= 0 ? "+" : ""}{formatCurrency(trade.pnl)}
            </div>
            {trade.pnlPercent !== undefined && (
              <div className="text-xs text-muted-foreground">
                ({formatPercentage(trade.pnlPercent)})
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <Button variant="ghost" size="sm" className="ml-2">
          <ExternalLink className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison function for better memoization
  return (
    prevProps.trade.id === nextProps.trade.id &&
    prevProps.trade.pnl === nextProps.trade.pnl &&
    prevProps.trade.pnlPercent === nextProps.trade.pnlPercent &&
    prevProps.trade.status === nextProps.trade.status &&
    prevProps.isBuy === nextProps.isBuy &&
    prevProps.tradeSide === nextProps.tradeSide
  );
});

