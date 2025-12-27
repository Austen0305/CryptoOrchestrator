import { describe, it, expect } from 'vitest';
import { computeReturns, valueAtRisk, maxDrawdown, sharpeRatio, conditionalVaR } from '../lib/risk';

describe('risk metrics helpers', () => {
  it('computes returns from trades with pnl', () => {
    const trades = [
      { status: 'completed', pnl: 100, price: 50, amount: 2 }, // cost 100 => 100/100 = 1
      { status: 'completed', pnl: -25, price: 25, amount: 1 }, // cost 25 => -25/25 = -1
      { status: 'pending', pnl: 10, price: 10, amount: 1 }, // ignored
    ];
    const returns = computeReturns(trades);
    expect(returns).toEqual([1, -1]);
  });

  it('calculates var95 as absolute lower tail', () => {
    const returns = [0.05, -0.10, 0.02, -0.50, 0.01];
    const var95 = valueAtRisk(returns, 0.95);
    // 95% => index at (1-0.95)=0.05 * n=5 => floor(0.25)=0 -> smallest sorted value = -0.50 => abs = 0.50
    expect(var95).toBeCloseTo(0.50, 2);
  });

  it('calculates cvar95 as mean of tail losses', () => {
    const returns = [0.05, -0.10, 0.02, -0.50, 0.01];
    const cvar = conditionalVaR(returns, 0.95);
    // Tail at 5% for n=5 -> index 0 -> include at least one element -> mean([-0.50]) = -0.50 -> abs
    expect(cvar).toBeCloseTo(0.50, 2);
  });

  it('cvar for empty returns is 0', () => {
    expect(conditionalVaR([], 0.95)).toBe(0);
  });

  it('computes max drawdown', () => {
    const returns = [0.1, -0.05, -0.10, 0.02];
    const dd = maxDrawdown(returns); // simplified cumulative pattern
    expect(dd).toBeGreaterThan(0);
  });

  it('computes sharpe ratio > 0 when avg positive', () => {
    const returns = [0.02, 0.01, 0.03, 0.005];
    const s = sharpeRatio(returns);
    expect(s).toBeGreaterThan(0);
  });
});
