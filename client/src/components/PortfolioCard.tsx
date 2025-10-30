import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown, LucideIcon } from "lucide-react";

interface PortfolioCardProps {
  title: string;
  value: string;
  change?: number;
  icon: LucideIcon;
  subtitle?: string;
}

export function PortfolioCard({ title, value, change, icon: Icon, subtitle }: PortfolioCardProps) {
  const isPositive = change !== undefined && change >= 0;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          <div className="text-3xl font-mono font-bold" data-testid={`text-${title.toLowerCase().replace(/\s/g, '-')}`}>
            {value}
          </div>
          {change !== undefined && (
            <div className="flex items-center gap-1 text-sm">
              {isPositive ? (
                <TrendingUp className="w-4 h-4 text-trading-profit" />
              ) : (
                <TrendingDown className="w-4 h-4 text-trading-loss" />
              )}
              <span className={isPositive ? "text-trading-profit" : "text-trading-loss"}>
                {isPositive ? "+" : ""}{change.toFixed(2)}%
              </span>
              <span className="text-muted-foreground">{subtitle || "24h"}</span>
            </div>
          )}
          {subtitle && change === undefined && (
            <p className="text-sm text-muted-foreground">{subtitle}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
