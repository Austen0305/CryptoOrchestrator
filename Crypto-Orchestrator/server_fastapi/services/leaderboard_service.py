"""
Leaderboard Service
Calculates and maintains trader leaderboards.
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
import os

from ..models.trade import Trade
from ..models.user import User
from ..services.pnl_service import PnLService

logger = logging.getLogger(__name__)

# Try to import Redis for caching
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class LeaderboardService:
    """Service for trader leaderboards"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.pnl_service = PnLService(db)
        self.redis_client = None
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis client for caching"""
        if REDIS_AVAILABLE:
            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                try:
                    self.redis_client = redis.from_url(redis_url, decode_responses=True)
                    logger.info("Redis initialized for leaderboard caching")
                except Exception as e:
                    logger.warning(f"Redis initialization failed: {e}")

    def _get_cache_key(self, metric: str, period: str, limit: int, mode: str) -> str:
        """Generate cache key for leaderboard"""
        return f"leaderboard:{metric}:{period}:{limit}:{mode}"

    async def _get_from_cache(self, key: str) -> Optional[List[Dict]]:
        """Get leaderboard from cache"""
        if not self.redis_client:
            return None
        try:
            cached = await self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None

    async def _set_cache(self, key: str, value: List[Dict], ttl: int = 300):
        """Set leaderboard in cache"""
        if not self.redis_client:
            return
        try:
            # Cache for 5 minutes (300 seconds) by default
            # Shorter for recent periods, longer for all-time
            if "24h" in key:
                ttl = 60  # 1 minute for 24h
            elif "7d" in key:
                ttl = 300  # 5 minutes for 7d
            elif "30d" in key:
                ttl = 600  # 10 minutes for 30d
            else:
                ttl = 1800  # 30 minutes for all-time

            await self.redis_client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    async def get_leaderboard(
        self,
        metric: str = "total_pnl",
        period: str = "all_time",
        limit: int = 100,
        mode: str = "paper",
    ) -> List[Dict]:
        """
        Get trader leaderboard.

        Args:
            metric: Ranking metric ("total_pnl", "win_rate", "sharpe_ratio", "profit_factor")
            period: Time period ("24h", "7d", "30d", "all_time")
            limit: Number of top traders to return
            mode: Trading mode ("paper" or "real")

        Returns:
            List of trader rankings
        """
        try:
            # Try to get from cache first
            cache_key = self._get_cache_key(metric, period, limit, mode)
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                logger.debug(f"Leaderboard cache hit: {cache_key}")
                return cached_result

            # Calculate period cutoff
            cutoff_date = None
            if period == "24h":
                cutoff_date = datetime.utcnow() - timedelta(hours=24)
            elif period == "7d":
                cutoff_date = datetime.utcnow() - timedelta(days=7)
            elif period == "30d":
                cutoff_date = datetime.utcnow() - timedelta(days=30)

            # Get all users with trades
            users_stmt = select(User.id, User.email, User.username)
            users_result = await self.db.execute(users_stmt)
            users = users_result.all()

            leaderboard = []

            for user_id, email, username in users:
                try:
                    # Calculate metrics for this user
                    if cutoff_date:
                        pnl_result = await self.pnl_service.calculate_portfolio_pnl(
                            user_id,
                            mode,
                            period_hours=None,  # Will filter by date in query
                        )
                    else:
                        pnl_result = await self.pnl_service.calculate_portfolio_pnl(
                            user_id, mode
                        )

                    # Get trade statistics
                    conditions = [
                        Trade.user_id == user_id,
                        Trade.mode == mode,
                        Trade.status == "completed",
                    ]

                    if cutoff_date:
                        conditions.append(Trade.timestamp >= cutoff_date)

                    trades_stmt = select(Trade).where(and_(*conditions))
                    trades_result = await self.db.execute(trades_stmt)
                    trades = trades_result.scalars().all()

                    if not trades:
                        continue

                    # Calculate metrics
                    total_pnl = pnl_result.get("net_pnl", 0.0)
                    total_trades = len(trades)
                    winning_trades = sum(1 for t in trades if (t.pnl or 0) > 0)
                    win_rate = (
                        (winning_trades / total_trades * 100)
                        if total_trades > 0
                        else 0.0
                    )

                    # Calculate profit factor
                    gross_profit = sum(t.pnl for t in trades if (t.pnl or 0) > 0)
                    gross_loss = abs(sum(t.pnl for t in trades if (t.pnl or 0) < 0))
                    profit_factor = (
                        (gross_profit / gross_loss)
                        if gross_loss > 0
                        else (gross_profit if gross_profit > 0 else 0)
                    )

                    # Calculate average win/loss
                    winning_trade_pnls = [t.pnl for t in trades if (t.pnl or 0) > 0]
                    losing_trade_pnls = [t.pnl for t in trades if (t.pnl or 0) < 0]
                    avg_win = (
                        sum(winning_trade_pnls) / len(winning_trade_pnls)
                        if winning_trade_pnls
                        else 0.0
                    )
                    avg_loss = (
                        sum(losing_trade_pnls) / len(losing_trade_pnls)
                        if losing_trade_pnls
                        else 0.0
                    )

                    # Calculate Sharpe ratio (simplified)
                    returns = [(t.pnl or 0) / (t.total or 1) for t in trades if t.total]
                    if returns:
                        import statistics

                        mean_return = statistics.mean(returns) if returns else 0.0
                        std_return = (
                            statistics.stdev(returns) if len(returns) > 1 else 0.0
                        )
                        sharpe_ratio = (
                            (mean_return / std_return) if std_return > 0 else 0.0
                        )
                    else:
                        sharpe_ratio = 0.0

                    leaderboard.append(
                        {
                            "user_id": user_id,
                            "username": username or email or f"User {user_id}",
                            "email": email,
                            "total_pnl": round(total_pnl, 2),
                            "win_rate": round(win_rate, 2),
                            "profit_factor": round(profit_factor, 2),
                            "sharpe_ratio": round(sharpe_ratio, 2),
                            "total_trades": total_trades,
                            "avg_win": round(avg_win, 2),
                            "avg_loss": round(avg_loss, 2),
                        }
                    )

                except Exception as e:
                    logger.warning(f"Error calculating metrics for user {user_id}: {e}")
                    continue

            # Sort by selected metric
            if metric == "total_pnl":
                leaderboard.sort(key=lambda x: x["total_pnl"], reverse=True)
            elif metric == "win_rate":
                leaderboard.sort(key=lambda x: x["win_rate"], reverse=True)
            elif metric == "profit_factor":
                leaderboard.sort(key=lambda x: x["profit_factor"], reverse=True)
            elif metric == "sharpe_ratio":
                leaderboard.sort(key=lambda x: x["sharpe_ratio"], reverse=True)

            # Return top N
            result = leaderboard[:limit]

            # Cache the result
            await self._set_cache(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}", exc_info=True)
            return []

    async def get_user_rank(
        self,
        user_id: int,
        metric: str = "total_pnl",
        period: str = "all_time",
        mode: str = "paper",
    ) -> Optional[Dict]:
        """Get a user's rank on the leaderboard"""
        try:
            leaderboard = await self.get_leaderboard(
                metric, period, limit=1000, mode=mode
            )

            for rank, entry in enumerate(leaderboard, start=1):
                if entry["user_id"] == user_id:
                    return {"rank": rank, **entry}

            return None
        except Exception as e:
            logger.error(f"Error getting user rank: {e}", exc_info=True)
            return None
