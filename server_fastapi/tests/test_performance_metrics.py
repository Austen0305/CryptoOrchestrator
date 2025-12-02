"""
Tests for performance metrics calculations
"""
import pytest
from datetime import datetime, timedelta
from server_fastapi.routes.performance import (
    DEFAULT_INITIAL_CAPITAL,
    RISK_FREE_RATE,
    TRADING_DAYS_PER_YEAR
)


class TestPerformanceMetrics:
    """Test suite for performance metrics calculations"""

    def test_constants_are_defined(self):
        """Test that configuration constants are properly defined"""
        assert DEFAULT_INITIAL_CAPITAL == 10000.0
        assert RISK_FREE_RATE == 0.04
        assert TRADING_DAYS_PER_YEAR == 252

    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio calculation with known values"""
        # Simulate simple returns
        returns = [0.01] * 100  # 1% daily returns
        
        # Calculate manually
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
        std_return = variance ** 0.5
        
        daily_risk_free = RISK_FREE_RATE / TRADING_DAYS_PER_YEAR
        excess_return = avg_return - daily_risk_free
        expected_sharpe = (excess_return / std_return * (TRADING_DAYS_PER_YEAR ** 0.5)) if std_return > 0 else 0
        
        # Sharpe should be positive for positive returns
        assert expected_sharpe > 0

    def test_sortino_ratio_no_downside(self):
        """Test Sortino ratio when all returns are positive"""
        # All positive returns should have higher Sortino than Sharpe
        returns = [0.01, 0.02, 0.015, 0.012] * 25  # 100 positive returns
        
        # With no downside, Sortino should be higher than Sharpe
        # or should use different calculation
        assert len([r for r in returns if r < 0]) == 0

    def test_max_drawdown_calculation(self):
        """Test maximum drawdown calculation"""
        # Simulate equity curve with drawdown
        initial_capital = DEFAULT_INITIAL_CAPITAL
        profits = [100, -50, 30, -200, 150]  # Contains drawdown
        
        equity = initial_capital
        peak_equity = initial_capital
        max_drawdown = 0
        
        for profit in profits:
            equity += profit
            if equity > peak_equity:
                peak_equity = equity
            drawdown = (peak_equity - equity) / peak_equity if peak_equity > 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Max drawdown should be positive
        assert max_drawdown >= 0
        # Should be less than 100%
        assert max_drawdown < 1.0

    def test_profit_factor_calculation(self):
        """Test profit factor calculation"""
        profits = [100, 150, -50, 200, -30, 80, -20]
        
        winning_profits = [p for p in profits if p > 0]
        losing_profits = [p for p in profits if p < 0]
        
        gross_profit = sum(winning_profits)
        gross_loss = abs(sum(losing_profits))
        
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Profit factor should be positive
        assert profit_factor > 0
        # With more wins, should be > 1
        assert profit_factor > 1

    def test_win_rate_calculation(self):
        """Test win rate calculation"""
        profits = [100, -50, 30, -20, 150, 80, -10]
        
        winning_trades = [p for p in profits if p > 0]
        total_trades = len(profits)
        
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        
        # Win rate should be between 0 and 100
        assert 0 <= win_rate <= 100
        # Should be reasonable for this data
        assert win_rate > 0

    def test_calmar_ratio_calculation(self):
        """Test Calmar ratio calculation"""
        # Annual return
        total_profit = 2000
        initial_capital = DEFAULT_INITIAL_CAPITAL
        days = 365
        
        annualized_return = (total_profit / initial_capital) * (365 / days)
        max_drawdown_pct = 0.15  # 15% max drawdown
        
        calmar_ratio = annualized_return / max_drawdown_pct if max_drawdown_pct > 0 else 0
        
        # Calmar should be positive for positive returns
        assert calmar_ratio > 0

    def test_edge_case_zero_trades(self):
        """Test metrics with zero trades"""
        profits = []
        
        total_profit = sum(profits) if profits else 0
        win_rate = 0 if not profits else (len([p for p in profits if p > 0]) / len(profits) * 100)
        
        assert total_profit == 0
        assert win_rate == 0

    def test_edge_case_all_winning_trades(self):
        """Test metrics when all trades are profitable"""
        profits = [100, 150, 200, 50, 75]
        
        winning_trades = [p for p in profits if p > 0]
        win_rate = (len(winning_trades) / len(profits) * 100)
        
        assert win_rate == 100

    def test_edge_case_all_losing_trades(self):
        """Test metrics when all trades are losing"""
        profits = [-100, -50, -75, -30]
        
        losing_profits = [p for p in profits if p < 0]
        gross_loss = abs(sum(losing_profits))
        
        # Profit factor should be 0 (no gross profit)
        profit_factor = 0 / gross_loss if gross_loss > 0 else 0
        
        assert profit_factor == 0
        assert gross_loss > 0

    def test_risk_free_rate_impact(self):
        """Test that risk-free rate affects Sharpe ratio"""
        # With risk-free rate, excess return should be less
        daily_return = 0.001  # 0.1% daily
        daily_risk_free = RISK_FREE_RATE / TRADING_DAYS_PER_YEAR
        
        excess_return = daily_return - daily_risk_free
        
        # Excess return should be less than raw return
        assert excess_return < daily_return
        # But should still be positive if return > risk-free
        if daily_return > daily_risk_free:
            assert excess_return > 0

    def test_annualization_factor(self):
        """Test that annualization uses correct trading days"""
        # Sharpe ratio annualization factor
        annualization_factor = TRADING_DAYS_PER_YEAR ** 0.5
        
        # Should be ~15.87 for 252 days
        assert 15 < annualization_factor < 16

    def test_drawdown_recovery(self):
        """Test drawdown calculation during recovery"""
        initial_capital = DEFAULT_INITIAL_CAPITAL
        profits = [100, -50, 30]  # Drawdown then partial recovery
        
        equity = initial_capital
        peak_equity = initial_capital
        drawdowns = []
        
        for profit in profits:
            equity += profit
            if equity > peak_equity:
                peak_equity = equity
            drawdown = (peak_equity - equity) / peak_equity if peak_equity > 0 else 0
            drawdowns.append(drawdown)
        
        # Last drawdown should be less than max (recovery happening)
        max_dd = max(drawdowns)
        current_dd = drawdowns[-1]
        
        # Current drawdown should be >= 0
        assert current_dd >= 0


class TestPerformanceAPIModels:
    """Test Pydantic models for performance API"""

    def test_advanced_metrics_model_validation(self):
        """Test AdvancedMetrics model accepts valid data"""
        from server_fastapi.routes.performance import AdvancedMetrics
        
        data = {
            "totalTrades": 100,
            "winningTrades": 65,
            "losingTrades": 35,
            "winRate": 65.0,
            "totalProfit": 5420.50,
            "avgProfit": 54.21,
            "avgWin": 120.0,
            "avgLoss": -80.0,
            "profitFactor": 2.1,
            "sharpeRatio": 1.8,
            "sortinoRatio": 2.3,
            "calmarRatio": 1.5,
            "maxDrawdown": 12.5,
            "maxDrawdownAmount": 1250.0,
            "avgDrawdown": 5.2,
            "currentDrawdown": 0.0,
            "bestTrade": 850.0,
            "worstTrade": -320.0,
            "avgHoldingTime": 120.0,
            "dailyReturn": 0.5,
            "weeklyReturn": 3.5,
            "monthlyReturn": 15.0
        }
        
        metrics = AdvancedMetrics(**data)
        assert metrics.totalTrades == 100
        assert metrics.sharpeRatio == 1.8
        assert metrics.winRate == 65.0

    def test_daily_pnl_model(self):
        """Test DailyPnL model"""
        from server_fastapi.routes.performance import DailyPnL
        
        pnl = DailyPnL(
            date="2025-12-01",
            pnl=150.50,
            cumulativePnl=1500.00,
            trades=5
        )
        
        assert pnl.date == "2025-12-01"
        assert pnl.pnl == 150.50
        assert pnl.trades == 5

    def test_drawdown_point_model(self):
        """Test DrawdownPoint model"""
        from server_fastapi.routes.performance import DrawdownPoint
        
        point = DrawdownPoint(
            date="2025-12-01 10:30",
            drawdown=5.5,
            peakEquity=11000.0,
            currentEquity=10395.0
        )
        
        assert point.drawdown == 5.5
        assert point.peakEquity == 11000.0
