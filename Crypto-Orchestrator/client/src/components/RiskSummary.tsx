import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useRiskMetrics } from '@/hooks/useRiskMetrics';
import { ShieldAlert, Activity } from 'lucide-react';
import { useScenarioStore } from '@/hooks/useScenarioStore';

export const RiskSummary = React.memo(function RiskSummary() {
  const { var95, cvar95, maxDrawdown, sharpe, tradeCount, volatility } = useRiskMetrics();
  const lastScenario = useScenarioStore(s => s.last);

  const riskLevel = maxDrawdown > 30 || volatility > 50 ? 'High' : maxDrawdown > 15 ? 'Medium' : 'Low';
  const riskColor = riskLevel === 'High' ? 'destructive' : riskLevel === 'Medium' ? 'secondary' : 'default';

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base flex items-center gap-2">
          <ShieldAlert className="h-4 w-4" /> Portfolio Risk
        </CardTitle>
        <Badge variant={riskColor}>{riskLevel}</Badge>
      </CardHeader>
      <CardContent className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
        <div>
          <div className="text-muted-foreground">
            <TooltipProvider delayDuration={200}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="underline decoration-dotted cursor-help">VaR (95%)</span>
                </TooltipTrigger>
                <TooltipContent>Worst expected loss at 95% confidence over the next period.</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <div className="font-mono font-semibold">${var95.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
        </div>
        <div>
          <div className="text-muted-foreground">
            <TooltipProvider delayDuration={200}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="underline decoration-dotted cursor-help">CVaR (95%)</span>
                </TooltipTrigger>
                <TooltipContent>Average loss assuming you are already beyond the VaR threshold.</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <div className="font-mono font-semibold">${cvar95.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
        </div>
        <div>
          <div className="text-muted-foreground">Max Drawdown</div>
          <div className="font-mono font-semibold">{maxDrawdown.toFixed(1)}%</div>
        </div>
        <div>
          <div className="text-muted-foreground">Volatility</div>
          <div className="font-mono font-semibold">{volatility.toFixed(1)}%</div>
        </div>
        <div>
          <div className="text-muted-foreground">Sharpe (est.)</div>
          <div className="font-mono font-semibold">{sharpe.toFixed(2)}</div>
        </div>
        <div className="col-span-2 md:col-span-5 text-xs text-muted-foreground flex items-center gap-2">
          <Activity className="h-3 w-3" /> Based on {tradeCount} completed trades
        </div>
        {lastScenario && (
          <div className="col-span-2 md:col-span-5 text-xs text-muted-foreground">
            Scenario: shocked VaR { (lastScenario.shocked_var * 100).toFixed(2) }% · projected { (lastScenario.projected_var * 100).toFixed(2) }% over { lastScenario.horizon_days }d
          </div>
        )}
      </CardContent>
    </Card>
  );
});
