"""
Portfolio Reconciliation Service
Validates portfolio balances against trade history to detect discrepancies
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class PortfolioReconciliationService:
    """Service for reconciling portfolio balances with trade history"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def reconcile_portfolio(self, user_id: str) -> Dict:
        """
        Reconcile portfolio balances with trade history

        Args:
            user_id: User ID to reconcile

        Returns:
            Dict with reconciliation results and any discrepancies found
        """
        try:
            from ..models.portfolio import Portfolio
            from ..models.trade import Trade

            # Get user's portfolio
            stmt = select(Portfolio).where(Portfolio.user_id == user_id)
            result = await self.db.execute(stmt)
            portfolio = result.scalar_one_or_none()

            if not portfolio:
                logger.warning(f"No portfolio found for user {user_id}")
                return {
                    "user_id": user_id,
                    "status": "no_portfolio",
                    "message": "Portfolio not found",
                }

            # Calculate actual balances from trades
            stmt = select(Trade).where(Trade.user_id == user_id, Trade.success == True)
            result = await self.db.execute(stmt)
            trades = result.scalars().all()

            # Aggregate balances by symbol
            calculated_balances = {}
            for trade in trades:
                # Extract base currency from symbol (e.g., BTC from BTC/USD)
                if "/" in trade.symbol:
                    base_symbol = trade.symbol.split("/")[0]
                else:
                    base_symbol = trade.symbol

                if base_symbol not in calculated_balances:
                    calculated_balances[base_symbol] = 0.0

                # Add for buy, subtract for sell
                if trade.side.lower() == "buy":
                    calculated_balances[base_symbol] += trade.amount
                else:
                    calculated_balances[base_symbol] -= trade.amount

            # Compare and flag discrepancies
            discrepancies = []
            tolerance = 0.0001  # Tolerance for floating point comparison

            # Check all symbols in calculated balances
            for symbol, calculated in calculated_balances.items():
                stored = portfolio.balances.get(symbol, 0.0)
                difference = abs(calculated - stored)

                if difference > tolerance:
                    discrepancies.append(
                        {
                            "symbol": symbol,
                            "stored": stored,
                            "calculated": calculated,
                            "difference": calculated - stored,
                            "difference_abs": difference,
                        }
                    )

            # Check for symbols in portfolio but not in trades
            for symbol, stored in portfolio.balances.items():
                if symbol not in calculated_balances and abs(stored) > tolerance:
                    discrepancies.append(
                        {
                            "symbol": symbol,
                            "stored": stored,
                            "calculated": 0.0,
                            "difference": -stored,
                            "difference_abs": abs(stored),
                        }
                    )

            # Handle discrepancies
            if discrepancies:
                logger.warning(
                    f"Portfolio discrepancies found for user {user_id}: "
                    f"{len(discrepancies)} symbols affected"
                )
                await self._handle_discrepancies(user_id, discrepancies)
                status = "discrepancies_found"
            else:
                logger.info(f"Portfolio reconciliation passed for user {user_id}")
                status = "success"

            return {
                "user_id": user_id,
                "status": status,
                "portfolio_id": portfolio.id,
                "trades_analyzed": len(trades),
                "discrepancies": discrepancies,
                "discrepancy_count": len(discrepancies),
            }

        except Exception as e:
            logger.error(
                f"Portfolio reconciliation failed for user {user_id}: {e}",
                exc_info=True,
            )
            return {"user_id": user_id, "status": "error", "error": str(e)}

    async def reconcile_all_portfolios(self) -> List[Dict]:
        """Reconcile all user portfolios"""
        try:
            from ..models.portfolio import Portfolio

            # Get all user IDs with portfolios
            stmt = select(Portfolio.user_id).distinct()
            result = await self.db.execute(stmt)
            user_ids = [row[0] for row in result.fetchall()]

            logger.info(f"Starting reconciliation for {len(user_ids)} portfolios")

            # Reconcile each portfolio
            results = []
            for user_id in user_ids:
                result = await self.reconcile_portfolio(user_id)
                results.append(result)

            # Summary statistics
            success_count = sum(1 for r in results if r["status"] == "success")
            discrepancy_count = sum(
                1 for r in results if r["status"] == "discrepancies_found"
            )
            error_count = sum(1 for r in results if r["status"] == "error")

            logger.info(
                f"Reconciliation complete: {success_count} success, "
                f"{discrepancy_count} with discrepancies, {error_count} errors"
            )

            return results

        except Exception as e:
            logger.error(f"Batch reconciliation failed: {e}", exc_info=True)
            return []

    async def _handle_discrepancies(self, user_id: str, discrepancies: List[Dict]):
        """
        Handle portfolio discrepancies by creating alerts

        Args:
            user_id: User ID
            discrepancies: List of discrepancy details
        """
        try:
            from ..services.risk_service import RiskService

            # Create risk service instance with current DB session
            risk_service = RiskService(db_session=self.db)

            # Create summary message
            total_discrepancies = len(discrepancies)
            symbols_affected = ", ".join([d["symbol"] for d in discrepancies[:5]])
            if total_discrepancies > 5:
                symbols_affected += f" and {total_discrepancies - 5} more"

            message = (
                f"Portfolio reconciliation found {total_discrepancies} discrepancies. "
                f"Affected symbols: {symbols_affected}"
            )

            # Determine severity based on magnitude
            max_difference = max(d["difference_abs"] for d in discrepancies)
            if max_difference > 1.0:
                severity = "high"
            elif max_difference > 0.1:
                severity = "medium"
            else:
                severity = "low"

            # Create alert in database
            await risk_service.create_alert_db(
                user_id=user_id,
                alert_type="portfolio_reconciliation",
                severity=severity,
                message=message,
                current_value=total_discrepancies,
                threshold_value=0.0,
            )

            logger.info(f"Created reconciliation alert for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to create discrepancy alert: {e}", exc_info=True)


async def reconcile_user_portfolio(user_id: str, session: AsyncSession) -> Dict:
    """Convenience helper to trigger reconciliation using existing session."""
    service = PortfolioReconciliationService(db_session=session)
    return await service.reconcile_portfolio(user_id)
