/**
 * Empty State Component
 * Provides consistent, helpful empty states throughout the application
 */

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LucideIcon, Inbox, Plus, Search, RefreshCw, TrendingUp, Bot, Code } from "lucide-react";
import { cn } from "@/lib/utils";
import { AnimatedContainer } from "@/components/PageTransition";

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  action?: {
    label: string;
    onClick: () => void;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
  illustration?: React.ReactNode;
}

export const EmptyState = React.memo(function EmptyState({
  title,
  description,
  icon: Icon = Inbox,
  action,
  secondaryAction,
  className,
  illustration,
}: EmptyStateProps) {
  return (
    <AnimatedContainer animation="fade-in-up" delay={100}>
      <Card className={cn("border-dashed", className)}>
        <CardContent className="flex flex-col items-center justify-center py-12 px-6 text-center">
          {illustration ? (
            illustration
          ) : (
            <div className="mb-4 p-4 rounded-full bg-muted/50 animate-float">
              <Icon className="h-8 w-8 text-muted-foreground" />
            </div>
          )}
          <h3 className="text-lg font-semibold mb-2">{title}</h3>
          <p className="text-sm text-muted-foreground mb-6 max-w-sm">{description}</p>
          <div className="flex gap-2">
            {action && (
              <Button onClick={action.onClick} size="sm" className="animate-scale-in">
                {action.label === "Create" && <Plus className="h-4 w-4 mr-2" />}
                {action.label === "Search" && <Search className="h-4 w-4 mr-2" />}
                {action.label === "Refresh" && <RefreshCw className="h-4 w-4 mr-2" />}
                {action.label}
              </Button>
            )}
            {secondaryAction && (
              <Button onClick={secondaryAction.onClick} variant="outline" size="sm" className="animate-scale-in">
                {secondaryAction.label}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </AnimatedContainer>
  );
});

/**
 * Pre-configured empty states for common scenarios
 */
export function EmptyBotsState({ onCreateBot }: { onCreateBot?: () => void }) {
  return (
    <EmptyState
      icon={Bot}
      title="No trading bots"
      description="Create your first trading bot to start automated trading."
      action={
        onCreateBot ? {
          label: "Create Bot",
          onClick: onCreateBot
        } : undefined
      }
    />
  );
}

export function EmptyStrategiesState({ onCreateStrategy }: { onCreateStrategy?: () => void }) {
  return (
    <EmptyState
      icon={Code}
      title="No strategies"
      description="Create or import a trading strategy to get started."
      action={
        onCreateStrategy ? {
          label: "Create Strategy",
          onClick: onCreateStrategy
        } : undefined
      }
    />
  );
}

export function EmptyTradesState({ onRefresh }: { onRefresh?: () => void }) {
  return (
    <EmptyState
      icon={TrendingUp}
      title="No trades found"
      description="You haven't made any trades yet. Start trading to see your trade history here."
      action={onRefresh ? { label: "Refresh", onClick: onRefresh } : undefined}
    />
  );
}

export function EmptyPortfolioState() {
  return (
    <EmptyState
      title="No portfolio data"
      description="Create a wallet or start paper trading to see your portfolio. Trade directly on blockchain via DEX aggregators."
      action={{ label: "Create Wallet", onClick: () => {} }}
    />
  );
}

export function EmptySearchResults({ query, onClear }: { query: string; onClear: () => void }) {
  return (
    <EmptyState
      title="No results found"
      description={`No results found for "${query}". Try adjusting your search terms.`}
      action={{ label: "Clear Search", onClick: onClear }}
      icon={Search}
    />
  );
}

