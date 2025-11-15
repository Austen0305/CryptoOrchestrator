import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useRunRiskScenario } from '@/hooks/useApi';
import { useScenarioStore } from '@/hooks/useScenarioStore';

export function RiskScenarioPanel() {
  const [portfolioValue, setPortfolioValue] = useState<number>(100000);
  const [baselineVar, setBaselineVar] = useState<number>(0.05); // 5%
  const [shockPercent, setShockPercent] = useState<number>(-0.1); // -10%
  const [horizonDays, setHorizonDays] = useState<number>(1);
  const [correlationFactor, setCorrelationFactor] = useState<number>(1);

  const { mutate: run, data, isPending, error, reset } = useRunRiskScenario();
  const addScenario = useScenarioStore(s => s.add);

  useEffect(() => {
    if (data) addScenario(data);
  }, [data, addScenario]);

  function onRun() {
    run({
      portfolio_value: Number(portfolioValue),
      baseline_var: Number(baselineVar),
      shock_percent: Number(shockPercent),
      horizon_days: Number(horizonDays),
      correlation_factor: Number(correlationFactor),
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Risk Scenario Simulator</CardTitle>
        <CardDescription>Shock VaR and horizon scaling via backend analytics</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="portfolioValue">Portfolio Value (USD)</Label>
            <Input id="portfolioValue" type="number" value={portfolioValue} onChange={(e) => setPortfolioValue(Number(e.target.value))} min={0} step={100} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="baselineVar">Baseline VaR (fraction)</Label>
            <Input id="baselineVar" type="number" value={baselineVar} onChange={(e) => setBaselineVar(Number(e.target.value))} min={0} max={1} step={0.005} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="shockPercent">Shock Percent (fraction, negative = drop)</Label>
            <Input id="shockPercent" type="number" value={shockPercent} onChange={(e) => setShockPercent(Number(e.target.value))} min={-1} max={1} step={0.01} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="horizonDays">Horizon (days)</Label>
            <Input id="horizonDays" type="number" value={horizonDays} onChange={(e) => setHorizonDays(Number(e.target.value))} min={1} max={365} step={1} />
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label id="cf-label" htmlFor="correlationFactor">Correlation Factor (0-2, 1 = baseline)</Label>
            <Input aria-labelledby="cf-label" aria-describedby="cf-help" id="correlationFactor" type="number" value={correlationFactor} onChange={(e) => setCorrelationFactor(Number(e.target.value))} min={0} max={2} step={0.05} />
            <div id="cf-help" className="sr-only">Higher values amplify shocks across correlated assets.</div>
          </div>
        </div>

        <div className="mt-4 flex gap-2" aria-live="polite">
          <Button onClick={onRun} disabled={isPending}> {isPending ? 'Running…' : 'Run Scenario'} </Button>
          {data && <Button variant="outline" onClick={() => reset()}>Clear</Button>}
        </div>

        {error && (
          <div className="mt-3 text-sm text-red-600">{String(error)}</div>
        )}

        {data && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
            <div className="rounded-md border p-3">
              <div className="text-muted-foreground">Shocked VaR</div>
              <div className="text-lg font-semibold">{(data.shocked_var * 100).toFixed(2)}%</div>
            </div>
            <div className="rounded-md border p-3">
              <div className="text-muted-foreground">Projected VaR ({data.horizon_days}d)</div>
              <div className="text-lg font-semibold">{(data.projected_var * 100).toFixed(2)}%</div>
            </div>
            <div className="rounded-md border p-3">
              <div className="text-muted-foreground">Stress Loss (USD)</div>
              <div className="text-lg font-semibold">${data.stress_loss.toLocaleString()}</div>
            </div>
            <div className="md:col-span-3 rounded-md bg-muted p-3 text-xs">
              {data.explanation}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default RiskScenarioPanel;
