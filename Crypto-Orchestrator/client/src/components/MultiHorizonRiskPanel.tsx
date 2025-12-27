import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { useRiskHorizons } from '@/hooks/useRiskHorizons';

export function MultiHorizonRiskPanel() {
  const { varSeries, esSeries } = useRiskHorizons();

  return (
    <Card role="region" aria-labelledby="multi-horizon-heading">
      <CardHeader>
        <CardTitle id="multi-horizon-heading">Multi-Horizon VaR & ES</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div aria-labelledby="var95-heading">
            <div id="var95-heading" className="text-muted-foreground mb-2">VaR (95%)</div>
            <div className="grid grid-cols-3 gap-2" role="list">
              {varSeries.map(s => (
                <div
                  key={s.horizon}
                  className="rounded border p-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  role="listitem"
                  tabIndex={0}
                  aria-label={`VaR ${s.horizon} ${s.var.toLocaleString(undefined, { maximumFractionDigits: 0 })} dollars`}
                >
                  <div className="text-xs text-muted-foreground">{s.horizon}</div>
                  <div className="font-mono font-semibold">${s.var.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
                </div>
              ))}
            </div>
          </div>
          <div aria-labelledby="es95-heading">
            <div id="es95-heading" className="text-muted-foreground mb-2">Expected Shortfall (95%)</div>
            <div className="grid grid-cols-3 gap-2" role="list">
              {esSeries.map(s => (
                <div
                  key={s.horizon}
                  className="rounded border p-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  role="listitem"
                  tabIndex={0}
                  aria-label={`Expected Shortfall ${s.horizon} ${s.cvar.toLocaleString(undefined, { maximumFractionDigits: 0 })} dollars`}
                >
                  <div className="text-xs text-muted-foreground">{s.horizon}</div>
                  <div className="font-mono font-semibold">${s.cvar.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="sr-only" aria-live="polite">
          {/* Summary for assistive tech: announce latest horizon values */}
          Latest VaR {varSeries[varSeries.length - 1]?.horizon}: ${varSeries[varSeries.length - 1]?.var.toLocaleString(undefined, { maximumFractionDigits: 0 })}. 
          Latest ES {esSeries[esSeries.length - 1]?.horizon}: ${esSeries[esSeries.length - 1]?.cvar.toLocaleString(undefined, { maximumFractionDigits: 0 })}.
        </div>
      </CardContent>
    </Card>
  );
}

export default MultiHorizonRiskPanel;
