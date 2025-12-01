import { multiHorizonVar, multiHorizonConditionalVar } from '../risk';

describe('multiHorizon risk helpers', () => {
  const returns = [0.01, -0.02, 0.005, 0.003, -0.01, 0.02];
  const balance = 10000;

  test('handles empty returns', () => {
    expect(multiHorizonVar([], balance)).toEqual([
      { horizon: '1D', var: 0 },
      { horizon: '7D', var: 0 },
      { horizon: '30D', var: 0 }
    ]);
  });

  test('dedupes and sorts horizons, filters invalid', () => {
    const res = multiHorizonVar(returns, balance, 0.95, [7, 1, 30, 7, -5, NaN, 2]);
    expect(res.map(r => r.horizon)).toEqual(['1D','2D','7D','30D']);
  });

  test('scales VAR by sqrt(time)', () => {
    const base = rescale(returns, balance);
    const res = multiHorizonVar(returns, balance, 0.95, [1,7,30]);
    expect(closeTo(res[0].var, base * Math.sqrt(1))).toBe(true);
    expect(closeTo(res[1].var, base * Math.sqrt(7))).toBe(true);
    expect(closeTo(res[2].var, base * Math.sqrt(30))).toBe(true);
  });

  test('conditional var parallels var horizon scaling', () => {
    const baseC = rescaleC(returns, balance);
    const res = multiHorizonConditionalVar(returns, balance, 0.95, [1,7,30]);
    expect(closeTo(res[0].cvar, baseC * Math.sqrt(1))).toBe(true);
    expect(closeTo(res[1].cvar, baseC * Math.sqrt(7))).toBe(true);
    expect(closeTo(res[2].cvar, baseC * Math.sqrt(30))).toBe(true);
  });
});

function valueAtRiskRaw(returns: number[], confidence = 0.95): number {
  if (!returns.length) return 0;
  const sorted = [...returns].sort((a,b)=>a-b);
  const index = Math.floor((1 - confidence) * sorted.length);
  const val = sorted[Math.max(0, Math.min(sorted.length - 1, index))] ?? 0;
  return Math.abs(val);
}
function conditionalVaRRaw(returns: number[], confidence = 0.95): number {
  if (!returns.length) return 0;
  const sorted = [...returns].sort((a,b)=>a-b);
  const cutoffIndex = Math.floor((1 - confidence) * sorted.length);
  const tail = sorted.slice(0, Math.max(1, cutoffIndex));
  if (!tail.length) return 0;
  const avgTail = tail.reduce((a,b)=>a+b,0)/tail.length;
  return Math.abs(avgTail);
}
function rescale(returns: number[], balance: number){
  return valueAtRiskRaw(returns, 0.95) * balance;
}
function rescaleC(returns: number[], balance: number){
  return conditionalVaRRaw(returns, 0.95) * balance;
}
function closeTo(a: number, b: number, eps = 1e-8){
  return Math.abs(a - b) < eps;
}
