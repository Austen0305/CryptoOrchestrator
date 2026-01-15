"""
Historical Performance Verification Service
Verifies and validates signal provider historical performance data.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.signal_provider import SignalProvider
from ..models.trade import Trade
from ..repositories.trade_repository import TradeRepository

logger = logging.getLogger(__name__)


class MarketplaceVerificationService:
    """
    Service for verifying historical performance of signal providers.
    Validates trade history, calculates verified metrics, and flags discrepancies.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.trade_repository = TradeRepository()

    async def verify_provider_performance(
        self,
        provider_id: int,
        period_days: int = 90,
    ) -> dict[str, Any]:
        """
        Verify historical performance for a signal provider.

        Args:
            provider_id: Signal provider ID
            period_days: Period to verify (default: 90 days)

        Returns:
            Dict with verification results
        """
        try:
            # Get provider
            provider = await self.db.get(SignalProvider, provider_id)
            if not provider:
                raise ValueError("Signal provider not found")

            # Get trade history for provider's user
            period_start = datetime.now(UTC) - timedelta(days=period_days)

            trades_result = await self.db.execute(
                select(Trade)
                .where(
                    and_(
                        Trade.user_id == provider.user_id,
                        Trade.mode == "real",  # Only real trades
                        Trade.status == "completed",
                        Trade.executed_at >= period_start,
                    )
                )
                .order_by(Trade.executed_at.desc())
            )
            trades = list(trades_result.scalars().all())

            if len(trades) == 0:
                return {
                    "provider_id": provider_id,
                    "verified": False,
                    "reason": "No trades found in period",
                    "period_days": period_days,
                    "trades_count": 0,
                }

            # Calculate verified metrics
            verified_metrics = self._calculate_verified_metrics(trades)

            # Compare with stored metrics
            stored_metrics = {
                "total_return": provider.total_return or 0.0,
                "sharpe_ratio": provider.sharpe_ratio or 0.0,
                "win_rate": provider.win_rate or 0.0,
                "total_trades": provider.total_trades or 0,
            }

            # Calculate discrepancies
            discrepancies = self._calculate_discrepancies(
                stored_metrics, verified_metrics
            )

            # Determine verification status
            verified = len(discrepancies) == 0 or all(
                abs(diff["difference"]) < 0.05
                for diff in discrepancies  # 5% tolerance
            )

            # Send email notification if verification failed
            if not verified and discrepancies:
                try:
                    from ..models.user import User
                    from ..services.marketplace_email_service import (
                        MarketplaceEmailService,
                    )

                    user = await self.db.get(User, provider.user_id)
                    if user and user.email:
                        email_service = MarketplaceEmailService()
                        import asyncio

                        asyncio.create_task(
                            email_service.send_verification_failure_email(
                                to_email=user.email,
                                provider_name=user.username or user.email,
                                discrepancies=discrepancies,
                            )
                        )
                except Exception as e:
                    logger.warning(f"Failed to send verification failure email: {e}")

            return {
                "provider_id": provider_id,
                "verified": verified,
                "period_days": period_days,
                "trades_count": len(trades),
                "verified_metrics": verified_metrics,
                "stored_metrics": stored_metrics,
                "discrepancies": discrepancies,
                "verification_date": datetime.now(UTC).isoformat(),
            }
        except Exception as e:
            logger.error(f"Error verifying provider performance: {e}", exc_info=True)
            raise

    def _calculate_verified_metrics(self, trades: list[Trade]) -> dict[str, Any]:
        """Calculate metrics from verified trade history"""
        if not trades:
            return {
                "total_return": 0.0,
                "sharpe_ratio": 0.0,
                "win_rate": 0.0,
                "total_trades": 0,
                "profit_factor": 0.0,
                "max_drawdown": 0.0,
            }

        # Calculate P&L
        total_pnl = sum(trade.pnl or 0.0 for trade in trades)
        winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl and t.pnl < 0]

        # Total return (assuming initial balance)
        initial_balance = 10000.0  # Default assumption
        total_return = (
            (total_pnl / initial_balance) * 100 if initial_balance > 0 else 0.0
        )

        # Win rate
        win_rate = len(winning_trades) / len(trades) if trades else 0.0

        # Profit factor
        total_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0.0
        total_loss = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 1.0
        profit_factor = total_profit / total_loss if total_loss > 0 else 0.0

        # Sharpe ratio (simplified)
        returns = [t.pnl_percent or 0.0 for t in trades if t.pnl_percent is not None]
        if len(returns) > 1:
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = (
                (mean_return / std_return) * np.sqrt(252) if std_return > 0 else 0.0
            )
        else:
            sharpe_ratio = 0.0

        # Max drawdown
        cumulative_pnl = []
        running_total = 0.0
        for trade in sorted(trades, key=lambda t: t.executed_at):
            running_total += trade.pnl or 0.0
            cumulative_pnl.append(running_total)

        if cumulative_pnl:
            peak = cumulative_pnl[0]
            max_drawdown = 0.0
            for value in cumulative_pnl:
                if value > peak:
                    peak = value
                drawdown = ((peak - value) / peak) * 100 if peak > 0 else 0.0
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        else:
            max_drawdown = 0.0

        return {
            "total_return": round(total_return, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "win_rate": round(win_rate, 4),
            "total_trades": len(trades),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown": round(max_drawdown, 2),
        }

    def _calculate_discrepancies(
        self, stored: dict[str, Any], verified: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Calculate discrepancies between stored and verified metrics"""
        discrepancies = []

        for key in ["total_return", "sharpe_ratio", "win_rate", "total_trades"]:
            stored_value = stored.get(key, 0.0)
            verified_value = verified.get(key, 0.0)

            if stored_value == 0 and verified_value == 0:
                continue

            if stored_value != 0:
                difference = ((verified_value - stored_value) / abs(stored_value)) * 100
            else:
                difference = 100.0 if verified_value != 0 else 0.0

            if abs(difference) > 5.0:  # 5% threshold
                discrepancies.append(
                    {
                        "metric": key,
                        "stored": stored_value,
                        "verified": verified_value,
                        "difference": round(difference, 2),
                        "difference_percent": round(difference, 2),
                    }
                )

        return discrepancies

    async def verify_all_providers(self, period_days: int = 90) -> dict[str, Any]:
        """
        Verify all approved signal providers.

        Args:
            period_days: Period to verify (default: 90 days)

        Returns:
            Dict with verification summary
        """
        try:
            # Get all approved providers
            providers_result = await self.db.execute(
                select(SignalProvider).where(
                    SignalProvider.curator_status == "approved"
                )
            )
            providers = list(providers_result.scalars().all())

            results = {
                "total_providers": len(providers),
                "verified": 0,
                "failed": 0,
                "no_trades": 0,
                "verifications": [],
            }

            for provider in providers:
                try:
                    verification = await self.verify_provider_performance(
                        provider.id, period_days
                    )
                    results["verifications"].append(verification)

                    if verification["verified"]:
                        results["verified"] += 1
                    elif verification.get("trades_count", 0) == 0:
                        results["no_trades"] += 1
                    else:
                        results["failed"] += 1
                except Exception as e:
                    logger.error(
                        f"Error verifying provider {provider.id}: {e}", exc_info=True
                    )
                    results["failed"] += 1

            return results
        except Exception as e:
            logger.error(f"Error verifying all providers: {e}", exc_info=True)
            raise

    async def flag_suspicious_providers(
        self, threshold_days: int = 30
    ) -> list[dict[str, Any]]:
        """
        Flag providers with suspicious activity or discrepancies.

        Args:
            threshold_days: Days since last verification to flag

        Returns:
            List of flagged providers
        """
        try:
            flagged = []

            # Get providers that haven't been verified recently
            datetime.now(UTC) - timedelta(days=threshold_days)

            providers_result = await self.db.execute(
                select(SignalProvider).where(
                    SignalProvider.curator_status == "approved"
                )
            )
            providers = list(providers_result.scalars().all())

            for provider in providers:
                # Verify performance
                verification = await self.verify_provider_performance(
                    provider.id, period_days=90
                )

                if not verification["verified"]:
                    flagged.append(
                        {
                            "provider_id": provider.id,
                            "user_id": provider.user_id,
                            "reason": "Performance discrepancy",
                            "discrepancies": verification.get("discrepancies", []),
                            "verification_date": verification.get("verification_date"),
                        }
                    )
                elif verification.get("trades_count", 0) == 0:
                    flagged.append(
                        {
                            "provider_id": provider.id,
                            "user_id": provider.user_id,
                            "reason": "No trades in verification period",
                            "verification_date": verification.get("verification_date"),
                        }
                    )

            return flagged
        except Exception as e:
            logger.error(f"Error flagging suspicious providers: {e}", exc_info=True)
            raise
