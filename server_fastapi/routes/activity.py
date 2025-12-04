"""
Activity Routes - Recent activity tracking
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from ..dependencies.auth import get_current_user

# Import cache utilities
try:
    from ..middleware.query_cache import cache_query_result

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

    def cache_query_result(*args, **kwargs):
        """Fallback no-op decorator when cache not available"""

        def decorator(func):
            return func

        return decorator


logger = logging.getLogger(__name__)

router = APIRouter()


class ActivityItem(BaseModel):
    """Activity item model"""

    id: str
    type: str  # "trade" | "bot" | "alert" | "system"
    message: str
    timestamp: str
    status: Optional[str] = None  # "success" | "warning" | "error"


@router.get("/recent")
@cache_query_result(
    ttl=30, key_prefix="activity_recent", include_user=True, include_params=True
)
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=100), current_user: dict = Depends(get_current_user)
) -> List[ActivityItem]:
    """
    Get recent activity for the current user.

    Returns a list of recent activities including:
    - Trades (buy/sell orders)
    - Bot events (start/stop/status changes)
    - System alerts
    - Risk warnings
    """
    try:
        user_id = current_user.get("id") or current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            logger.warning(f"User ID not found in current_user: {current_user}")
            return []

        # Import repositories
        from ..database import get_db_context
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select, desc
        from ..models.trade import Trade
        from ..models.bot import Bot
        from ..models.risk_alert import RiskAlert

        activities: List[ActivityItem] = []

        async with get_db_context() as db:
            # Get recent trades
            trades_result = await db.execute(
                select(Trade)
                .where(Trade.user_id == str(user_id))
                .order_by(desc(Trade.created_at))
                .limit(limit // 2)
            )
            trades = trades_result.scalars().all()

            for trade in trades:
                side_label = "Buy" if trade.side == "buy" else "Sell"
                activities.append(
                    ActivityItem(
                        id=f"trade-{trade.id}",
                        type="trade",
                        message=f"{side_label} {trade.amount} {trade.pair} @ ${trade.price:.2f}",
                        timestamp=(
                            trade.created_at.isoformat()
                            if hasattr(trade.created_at, "isoformat")
                            else str(trade.created_at)
                        ),
                        status="success" if trade.success else "error",
                    )
                )

            # Get recent bot events
            bots_result = await db.execute(
                select(Bot)
                .where(Bot.user_id == str(user_id))
                .order_by(desc(Bot.updated_at))
                .limit(limit // 4)
            )
            bots = bots_result.scalars().all()

            for bot in bots:
                activities.append(
                    ActivityItem(
                        id=f"bot-{bot.id}",
                        type="bot",
                        message=f"Bot '{bot.name}' status: {bot.status}",
                        timestamp=(
                            bot.updated_at.isoformat()
                            if hasattr(bot.updated_at, "isoformat")
                            else str(bot.updated_at)
                        ),
                        status="success" if bot.status == "active" else "warning",
                    )
                )

            # Get recent risk alerts
            alerts_result = await db.execute(
                select(RiskAlert)
                .where(RiskAlert.user_id == str(user_id))
                .order_by(desc(RiskAlert.created_at))
                .limit(limit // 4)
            )
            alerts = alerts_result.scalars().all()

            for alert in alerts:
                activities.append(
                    ActivityItem(
                        id=f"alert-{alert.id}",
                        type="alert",
                        message=f"Risk Alert: {alert.alert_type} - {alert.message}",
                        timestamp=(
                            alert.created_at.isoformat()
                            if hasattr(alert.created_at, "isoformat")
                            else str(alert.created_at)
                        ),
                        status=(
                            "warning"
                            if alert.severity == "medium"
                            else "error" if alert.severity == "high" else "success"
                        ),
                    )
                )

        # Sort by timestamp (most recent first) and limit
        activities.sort(key=lambda x: x.timestamp, reverse=True)
        return activities[:limit]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recent activity: {e}", exc_info=True)
        # Return empty activity list instead of 500 error for better UX during development
        logger.warning(f"Returning empty activity list due to error: {e}")
        return []
