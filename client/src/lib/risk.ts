// Shared risk calculations utilities

export function computeReturns(trades: any[]): number[] {
  return trades
    .filter(t => t.status === 'completed')
    .map(t => {
      const pnl = (t.pnl ?? t.profit ?? 0);
      const cost = t.total || (t.price * t.amount) || 1;
      return cost !== 0 ? pnl / cost : 0;
    })
    .filter(r => Number.isFinite(r));
}

export function valueAtRisk(returns: number[], confidence = 0.95): number {
  if (!returns.length) return 0;
  const sorted = [...returns].sort((a, b) => a - b);
  const index = Math.floor((1 - confidence) * sorted.length);
  const val = sorted[Math.max(0, Math.min(sorted.length - 1, index))] ?? 0;
  return Math.abs(val);
}

export function maxDrawdown(returns: number[]): number {
  if (!returns.length) return 0;
  let peak = 0;
  let trough = 0;
  let maxDd = 0;
  let cumulative = 0;
  for (const r of returns) {
    cumulative += r;
    if (cumulative > peak) {
      peak = cumulative;
      trough = cumulative;
    }
    if (cumulative < trough) {
      trough = cumulative;
      const denom = peak === 0 ? 1 : peak;
      const dd = (peak - trough) / denom;
      if (dd > maxDd) maxDd = dd;
    }
  }
  return maxDd;
}

export function sharpeRatio(returns: number[]): number {
  if (!returns.length) return 0;
  const avg = returns.reduce((a, b) => a + b, 0) / returns.length;
  const vol = Math.sqrt(
    returns.reduce((sum, r) => sum + Math.pow(r - avg, 2), 0) / returns.length
  );
  if (vol === 0) return 0;
  return (avg / vol) * Math.sqrt(252);
}

export function conditionalVaR(returns: number[], confidence = 0.95): number {
  if (!returns.length) return 0;
  const sorted = [...returns].sort((a, b) => a - b);
  const cutoffIndex = Math.floor((1 - confidence) * sorted.length);
  const tail = sorted.slice(0, Math.max(1, cutoffIndex));
  if (tail.length === 0) return 0;
  const avgTail = tail.reduce((a, b) => a + b, 0) / tail.length;
  return Math.abs(avgTail);
}

export function multiHorizonVar(
  returns: number[],
  balance: number,
  confidence = 0.95,
  horizons: number[] = [1, 7, 30]
): { horizon: string; var: number }[] {
  const base = valueAtRisk(returns, confidence) * balance;
  const uniq = Array.from(new Set(horizons.filter(h => Number.isFinite(h) && h > 0))).sort((a,b)=>a-b);
  return uniq.map(h => ({ horizon: `${h}D`, var: base * Math.sqrt(Math.max(1, h)) }));
}

export function multiHorizonConditionalVar(
  returns: number[],
  balance: number,
  confidence = 0.95,
  horizons: number[] = [1, 7, 30]
): { horizon: string; cvar: number }[] {
  const base = conditionalVaR(returns, confidence) * balance;
  const uniq = Array.from(new Set(horizons.filter(h => Number.isFinite(h) && h > 0))).sort((a,b)=>a-b);
  return uniq.map(h => ({ horizon: `${h}D`, cvar: base * Math.sqrt(Math.max(1, h)) }));
}
