import { useMemo } from 'react';
import { usePortfolio, useTrades } from '@/hooks/useApi';
import { computeReturns, valueAtRisk, maxDrawdown, sharpeRatio, conditionalVaR } from '@/lib/risk';

interface RiskMetrics {
  var95: number; // Value-at-Risk at 95%
  cvar95: number; // Conditional Value-at-Risk at 95%
  maxDrawdown: number; // percentage
  sharpe: number; // simplified daily Sharpe
  tradeCount: number;
  volatility: number; // std dev of returns
  multiVar?: { horizon: string; value: number }[]; // future multi-horizon VaR values
}

export function useRiskMetrics(): RiskMetrics {
  const { data: portfolio } = usePortfolio('paper');
  const { data: trades } = useTrades();

  return useMemo(() => {
    const tradeList = trades || [];
    const returns = computeReturns(tradeList);
    const vol = returns.length
      ? Math.sqrt(
          returns.reduce((s, r) => s + (r * r), 0) / returns.length -
            Math.pow(returns.reduce((a, b) => a + b, 0) / returns.length, 2)
        )
      : 0;
    const balance = portfolio?.totalBalance || 0;
    return {
      var95: valueAtRisk(returns, 0.95) * balance,
      cvar95: conditionalVaR(returns, 0.95) * balance,
      maxDrawdown: maxDrawdown(returns) * 100,
      sharpe: sharpeRatio(returns),
      tradeCount: tradeList.length,
      volatility: vol * 100,
      multiVar: [
        { horizon: '1D', value: valueAtRisk(returns, 0.95) * balance },
        { horizon: '7D', value: valueAtRisk(returns, 0.95) * balance * Math.sqrt(7) },
        { horizon: '30D', value: valueAtRisk(returns, 0.95) * balance * Math.sqrt(30) }
      ]
    };
  }, [trades, portfolio]);
}
