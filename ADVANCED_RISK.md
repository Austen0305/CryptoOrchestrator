# 📐 Advanced Risk Metrics

This document outlines the initial risk calculations integrated into the dashboard and future enhancement paths.

## Current Metrics

| Metric | Description | Formula (Simplified) |
|--------|-------------|----------------------|
| VaR (95%) | Estimated worst loss (absolute) at 95% confidence based on trade return distribution. | `abs(quantile(return, 0.05)) * portfolioBalance` |
| Max Drawdown | Largest peak-to-trough cumulative return decline (percent). | `max((peak - trough)/peak)` over cumulative returns |
| Volatility | Standard deviation of trade returns (percent). | `std(returns) * 100` |
| Sharpe (est.) | Risk-adjusted return (annualized, risk-free ~ 0). | `(avg(returns)/std(returns))*sqrt(252)` |

## Data Sources

1. Trades: Completed trades with `pnl` or `profit` fields.
2. Portfolio: Total balance provides scaling for VaR.

## Assumptions

- Returns approximated from `pnl / cost` where cost = `price * amount` or `total`.
- Risk-free rate assumed negligible.
- Daily scaling (sqrt(252)) applied even if trading frequency differs.
- No correlation modeling yet (positions treated independently implicitly).

## Limitations

- Small trade sample leads to unstable VaR.
- Drawdown computed from cumulative trade returns—not full equity curve or mark-to-market.
- Volatility ignores intraday unrealized PnL.
- Sharpe ignores skew/kurtosis and assumes IID returns.

## Future Enhancements

| Feature | Benefit |
|---------|---------|
| Historical Equity Curve reconstruction | Accurate drawdown & recovery analysis |
| Expected Shortfall (CVaR) | Better tail risk characterization |
| Position Greeks (for options) | Portfolio sensitivity insight |
| Regime Detection (volatility clustering) | Adaptive risk scaling |
| Correlation Matrix & Diversification Score | Portfolio concentration measurement |
| Dynamic Position Sizing via Kelly Fraction | Systematic capital allocation |
| Stress Testing (shock scenarios) | Evaluate resilience under extreme moves |
| Multi-horizon VaR (1d, 7d, 30d) | Strategic vs tactical risk overview |
| Risk Budget per Strategy | Enforce allocation discipline |

## Scenario Simulator (Shock VaR + Horizon Scaling)

The platform exposes a backend endpoint and a frontend panel to simulate stress scenarios and project VaR across horizons.

- Frontend: Risk Scenario panel in the dashboard lets you input Portfolio Value, Baseline VaR, Shock Percent, Horizon (days), and Correlation Factor.
- Backend: POST /api/risk-scenarios/simulate returns shocked and projected VaR with a human-readable explanation.

Example request:

```json
{
  "portfolio_value": 100000,
  "baseline_var": 2500,
  "shock_percent": -0.10,
  "horizon_days": 7,
  "correlation_factor": 1.2
}
```

Example response (fields abbreviated):

```json
{
  "portfolio_value": 100000,
  "baseline_var": 2500,
  "shock_percent": -0.1,
  "correlation_factor": 1.2,
  "horizon_days": 7,
  "shocked_var": 0.035,
  "projected_var": 0.092,
  "stress_loss": 3500,
  "horizon_scale": 2.65,
  "explanation": "Shock applied at 10.0% with correlation factor 1.20. Horizon scaling by sqrt(7)."
}
```

Notes
- shocked_var and projected_var are proportions; multiply by portfolio_value for currency.
- correlation_factor ≥ 1 models elevated co-movements; < 1 dampens.
- horizon scaling uses sqrt(time) as a first-order approximation.

### Real-Time Scenario Broadcast

When a scenario is simulated via `/api/risk-scenarios/simulate`, the backend automatically broadcasts the result over the WebSocket notification channel (`/ws/notifications`) in addition to returning it in the HTTP response.

**WebSocket Event Structure:**

```json
{
  "type": "risk_scenario",
  "data": {
    "id": "...",
    "type": "risk_scenario",
    "category": "RISK",
    "priority": "high",
    "title": "Risk Scenario Simulated",
    "message": "Portfolio VaR projected for shock scenario",
    "read": false,
    "created_at": "...",
    "data": {
      "portfolio_value": 100000,
      "baseline_var": 2500,
      "shock_percent": -0.1,
      "shocked_var": 0.035,
      "projected_var": 0.092,
      "stress_loss": 3500,
      "horizon_days": 7,
      "horizon_scale": 2.65,
      "correlation_factor": 1.2,
      "explanation": "Shock applied at 10.0% with correlation factor 1.20. Horizon scaling by sqrt(7)."
    }
  }
}
```

**Client Handling:**

The frontend `useNotifications` hook listens for `risk_scenario` events and:

1. Updates the Zustand scenario store (`useScenarioStore`) with the scenario result for display in the Risk Scenario panel.
2. Surfaces the event as a notification in the UI notifications list.

This enables live updates to the scenario history without polling, and users can view scenario results in real time across multiple browser tabs or sessions.

## Extension Pattern

Add new metrics by:

1. Extending `risk.ts` with pure function implementation.
2. Composing inside `useRiskMetrics` to avoid duplicating data fetch.
3. Writing isolated vitest unit test for formula correctness.
4. Extending `RiskSummary` with new cards or tooltip details.

## Example: Adding Expected Shortfall

```ts
export function conditionalVaR(returns: number[], confidence = 0.95): number {
  if (!returns.length) return 0;
  const sorted = [...returns].sort((a,b) => a-b);
  const cutoffIndex = Math.floor((1 - confidence) * sorted.length);
  const tail = sorted.slice(0, Math.max(1, cutoffIndex));
  return Math.abs(tail.reduce((a,b)=>a+b,0)/tail.length || 0);
}
```

## Dashboard Integration Philosophy

- Keep the UI concise: badge risk level + core metrics.
- Offer drill-down modal for advanced users (future).
- Avoid overfitting early—start with robust, interpretable metrics.
- Inline tooltips explain VaR (worst expected loss at threshold) and CVaR (average loss beyond VaR).

---

Risk analytics will evolve iteratively; foundations are now in place for deeper modeling.

