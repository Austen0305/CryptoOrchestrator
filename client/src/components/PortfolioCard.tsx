import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown, LucideIcon } from "lucide-react";
import React from "react";

interface PortfolioCardProps {
  title: string;
  value: string;
  change?: number;
  icon: LucideIcon;
  subtitle?: string;
  className?: string;
}

export const PortfolioCard = React.memo(function PortfolioCard({ title, value, change, icon: Icon, subtitle, className }: PortfolioCardProps) {
  const isPositive = change !== undefined && change >= 0;

  return (
    <Card 
      className={`group relative overflow-hidden border-border/50 glass-premium hover-lift ${className}`} 
      role="region"
      aria-label={`${title} portfolio card`}
    >
      <CardHeader 
        className="flex flex-row items-center justify-between space-y-0 pb-5 border-b border-primary/10 bg-gradient-to-r from-primary/5 to-transparent"
      >
        <CardTitle className="text-xs md:text-sm font-extrabold text-muted-foreground uppercase tracking-widest">
          {title}
        </CardTitle>
        <div 
          className="p-3.5 rounded-2xl bg-gradient-to-br from-primary/25 to-primary/15 group-hover:from-primary/35 group-hover:to-primary/25 transition-all duration-300 group-hover:scale-110 group-hover:rotate-6 shadow-glow border border-primary/30 group-hover:border-primary/50"
        >
          <Icon className="h-5 w-5 md:h-6 md:w-6 text-primary drop-shadow-glow" />
        </div>
      </CardHeader>
      <CardContent className="space-y-4 pt-6">
        <div 
          className="text-3xl md:text-4xl lg:text-5xl font-mono font-black text-foreground" 
          data-testid={`text-${title.toLowerCase().replace(/\s/g, '-')}`}
          aria-label={`${title} value: ${value}`}
        >
          {value}
        </div>
        {change !== undefined && (
          <div className="flex items-center gap-2 text-sm">
            <div className={`p-1.5 rounded-lg ${isPositive ? 'bg-trading-profit/20 border border-trading-profit/30' : 'bg-trading-loss/20 border border-trading-loss/30'}`}>
              {isPositive ? (
                <TrendingUp className="w-4 h-4 text-trading-profit" />
              ) : (
                <TrendingDown className="w-4 h-4 text-trading-loss" />
              )}
            </div>
            <span className={`font-bold text-base ${isPositive ? "text-trading-profit" : "text-trading-loss"}`}>
              {isPositive ? "+" : ""}{change.toFixed(2)}%
            </span>
            <span className="text-muted-foreground text-xs font-medium">{subtitle || "24h"}</span>
          </div>
        )}
        {subtitle && change === undefined && (
          <p className="text-xs md:text-sm text-muted-foreground font-medium">{subtitle}</p>
        )}
      </CardContent>
    </Card>
  );
});
