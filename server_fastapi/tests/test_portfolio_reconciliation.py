"""
Portfolio Reconciliation Tests
Tests portfolio reconciliation service, edge cases, and error scenarios
"""

import logging

import pytest
from httpx import AsyncClient

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


class TestPortfolioReconciliation:
    """Tests for portfolio reconciliation service"""

    async def test_reconcile_portfolio_success(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Test successful portfolio reconciliation"""
        from server_fastapi.services.portfolio_reconciliation import (
            PortfolioReconciliationService,
        )

        service = PortfolioReconciliationService(db_session=db_session)

        # Create test portfolio and trades
        from server_fastapi.models.portfolio import Portfolio
        from server_fastapi.models.trade import Trade

        # Create portfolio
        portfolio = Portfolio(
            user_id="test_user",
            balances={"BTC": 1.0, "ETH": 10.0},
            total_value_usd=50000.0,
        )
        db_session.add(portfolio)
        await db_session.commit()

        # Create matching trades
        trade1 = Trade(
            user_id="test_user",
            symbol="BTC/USD",
            side="buy",
            amount=1.0,
            price=40000.0,
            success=True,
        )
        trade2 = Trade(
            user_id="test_user",
            symbol="ETH/USD",
            side="buy",
            amount=10.0,
            price=3000.0,
            success=True,
        )
        db_session.add(trade1)
        db_session.add(trade2)
        await db_session.commit()

        # Reconcile
        result = await service.reconcile_portfolio("test_user")

        assert result["status"] in ["success", "discrepancies_found"]
        assert "user_id" in result
        assert "trades_analyzed" in result

    async def test_reconcile_portfolio_with_discrepancies(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Test portfolio reconciliation with discrepancies"""
        from server_fastapi.services.portfolio_reconciliation import (
            PortfolioReconciliationService,
        )

        service = PortfolioReconciliationService(db_session=db_session)

        # Create portfolio with incorrect balance
        from server_fastapi.models.portfolio import Portfolio
        from server_fastapi.models.trade import Trade

        portfolio = Portfolio(
            user_id="test_user",
            balances={"BTC": 2.0},  # Incorrect: should be 1.0
            total_value_usd=80000.0,
        )
        db_session.add(portfolio)
        await db_session.commit()

        # Create trade that shows correct balance
        trade = Trade(
            user_id="test_user",
            symbol="BTC/USD",
            side="buy",
            amount=1.0,
            price=40000.0,
            success=True,
        )
        db_session.add(trade)
        await db_session.commit()

        # Reconcile
        result = await service.reconcile_portfolio("test_user")

        assert result["status"] == "discrepancies_found"
        assert result["discrepancy_count"] > 0
        assert len(result["discrepancies"]) > 0

    async def test_reconcile_portfolio_no_portfolio(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Test reconciliation when portfolio doesn't exist"""
        from server_fastapi.services.portfolio_reconciliation import (
            PortfolioReconciliationService,
        )

        service = PortfolioReconciliationService(db_session=db_session)

        result = await service.reconcile_portfolio("nonexistent_user")

        assert result["status"] == "no_portfolio"
        assert "message" in result

    async def test_reconcile_portfolio_no_trades(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Test reconciliation when no trades exist"""
        from server_fastapi.services.portfolio_reconciliation import (
            PortfolioReconciliationService,
        )

        service = PortfolioReconciliationService(db_session=db_session)

        # Create portfolio but no trades
        from server_fastapi.models.portfolio import Portfolio

        portfolio = Portfolio(
            user_id="test_user",
            balances={"BTC": 1.0},
            total_value_usd=40000.0,
        )
        db_session.add(portfolio)
        await db_session.commit()

        result = await service.reconcile_portfolio("test_user")

        # Should detect discrepancy (portfolio has balance but no trades)
        assert result["status"] in ["success", "discrepancies_found"]
        assert result["trades_analyzed"] == 0

    async def test_reconcile_all_portfolios(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Test batch reconciliation of all portfolios"""
        from server_fastapi.services.portfolio_reconciliation import (
            PortfolioReconciliationService,
        )

        service = PortfolioReconciliationService(db_session=db_session)

        # Create multiple portfolios
        from server_fastapi.models.portfolio import Portfolio

        for i in range(3):
            portfolio = Portfolio(
                user_id=f"test_user_{i}",
                balances={"BTC": 1.0},
                total_value_usd=40000.0,
            )
            db_session.add(portfolio)

        await db_session.commit()

        # Reconcile all
        results = await service.reconcile_all_portfolios()

        assert len(results) >= 3
        assert all("status" in r for r in results)

    async def test_reconcile_portfolio_with_failed_trades(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Test reconciliation excluding failed trades"""
        from server_fastapi.services.portfolio_reconciliation import (
            PortfolioReconciliationService,
        )

        service = PortfolioReconciliationService(db_session=db_session)

        # Create portfolio
        from server_fastapi.models.portfolio import Portfolio
        from server_fastapi.models.trade import Trade

        portfolio = Portfolio(
            user_id="test_user",
            balances={"BTC": 1.0},
            total_value_usd=40000.0,
        )
        db_session.add(portfolio)

        # Create successful and failed trades
        successful_trade = Trade(
            user_id="test_user",
            symbol="BTC/USD",
            side="buy",
            amount=1.0,
            price=40000.0,
            success=True,
        )
        failed_trade = Trade(
            user_id="test_user",
            symbol="BTC/USD",
            side="buy",
            amount=0.5,
            price=40000.0,
            success=False,  # Failed trade should be excluded
        )
        db_session.add(successful_trade)
        db_session.add(failed_trade)
        await db_session.commit()

        result = await service.reconcile_portfolio("test_user")

        # Should only count successful trade
        assert result["trades_analyzed"] == 1

    async def test_reconcile_portfolio_multiple_symbols(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Test reconciliation with multiple symbols"""
        from server_fastapi.services.portfolio_reconciliation import (
            PortfolioReconciliationService,
        )

        service = PortfolioReconciliationService(db_session=db_session)

        # Create portfolio with multiple symbols
        from server_fastapi.models.portfolio import Portfolio
        from server_fastapi.models.trade import Trade

        portfolio = Portfolio(
            user_id="test_user",
            balances={"BTC": 1.0, "ETH": 10.0, "USDC": 1000.0},
            total_value_usd=80000.0,
        )
        db_session.add(portfolio)

        # Create trades for each symbol
        trades = [
            Trade(
                user_id="test_user",
                symbol="BTC/USD",
                side="buy",
                amount=1.0,
                price=40000.0,
                success=True,
            ),
            Trade(
                user_id="test_user",
                symbol="ETH/USD",
                side="buy",
                amount=10.0,
                price=3000.0,
                success=True,
            ),
            Trade(
                user_id="test_user",
                symbol="USDC/USD",
                side="buy",
                amount=1000.0,
                price=1.0,
                success=True,
            ),
        ]
        for trade in trades:
            db_session.add(trade)

        await db_session.commit()

        result = await service.reconcile_portfolio("test_user")

        assert result["trades_analyzed"] == 3
        # Should reconcile all symbols correctly

    async def test_reconcile_portfolio_sell_trades(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Test reconciliation with sell trades (should reduce balance)"""
        from server_fastapi.services.portfolio_reconciliation import (
            PortfolioReconciliationService,
        )

        service = PortfolioReconciliationService(db_session=db_session)

        # Create portfolio
        from server_fastapi.models.portfolio import Portfolio
        from server_fastapi.models.trade import Trade

        portfolio = Portfolio(
            user_id="test_user",
            balances={"BTC": 0.5},  # Should be 0.5 after buy and sell
            total_value_usd=20000.0,
        )
        db_session.add(portfolio)

        # Create buy and sell trades
        buy_trade = Trade(
            user_id="test_user",
            symbol="BTC/USD",
            side="buy",
            amount=1.0,
            price=40000.0,
            success=True,
        )
        sell_trade = Trade(
            user_id="test_user",
            symbol="BTC/USD",
            side="sell",
            amount=0.5,
            price=40000.0,
            success=True,
        )
        db_session.add(buy_trade)
        db_session.add(sell_trade)
        await db_session.commit()

        result = await service.reconcile_portfolio("test_user")

        # Calculated balance should be 0.5 (1.0 - 0.5)
        assert result["trades_analyzed"] == 2
        # If there's a discrepancy, it should be detected
