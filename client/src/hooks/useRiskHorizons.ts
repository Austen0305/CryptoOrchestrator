import { useMemo } from 'react';
import { usePortfolio, useTrades } from '@/hooks/useApi';
import { computeReturns, multiHorizonVar, multiHorizonConditionalVar } from '@/lib/risk';

export function useRiskHorizons() {
  const { data: portfolio } = usePortfolio('paper');
  const { data: trades } = useTrades();

  // Stable dependency key: avoids deep compares on trades array by using length + balance snapshot
  const depKey = useMemo(() => {
    return `${portfolio?.totalBalance || 0}|${(trades || []).length}`;
  }, [portfolio?.totalBalance, (trades || []).length]);

  return useMemo(() => {
    const returns = computeReturns(trades || []);
    const balance = portfolio?.totalBalance || 0;
    const varSeries = multiHorizonVar(returns, balance, 0.95, [1, 7, 30]);
    const esSeries = multiHorizonConditionalVar(returns, balance, 0.95, [1, 7, 30]);
    return { varSeries, esSeries };
  }, [depKey]);
}
