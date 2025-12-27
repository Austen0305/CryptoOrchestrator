import { useMemo } from 'react';
import { usePortfolio, useTrades } from '@/hooks/useApi';
import { computeReturns, multiHorizonVar, multiHorizonConditionalVar } from '@/lib/risk';

export function useRiskHorizons() {
  const { data: portfolio } = usePortfolio('paper');
  const { data: trades } = useTrades();

  // Type guards for portfolio and trades
  const portfolioBalance = portfolio && typeof portfolio === 'object' && 'totalBalance' in portfolio
    ? (portfolio.totalBalance as number) ?? 0
    : 0;
  const tradesArray = Array.isArray(trades) ? trades : [];

  // Stable dependency key: avoids deep compares on trades array by using length + balance snapshot
  const depKey = useMemo(() => {
    return `${portfolioBalance}|${tradesArray.length}`;
  }, [portfolioBalance, tradesArray.length]);

  return useMemo(() => {
    const returns = computeReturns(tradesArray);
    const balance = portfolioBalance;
    const varSeries = multiHorizonVar(returns, balance, 0.95, [1, 7, 30]);
    const esSeries = multiHorizonConditionalVar(returns, balance, 0.95, [1, 7, 30]);
    return { varSeries, esSeries };
  }, [depKey, tradesArray, portfolioBalance]);
}
