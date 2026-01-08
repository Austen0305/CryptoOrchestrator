"""
Marketplace Service
Manages signal providers, curator system, reputation, and payouts for copy trading marketplace.
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:
    from ..models.follow import Follow
    from ..models.signal_provider import Payout, SignalProvider, SignalProviderRating
    from ..models.trade import Trade

from ..models.follow import Follow
from ..models.signal_provider import (
    CuratorStatus,
    Payout,
    SignalProvider,
    SignalProviderRating,
)
from ..models.trade import Trade
from ..repositories.follow_repository import FollowRepository
from ..repositories.trade_repository import TradeRepository
from ..repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class MarketplaceService:
    """Service for marketplace functionality"""

    def __init__(
        self,
        db: AsyncSession,
        user_repository: UserRepository | None = None,
        trade_repository: TradeRepository | None = None,
        follow_repository: FollowRepository | None = None,
    ):
        self.db = db
        self.user_repository = user_repository or UserRepository()
        self.trade_repository = trade_repository or TradeRepository()
        self.follow_repository = follow_repository or FollowRepository()

    async def apply_as_signal_provider(
        self, user_id: int, profile_description: str | None = None
    ) -> dict[str, any]:
        """
        Apply to become a signal provider (curator approval required).

        Args:
            user_id: User ID applying
            profile_description: Optional profile description

        Returns:
            Dict with application details
        """
        try:
            # Check if already exists
            existing = await self.db.execute(
                select(SignalProvider).where(SignalProvider.user_id == user_id)
            )
            signal_provider = existing.scalar_one_or_none()

            if signal_provider:
                if signal_provider.curator_status == CuratorStatus.APPROVED.value:
                    raise ValueError("Already an approved signal provider")
                elif signal_provider.curator_status == CuratorStatus.PENDING.value:
                    raise ValueError("Application already pending")
                # If rejected or suspended, allow re-application
                signal_provider.curator_status = CuratorStatus.PENDING.value
                if profile_description:
                    signal_provider.profile_description = profile_description
            else:
                # Create new application
                signal_provider = SignalProvider(
                    user_id=user_id,
                    curator_status=CuratorStatus.PENDING.value,
                    profile_description=profile_description,
                    is_public=False,
                )
                self.db.add(signal_provider)

            await self.db.commit()
            await self.db.refresh(signal_provider)

            # Send email notification (async, don't wait)
            try:
                from ..models.user import User
                from ..services.marketplace_email_service import MarketplaceEmailService

                user = await self.db.get(User, user_id)
                if user and user.email:
                    email_service = MarketplaceEmailService()
                    # Fire and forget
                    import asyncio

                    asyncio.create_task(
                        email_service.send_provider_approval_email(
                            user.email, user.username or user.email
                        )
                        if signal_provider.curator_status
                        == CuratorStatus.APPROVED.value
                        else email_service.send_provider_rejection_email(
                            user.email, user.username or user.email
                        )
                    )
            except Exception as e:
                logger.warning(f"Failed to send email notification: {e}")

            return {
                "id": signal_provider.id,
                "user_id": user_id,
                "status": signal_provider.curator_status,
                "message": "Application submitted for curator review",
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error applying as signal provider: {e}", exc_info=True)
            await self.db.rollback()
            raise

    async def approve_signal_provider(
        self, signal_provider_id: int, curator_notes: str | None = None
    ) -> dict[str, any]:
        """
        Approve a signal provider (curator action).

        Args:
            signal_provider_id: Signal provider ID to approve
            curator_notes: Optional notes from curator

        Returns:
            Dict with approval details
        """
        try:
            signal_provider = await self.db.get(SignalProvider, signal_provider_id)
            if not signal_provider:
                raise ValueError("Signal provider not found")

            signal_provider.curator_status = CuratorStatus.APPROVED.value
            signal_provider.curator_approved_at = datetime.utcnow()
            if curator_notes:
                signal_provider.curator_notes = curator_notes
            signal_provider.is_public = True  # Make public upon approval

            await self.db.commit()
            await self.db.refresh(signal_provider)

            # Send approval email notification
            try:
                from ..models.user import User
                from ..services.marketplace_email_service import MarketplaceEmailService

                user = await self.db.get(User, signal_provider.user_id)
                if user and user.email:
                    email_service = MarketplaceEmailService()
                    import asyncio

                    asyncio.create_task(
                        email_service.send_provider_approval_email(
                            user.email, user.username or user.email
                        )
                    )
            except Exception as e:
                logger.warning(f"Failed to send approval email: {e}")

            return {
                "id": signal_provider.id,
                "user_id": signal_provider.user_id,
                "status": signal_provider.curator_status,
                "approved_at": signal_provider.curator_approved_at.isoformat(),
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error approving signal provider: {e}", exc_info=True)
            await self.db.rollback()
            raise

    async def update_performance_metrics(
        self, signal_provider_id: int
    ) -> dict[str, any]:
        """
        Update performance metrics for a signal provider.
        Calculates Sharpe ratio, win rate, total return, etc.

        Args:
            signal_provider_id: Signal provider ID

        Returns:
            Dict with updated metrics
        """
        try:
            signal_provider = await self.db.get(SignalProvider, signal_provider_id)
            if not signal_provider:
                raise ValueError("Signal provider not found")

            # Get all completed trades for this user
            trades_result = await self.db.execute(
                select(Trade)
                .where(
                    and_(
                        Trade.user_id == signal_provider.user_id,
                        Trade.status == "completed",
                    )
                )
                .order_by(Trade.created_at)
            )
            trades = trades_result.scalars().all()

            if not trades:
                # No trades, reset metrics
                signal_provider.total_trades = 0
                signal_provider.winning_trades = 0
                signal_provider.win_rate = 0.0
                signal_provider.total_profit = 0.0
                signal_provider.total_return = 0.0
                signal_provider.sharpe_ratio = 0.0
                signal_provider.profit_factor = 0.0
                signal_provider.max_drawdown = 0.0
            else:
                # Calculate metrics
                winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
                losing_trades = [t for t in trades if t.pnl and t.pnl < 0]

                signal_provider.total_trades = len(trades)
                signal_provider.winning_trades = len(winning_trades)
                signal_provider.win_rate = (
                    len(winning_trades) / len(trades) if trades else 0.0
                )

                total_profit = sum(t.pnl for t in trades if t.pnl)
                signal_provider.total_profit = total_profit

                # Calculate total return (assuming initial capital from first trade)
                if trades:
                    # Estimate initial capital from first trade
                    first_trade = trades[0]
                    if first_trade.total:
                        initial_capital = abs(first_trade.total) * 10  # Rough estimate
                    else:
                        initial_capital = 10000  # Default
                    signal_provider.total_return = (
                        (total_profit / initial_capital * 100)
                        if initial_capital > 0
                        else 0.0
                    )

                # Calculate Sharpe ratio
                if len(trades) > 1:
                    returns = [t.pnl for t in trades if t.pnl]
                    if returns:
                        avg_return = sum(returns) / len(returns)
                        variance = sum((r - avg_return) ** 2 for r in returns) / len(
                            returns
                        )
                        std_dev = variance**0.5 if variance > 0 else 0.0
                        signal_provider.sharpe_ratio = (
                            (avg_return / std_dev * (365**0.5)) if std_dev > 0 else 0.0
                        )

                # Calculate profit factor
                gross_profit = sum(t.pnl for t in winning_trades if t.pnl)
                gross_loss = abs(sum(t.pnl for t in losing_trades if t.pnl))
                signal_provider.profit_factor = (
                    gross_profit / gross_loss if gross_loss > 0 else 0.0
                )

                # Calculate max drawdown
                equity_curve = []
                running_balance = initial_capital
                peak = initial_capital
                max_dd = 0.0

                for trade in trades:
                    if trade.pnl:
                        running_balance += trade.pnl
                        if running_balance > peak:
                            peak = running_balance
                        drawdown = (peak - running_balance) / peak if peak > 0 else 0.0
                        max_dd = max(max_dd, drawdown)

                signal_provider.max_drawdown = max_dd * 100  # As percentage

            # Update follower count
            follows_result = await self.db.execute(
                select(func.count(Follow.id)).where(
                    and_(
                        Follow.trader_id == signal_provider.user_id,
                        Follow.is_active == True,
                    )
                )
            )
            signal_provider.follower_count = follows_result.scalar() or 0

            signal_provider.last_metrics_update = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(signal_provider)

            return {
                "total_trades": signal_provider.total_trades,
                "win_rate": signal_provider.win_rate,
                "total_return": signal_provider.total_return,
                "sharpe_ratio": signal_provider.sharpe_ratio,
                "profit_factor": signal_provider.profit_factor,
                "max_drawdown": signal_provider.max_drawdown,
                "follower_count": signal_provider.follower_count,
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}", exc_info=True)
            await self.db.rollback()
            raise

    async def rate_signal_provider(
        self,
        signal_provider_id: int,
        user_id: int,
        rating: int,
        comment: str | None = None,
    ) -> dict[str, any]:
        """
        Rate a signal provider (1-5 stars).

        Args:
            signal_provider_id: Signal provider ID
            user_id: User ID rating
            rating: Rating (1-5)
            comment: Optional comment

        Returns:
            Dict with rating details
        """
        try:
            if rating < 1 or rating > 5:
                raise ValueError("Rating must be between 1 and 5")

            # Check if already rated
            existing_result = await self.db.execute(
                select(SignalProviderRating).where(
                    and_(
                        SignalProviderRating.signal_provider_id == signal_provider_id,
                        SignalProviderRating.user_id == user_id,
                    )
                )
            )
            existing_rating = existing_result.scalar_one_or_none()

            if existing_rating:
                existing_rating.rating = rating
                if comment:
                    existing_rating.comment = comment
                rating_obj = existing_rating
            else:
                rating_obj = SignalProviderRating(
                    signal_provider_id=signal_provider_id,
                    user_id=user_id,
                    rating=rating,
                    comment=comment,
                )
                self.db.add(rating_obj)

            await self.db.commit()
            await self.db.refresh(rating_obj)

            # Update average rating
            await self._update_average_rating(signal_provider_id)

            return {
                "id": rating_obj.id,
                "signal_provider_id": signal_provider_id,
                "rating": rating,
                "comment": comment,
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error rating signal provider: {e}", exc_info=True)
            await self.db.rollback()
            raise

    async def _update_average_rating(self, signal_provider_id: int) -> None:
        """Update average rating for a signal provider"""
        try:
            ratings_result = await self.db.execute(
                select(
                    func.avg(SignalProviderRating.rating),
                    func.count(SignalProviderRating.id),
                ).where(SignalProviderRating.signal_provider_id == signal_provider_id)
            )
            result = ratings_result.first()

            if result and result[0]:
                signal_provider = await self.db.get(SignalProvider, signal_provider_id)
                if signal_provider:
                    signal_provider.average_rating = round(float(result[0]), 2)
                    signal_provider.total_ratings = result[1] or 0
                    await self.db.commit()
        except Exception as e:
            logger.error(f"Error updating average rating: {e}", exc_info=True)

    async def get_marketplace_traders(
        self,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "total_return",
        min_rating: float | None = None,
        min_win_rate: float | None = None,
        min_sharpe: float | None = None,
    ) -> dict[str, any]:
        """
        Get list of signal providers for marketplace (public, approved only).

        Args:
            skip: Pagination offset
            limit: Pagination limit
            sort_by: Sort field (total_return, sharpe_ratio, win_rate, follower_count, rating)
            min_rating: Minimum average rating filter
            min_win_rate: Minimum win rate filter
            min_sharpe: Minimum Sharpe ratio filter

        Returns:
            Dict with traders list and pagination info
        """
        try:
            # Optimized query with eager loading and filtering
            query = (
                select(SignalProvider)
                .options(
                    selectinload(SignalProvider.user)
                )  # Eager load user to prevent N+1
                .where(
                    and_(
                        SignalProvider.curator_status == CuratorStatus.APPROVED.value,
                        SignalProvider.is_public == True,
                    )
                )
                .options(selectinload(SignalProvider.user))
            )

            # Apply filters
            if min_rating is not None:
                query = query.where(SignalProvider.average_rating >= min_rating)
            if min_win_rate is not None:
                query = query.where(SignalProvider.win_rate >= min_win_rate)
            if min_sharpe is not None:
                query = query.where(SignalProvider.sharpe_ratio >= min_sharpe)

            # Apply sorting
            if sort_by == "total_return":
                query = query.order_by(desc(SignalProvider.total_return))
            elif sort_by == "sharpe_ratio":
                query = query.order_by(desc(SignalProvider.sharpe_ratio))
            elif sort_by == "win_rate":
                query = query.order_by(desc(SignalProvider.win_rate))
            elif sort_by == "follower_count":
                query = query.order_by(desc(SignalProvider.follower_count))
            elif sort_by == "rating":
                query = query.order_by(desc(SignalProvider.average_rating))
            else:
                query = query.order_by(desc(SignalProvider.total_return))

            # Get total count (optimized - reuse filter conditions)
            count_conditions = [
                SignalProvider.curator_status == CuratorStatus.APPROVED.value,
                SignalProvider.is_public == True,
            ]
            if min_rating is not None:
                count_conditions.append(SignalProvider.average_rating >= min_rating)
            if min_win_rate is not None:
                count_conditions.append(SignalProvider.win_rate >= min_win_rate)
            if min_sharpe is not None:
                count_conditions.append(SignalProvider.sharpe_ratio >= min_sharpe)

            count_query = select(func.count(SignalProvider.id)).where(
                and_(*count_conditions)
            )
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0

            # Apply pagination
            query = query.offset(skip).limit(limit)

            result = await self.db.execute(query)
            signal_providers = result.scalars().all()

            traders = []
            for sp in signal_providers:
                user = sp.user
                traders.append(
                    {
                        "id": sp.id,
                        "user_id": sp.user_id,
                        "username": user.username or user.email if user else None,
                        "profile_description": sp.profile_description,
                        "trading_strategy": sp.trading_strategy,
                        "risk_level": sp.risk_level,
                        "total_return": sp.total_return,
                        "sharpe_ratio": sp.sharpe_ratio,
                        "win_rate": sp.win_rate,
                        "total_trades": sp.total_trades,
                        "follower_count": sp.follower_count,
                        "average_rating": sp.average_rating,
                        "total_ratings": sp.total_ratings,
                        "subscription_fee": sp.subscription_fee,
                        "performance_fee_percentage": sp.performance_fee_percentage,
                        "curator_status": sp.curator_status,
                        "last_metrics_update": (
                            sp.last_metrics_update.isoformat()
                            if sp.last_metrics_update
                            else None
                        ),
                    }
                )

            return {
                "traders": traders,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"Error getting marketplace traders: {e}", exc_info=True)
            return {"traders": [], "total": 0, "skip": skip, "limit": limit}

    async def calculate_payout(
        self, signal_provider_id: int, period_start: datetime, period_end: datetime
    ) -> dict[str, any]:
        """
        Calculate payout for a signal provider for a given period.
        Platform takes 20%, provider gets 80%.

        Args:
            signal_provider_id: Signal provider ID
            period_start: Period start date
            period_end: Period end date

        Returns:
            Dict with payout calculation
        """
        try:
            signal_provider = await self.db.get(SignalProvider, signal_provider_id)
            if not signal_provider:
                raise ValueError("Signal provider not found")

            # Get all active followers during this period
            follows_result = await self.db.execute(
                select(Follow).where(
                    and_(
                        Follow.trader_id == signal_provider.user_id,
                        Follow.is_active == True,
                    )
                )
            )
            follows = follows_result.scalars().all()

            # Calculate revenue from subscription fees
            subscription_revenue = 0.0
            if signal_provider.subscription_fee:
                subscription_revenue = (
                    len(follows) * signal_provider.subscription_fee
                )  # Monthly fee per follower

            # Calculate performance fees (80/20 split)
            # Get copied trades in this period
            from ..models.follow import CopiedTrade

            copied_trades_result = await self.db.execute(
                select(CopiedTrade)
                .where(
                    and_(
                        CopiedTrade.trader_id == signal_provider.user_id,
                        CopiedTrade.created_at >= period_start,
                        CopiedTrade.created_at <= period_end,
                        CopiedTrade.status == "executed",
                    )
                )
                .options(selectinload(CopiedTrade.copied_trade))
            )
            copied_trades = copied_trades_result.scalars().all()

            performance_revenue = 0.0
            for copied_trade in copied_trades:
                if copied_trade.copied_trade and copied_trade.copied_trade.pnl:
                    # Calculate fee based on profit
                    profit = copied_trade.copied_trade.pnl
                    if profit > 0 and signal_provider.performance_fee_percentage > 0:
                        fee = profit * (
                            signal_provider.performance_fee_percentage / 100.0
                        )
                        performance_revenue += fee

            total_revenue = subscription_revenue + performance_revenue
            platform_fee = total_revenue * 0.20  # 20% to platform
            provider_payout = total_revenue * 0.80  # 80% to provider

            return {
                "signal_provider_id": signal_provider_id,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "subscription_revenue": round(subscription_revenue, 2),
                "performance_revenue": round(performance_revenue, 2),
                "total_revenue": round(total_revenue, 2),
                "platform_fee": round(platform_fee, 2),
                "provider_payout": round(provider_payout, 2),
                "active_followers": len(follows),
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error calculating payout: {e}", exc_info=True)
            raise

    async def create_payout(
        self, signal_provider_id: int, period_start: datetime, period_end: datetime
    ) -> dict[str, any]:
        """
        Create a payout record for a signal provider.

        Args:
            signal_provider_id: Signal provider ID
            period_start: Period start date
            period_end: Period end date

        Returns:
            Dict with payout details
        """
        try:
            # Calculate payout
            payout_calc = await self.calculate_payout(
                signal_provider_id, period_start, period_end
            )

            # Create payout record
            payout = Payout(
                signal_provider_id=signal_provider_id,
                period_start=period_start,
                period_end=period_end,
                total_revenue=payout_calc["total_revenue"],
                platform_fee=payout_calc["platform_fee"],
                provider_payout=payout_calc["provider_payout"],
                status="pending",
            )

            self.db.add(payout)
            await self.db.commit()
            await self.db.refresh(payout)

            # Send payout notification email
            try:
                from ..models.user import User
                from ..services.marketplace_email_service import MarketplaceEmailService

                user = await self.db.get(User, signal_provider.user_id)
                if user and user.email:
                    email_service = MarketplaceEmailService()
                    import asyncio

                    asyncio.create_task(
                        email_service.send_payout_notification_email(
                            to_email=user.email,
                            provider_name=user.username or user.email,
                            payout_amount=payout.provider_payout,
                            period_start=period_start,
                            period_end=period_end,
                        )
                    )
            except Exception as e:
                logger.warning(f"Failed to send payout notification email: {e}")

            return {
                "id": payout.id,
                "signal_provider_id": signal_provider_id,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "total_revenue": payout.total_revenue,
                "platform_fee": payout.platform_fee,
                "provider_payout": payout.provider_payout,
                "status": payout.status,
            }
        except Exception as e:
            logger.error(f"Error creating payout: {e}", exc_info=True)
            await self.db.rollback()
            raise
