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
      className={`group relative overflow-hidden border-2 hover:border-primary/60 bg-gradient-to-br from-card via-card/98 to-card/95 ${className}`} 
      style={{ 
        borderWidth: '3px',
        borderStyle: 'solid',
        background: 'linear-gradient(135deg, hsl(var(--card)), hsl(var(--card) / 0.98), hsl(var(--card) / 0.95))',
        boxShadow: '0px 16px 32px -8px hsl(220 8% 2% / 0.50), 0px 8px 16px -8px hsl(220 8% 2% / 0.50)'
      }}
      role="region"
      aria-label={`${title} portfolio card`}
    >
      <CardHeader 
        className="flex flex-row items-center justify-between space-y-0 pb-5 bg-gradient-to-r from-primary/5 to-transparent border-b border-primary/10"
        style={{
          background: 'linear-gradient(90deg, hsl(var(--primary) / 0.05), transparent)',
          borderBottomWidth: '1px',
          borderBottomStyle: 'solid'
        }}
      >
        <CardTitle className="text-xs md:text-sm font-extrabold text-muted-foreground uppercase tracking-widest">
          {title}
        </CardTitle>
        <div 
          className="p-3.5 rounded-2xl bg-gradient-to-br from-primary/25 to-primary/15 group-hover:from-primary/35 group-hover:to-primary/25 transition-all duration-300 group-hover:scale-110 group-hover:rotate-6 shadow-lg group-hover:shadow-xl border-2 border-primary/30 group-hover:border-primary/50"
          style={{
            background: 'linear-gradient(135deg, hsl(var(--primary) / 0.3), hsl(var(--primary) / 0.2))',
            borderWidth: '2px',
            borderStyle: 'solid',
            boxShadow: '0px 6px 12px -2px hsl(var(--primary) / 0.3), 0px 2px 4px -1px hsl(var(--primary) / 0.2)',
            borderRadius: '1rem'
          }}
        >
          <Icon className="h-5 w-5 md:h-6 md:w-6 text-primary drop-shadow-md" />
        </div>
      </CardHeader>
      <CardContent className="space-y-4 pt-4">
        <div 
          className="text-4xl md:text-5xl font-mono font-black text-foreground drop-shadow-md" 
          data-testid={`text-${title.toLowerCase().replace(/\s/g, '-')}`}
          style={{
            fontSize: 'clamp(2rem, 5vw, 3rem)',
            fontWeight: 900,
            textShadow: '0 2px 4px hsl(var(--foreground) / 0.2)'
          }}
          aria-label={`${title} value: ${value}`}
        >
          {value}
        </div>
        {change !== undefined && (
          <div className="flex items-center gap-2 text-sm">
            <div className={`p-2 rounded-lg ${isPositive ? 'bg-trading-profit/20 border border-trading-profit/30' : 'bg-trading-loss/20 border border-trading-loss/30'} shadow-sm`}>
              {isPositive ? (
                <TrendingUp className="w-4 h-4 md:w-5 md:h-5 text-trading-profit" />
              ) : (
                <TrendingDown className="w-4 h-4 md:w-5 md:h-5 text-trading-loss" />
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
      {/* Subtle gradient overlay on hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/0 via-primary/0 to-primary/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
    </Card>
  );
});
