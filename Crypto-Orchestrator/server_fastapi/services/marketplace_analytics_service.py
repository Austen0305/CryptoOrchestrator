"""
Marketplace Analytics Service
Provides analytics and metrics for marketplace features.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload

from ..models.signal_provider import SignalProvider, SignalProviderRating, Payout, CuratorStatus
from ..models.indicator import Indicator, IndicatorPurchase, IndicatorRating, IndicatorStatus
from ..models.user import User

logger = logging.getLogger(__name__)


class MarketplaceAnalyticsService:
    """Service for marketplace analytics and metrics"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_marketplace_overview(self) -> Dict[str, Any]:
        """Get overview statistics for both marketplaces"""
        try:
            # Copy Trading Marketplace stats
            copy_trading_stats = await self._get_copy_trading_stats()
            
            # Indicator Marketplace stats
            indicator_stats = await self._get_indicator_stats()
            
            return {
                "copy_trading": copy_trading_stats,
                "indicators": indicator_stats,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting marketplace overview: {e}", exc_info=True)
            raise

    async def _get_copy_trading_stats(self) -> Dict[str, Any]:
        """Get copy trading marketplace statistics"""
        # Total providers
        total_providers_result = await self.db.execute(
            select(func.count(SignalProvider.id))
        )
        total_providers = total_providers_result.scalar() or 0
        
        # Approved providers
        approved_providers_result = await self.db.execute(
            select(func.count(SignalProvider.id)).where(
                SignalProvider.curator_status == CuratorStatus.APPROVED.value
            )
        )
        approved_providers = approved_providers_result.scalar() or 0
        
        # Pending providers
        pending_providers_result = await self.db.execute(
            select(func.count(SignalProvider.id)).where(
                SignalProvider.curator_status == CuratorStatus.PENDING.value
            )
        )
        pending_providers = pending_providers_result.scalar() or 0
        
        # Total ratings
        total_ratings_result = await self.db.execute(
            select(func.count(SignalProviderRating.id))
        )
        total_ratings = total_ratings_result.scalar() or 0
        
        # Average rating
        avg_rating_result = await self.db.execute(
            select(func.avg(SignalProviderRating.rating))
        )
        avg_rating = avg_rating_result.scalar() or 0.0
        
        # Total followers
        total_followers_result = await self.db.execute(
            select(func.sum(SignalProvider.follower_count))
        )
        total_followers = total_followers_result.scalar() or 0
        
        # Total payouts
        total_payouts_result = await self.db.execute(
            select(func.count(Payout.id))
        )
        total_payouts = total_payouts_result.scalar() or 0
        
        # Total payout amount
        total_payout_amount_result = await self.db.execute(
            select(func.sum(Payout.provider_payout))
        )
        total_payout_amount = total_payout_amount_result.scalar() or 0.0
        
        # Platform revenue
        platform_revenue_result = await self.db.execute(
            select(func.sum(Payout.platform_fee))
        )
        platform_revenue = platform_revenue_result.scalar() or 0.0
        
        return {
            "total_providers": total_providers,
            "approved_providers": approved_providers,
            "pending_providers": pending_providers,
            "total_ratings": total_ratings,
            "average_rating": round(avg_rating, 2) if avg_rating else 0.0,
            "total_followers": total_followers,
            "total_payouts": total_payouts,
            "total_payout_amount": round(total_payout_amount, 2),
            "platform_revenue": round(platform_revenue, 2),
        }

    async def _get_indicator_stats(self) -> Dict[str, Any]:
        """Get indicator marketplace statistics"""
        # Total indicators
        total_indicators_result = await self.db.execute(
            select(func.count(Indicator.id))
        )
        total_indicators = total_indicators_result.scalar() or 0
        
        # Approved indicators
        approved_indicators_result = await self.db.execute(
            select(func.count(Indicator.id)).where(
                Indicator.status == IndicatorStatus.APPROVED.value
            )
        )
        approved_indicators = approved_indicators_result.scalar() or 0
        
        # Pending indicators
        pending_indicators_result = await self.db.execute(
            select(func.count(Indicator.id)).where(
                Indicator.status == IndicatorStatus.PENDING.value
            )
        )
        pending_indicators = pending_indicators_result.scalar() or 0
        
        # Free vs Paid
        free_indicators_result = await self.db.execute(
            select(func.count(Indicator.id)).where(Indicator.is_free == True)
        )
        free_indicators = free_indicators_result.scalar() or 0
        
        paid_indicators = total_indicators - free_indicators
        
        # Total purchases
        total_purchases_result = await self.db.execute(
            select(func.count(IndicatorPurchase.id))
        )
        total_purchases = total_purchases_result.scalar() or 0
        
        # Total revenue
        total_revenue_result = await self.db.execute(
            select(func.sum(IndicatorPurchase.purchase_price))
        )
        total_revenue = total_revenue_result.scalar() or 0.0
        
        # Platform revenue (30%)
        platform_revenue = total_revenue * 0.30
        
        # Developer revenue (70%)
        developer_revenue = total_revenue * 0.70
        
        # Total ratings
        total_ratings_result = await self.db.execute(
            select(func.count(IndicatorRating.id))
        )
        total_ratings = total_ratings_result.scalar() or 0
        
        # Average rating
        avg_rating_result = await self.db.execute(
            select(func.avg(IndicatorRating.rating))
        )
        avg_rating = avg_rating_result.scalar() or 0.0
        
        # By category
        category_stats_result = await self.db.execute(
            select(
                Indicator.category,
                func.count(Indicator.id).label("count")
            ).group_by(Indicator.category)
        )
        category_stats = {
            row.category: row.count
            for row in category_stats_result.all()
        }
        
        return {
            "total_indicators": total_indicators,
            "approved_indicators": approved_indicators,
            "pending_indicators": pending_indicators,
            "free_indicators": free_indicators,
            "paid_indicators": paid_indicators,
            "total_purchases": total_purchases,
            "total_revenue": round(total_revenue, 2),
            "platform_revenue": round(platform_revenue, 2),
            "developer_revenue": round(developer_revenue, 2),
            "total_ratings": total_ratings,
            "average_rating": round(avg_rating, 2) if avg_rating else 0.0,
            "by_category": category_stats,
        }

    async def get_top_providers(
        self, limit: int = 10, sort_by: str = "total_return"
    ) -> List[Dict[str, Any]]:
        """Get top performing signal providers"""
        try:
            query = (
                select(SignalProvider)
                .where(
                    and_(
                        SignalProvider.curator_status == CuratorStatus.APPROVED.value,
                        SignalProvider.is_public == True,
                    )
                )
                .options(selectinload(SignalProvider.user))
            )
            
            if sort_by == "total_return":
                query = query.order_by(desc(SignalProvider.total_return))
            elif sort_by == "sharpe_ratio":
                query = query.order_by(desc(SignalProvider.sharpe_ratio))
            elif sort_by == "follower_count":
                query = query.order_by(desc(SignalProvider.follower_count))
            elif sort_by == "rating":
                query = query.order_by(desc(SignalProvider.average_rating))
            
            query = query.limit(limit)
            
            result = await self.db.execute(query)
            providers = result.scalars().all()
            
            return [
                {
                    "id": p.id,
                    "username": p.user.username if p.user else None,
                    "total_return": p.total_return,
                    "sharpe_ratio": p.sharpe_ratio,
                    "win_rate": p.win_rate,
                    "follower_count": p.follower_count,
                    "average_rating": p.average_rating,
                }
                for p in providers
            ]
        except Exception as e:
            logger.error(f"Error getting top providers: {e}", exc_info=True)
            raise

    async def get_top_indicators(
        self, limit: int = 10, sort_by: str = "purchase_count"
    ) -> List[Dict[str, Any]]:
        """Get top performing indicators"""
        try:
            # Get indicators with purchase counts
            query = (
                select(
                    Indicator,
                    func.count(IndicatorPurchase.id).label("purchase_count"),
                    func.avg(IndicatorRating.rating).label("avg_rating"),
                )
                .outerjoin(IndicatorPurchase)
                .outerjoin(IndicatorRating)
                .where(Indicator.status == IndicatorStatus.APPROVED.value)
                .group_by(Indicator.id)
            )
            
            if sort_by == "purchase_count":
                query = query.order_by(desc("purchase_count"))
            elif sort_by == "rating":
                query = query.order_by(desc("avg_rating"))
            elif sort_by == "price":
                query = query.order_by(desc(Indicator.price))
            
            query = query.limit(limit)
            
            result = await self.db.execute(query)
            rows = result.all()
            
            return [
                {
                    "id": row.Indicator.id,
                    "name": row.Indicator.name,
                    "category": row.Indicator.category,
                    "price": row.Indicator.price,
                    "is_free": row.Indicator.is_free,
                    "purchase_count": row.purchase_count or 0,
                    "average_rating": round(row.avg_rating, 2) if row.avg_rating else 0.0,
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error getting top indicators: {e}", exc_info=True)
            raise

    async def get_revenue_trends(
        self, days: int = 30
    ) -> Dict[str, Any]:
        """Get revenue trends over time"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Copy trading payouts
            copy_trading_payouts_result = await self.db.execute(
                select(
                    func.date(Payout.created_at).label("date"),
                    func.sum(Payout.platform_fee).label("platform_revenue"),
                    func.sum(Payout.provider_payout).label("provider_payout"),
                )
                .where(Payout.created_at >= cutoff_date)
                .group_by(func.date(Payout.created_at))
                .order_by("date")
            )
            
            copy_trading_trends = [
                {
                    "date": row.date.isoformat() if row.date else None,
                    "platform_revenue": float(row.platform_revenue or 0),
                    "provider_payout": float(row.provider_payout or 0),
                }
                for row in copy_trading_payouts_result.all()
            ]
            
            # Indicator purchases
            indicator_purchases_result = await self.db.execute(
                select(
                    func.date(IndicatorPurchase.purchased_at).label("date"),
                    func.sum(IndicatorPurchase.purchase_price).label("total_revenue"),
                    func.count(IndicatorPurchase.id).label("purchase_count"),
                )
                .where(IndicatorPurchase.purchased_at >= cutoff_date)
                .group_by(func.date(IndicatorPurchase.purchased_at))
                .order_by("date")
            )
            
            indicator_trends = [
                {
                    "date": row.date.isoformat() if row.date else None,
                    "total_revenue": float(row.total_revenue or 0),
                    "platform_revenue": float(row.total_revenue or 0) * 0.30,
                    "developer_revenue": float(row.total_revenue or 0) * 0.70,
                    "purchase_count": row.purchase_count or 0,
                }
                for row in indicator_purchases_result.all()
            ]
            
            return {
                "copy_trading": copy_trading_trends,
                "indicators": indicator_trends,
                "period_days": days,
            }
        except Exception as e:
            logger.error(f"Error getting revenue trends: {e}", exc_info=True)
            raise

    async def get_developer_analytics(
        self, developer_id: int
    ) -> Dict[str, Any]:
        """Get analytics for a specific developer"""
        try:
            # Get developer's indicators
            indicators_result = await self.db.execute(
                select(Indicator).where(Indicator.developer_id == developer_id)
            )
            indicators = indicators_result.scalars().all()
            
            indicator_ids = [ind.id for ind in indicators]
            
            if not indicator_ids:
                return {
                    "developer_id": developer_id,
                    "total_indicators": 0,
                    "total_purchases": 0,
                    "total_revenue": 0.0,
                    "developer_earnings": 0.0,
                    "average_rating": 0.0,
                    "indicators": [],
                }
            
            # Total purchases
            total_purchases_result = await self.db.execute(
                select(func.count(IndicatorPurchase.id)).where(
                    IndicatorPurchase.indicator_id.in_(indicator_ids)
                )
            )
            total_purchases = total_purchases_result.scalar() or 0
            
            # Total revenue
            total_revenue_result = await self.db.execute(
                select(func.sum(IndicatorPurchase.purchase_price)).where(
                    IndicatorPurchase.indicator_id.in_(indicator_ids)
                )
            )
            total_revenue = total_revenue_result.scalar() or 0.0
            
            # Developer earnings (70%)
            developer_earnings = total_revenue * 0.70
            
            # Average rating
            avg_rating_result = await self.db.execute(
                select(func.avg(IndicatorRating.rating)).where(
                    IndicatorRating.indicator_id.in_(indicator_ids)
                )
            )
            avg_rating = avg_rating_result.scalar() or 0.0
            
            # Per-indicator stats
            indicator_stats = []
            for indicator in indicators:
                purchases_result = await self.db.execute(
                    select(func.count(IndicatorPurchase.id)).where(
                        IndicatorPurchase.indicator_id == indicator.id
                    )
                )
                purchases = purchases_result.scalar() or 0
                
                revenue_result = await self.db.execute(
                    select(func.sum(IndicatorPurchase.purchase_price)).where(
                        IndicatorPurchase.indicator_id == indicator.id
                    )
                )
                revenue = revenue_result.scalar() or 0.0
                
                rating_result = await self.db.execute(
                    select(func.avg(IndicatorRating.rating)).where(
                        IndicatorRating.indicator_id == indicator.id
                    )
                )
                rating = rating_result.scalar() or 0.0
                
                indicator_stats.append({
                    "id": indicator.id,
                    "name": indicator.name,
                    "purchases": purchases,
                    "revenue": round(revenue, 2),
                    "developer_earnings": round(revenue * 0.70, 2),
                    "average_rating": round(rating, 2) if rating else 0.0,
                })
            
            return {
                "developer_id": developer_id,
                "total_indicators": len(indicators),
                "total_purchases": total_purchases,
                "total_revenue": round(total_revenue, 2),
                "developer_earnings": round(developer_earnings, 2),
                "average_rating": round(avg_rating, 2) if avg_rating else 0.0,
                "indicators": indicator_stats,
            }
        except Exception as e:
            logger.error(f"Error getting developer analytics: {e}", exc_info=True)
            raise

    async def get_provider_analytics(
        self, provider_id: int
    ) -> Dict[str, Any]:
        """Get analytics for a specific signal provider"""
        try:
            provider = await self.db.get(SignalProvider, provider_id)
            if not provider:
                raise ValueError("Signal provider not found")
            
            # Get payout history
            payouts_result = await self.db.execute(
                select(Payout)
                .where(Payout.signal_provider_id == provider_id)
                .order_by(desc(Payout.created_at))
                .limit(12)  # Last 12 payouts
            )
            payouts = payouts_result.scalars().all()
            
            # Get ratings
            ratings_result = await self.db.execute(
                select(SignalProviderRating)
                .where(SignalProviderRating.signal_provider_id == provider_id)
                .order_by(desc(SignalProviderRating.created_at))
                .limit(10)  # Last 10 ratings
            )
            ratings = ratings_result.scalars().all()
            
            return {
                "provider_id": provider_id,
                "total_return": provider.total_return,
                "sharpe_ratio": provider.sharpe_ratio,
                "win_rate": provider.win_rate,
                "total_trades": provider.total_trades,
                "follower_count": provider.follower_count,
                "average_rating": provider.average_rating,
                "total_ratings": provider.total_ratings,
                "total_payouts": len(payouts),
                "total_earnings": sum(p.provider_payout for p in payouts),
                "recent_payouts": [
                    {
                        "id": p.id,
                        "period_start": p.period_start.isoformat(),
                        "period_end": p.period_end.isoformat(),
                        "provider_payout": p.provider_payout,
                        "status": p.status,
                    }
                    for p in payouts
                ],
                "recent_ratings": [
                    {
                        "id": r.id,
                        "rating": r.rating,
                        "comment": r.comment,
                        "created_at": r.created_at.isoformat(),
                    }
                    for r in ratings
                ],
            }
        except Exception as e:
            logger.error(f"Error getting provider analytics: {e}", exc_info=True)
            raise
