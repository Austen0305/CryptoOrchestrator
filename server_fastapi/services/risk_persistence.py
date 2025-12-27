"""
Risk Persistence Service
Handles persistence of risk limits, metrics, and alerts to database.
"""

import logging
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..repositories.risk_repository import RiskRepository, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.risk_limit import RiskLimit
from ..models.risk_alert import RiskAlert as RiskAlertModel
from ..repositories.risk_repository import RiskRepository

logger = logging.getLogger(__name__)


class RiskPersistenceService:
    """Service for persisting risk management data to database"""

    def __init__(
        self,
        db_session: AsyncSession,
        risk_repository: Optional[RiskRepository] = None,
    ):
        # ✅ Repository injected via dependency injection (Service Layer Pattern)
        self.risk_repository = risk_repository or RiskRepository()
        self.db = db_session  # Keep db for transaction handling

    async def save_risk_limits(
        self, user_id: str, limits: Dict[str, float]
    ) -> List[RiskLimit]:
        """
        Save or update risk limits for a user.

        Args:
            user_id: User ID
            limits: Dictionary of limit_type -> value mappings

        Returns:
            List of saved/updated RiskLimit objects
        """
        saved_limits = []

        # ✅ Data access delegated to repository
        for limit_type, value in limits.items():
            limit = await self.risk_repository.create_or_update_limit(
                self.db,
                user_id=user_id,
                limit_type=limit_type,
                value=value,
                enabled=True,
            )
            saved_limits.append(limit)

        logger.info(
            f"Saved {len(saved_limits)} risk limits for user {user_id}",
            extra={"user_id": user_id, "limit_count": len(saved_limits)},
        )
        return saved_limits

    async def get_risk_limits(self, user_id: str) -> Dict[str, float]:
        """
        Get all risk limits for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary of limit_type -> value mappings
        """
        # ✅ Data access delegated to repository
        limits = await self.risk_repository.get_user_limits(self.db, user_id)
        return {limit.limit_type: limit.value for limit in limits}

    async def disable_risk_limit(
        self, user_id: str, limit_type: str
    ) -> Optional[RiskLimit]:
        """
        Disable a risk limit for a user.

        Args:
            user_id: User ID
            limit_type: Type of limit to disable

        Returns:
            Updated RiskLimit object or None if not found
        """
        # ✅ Data access delegated to repository
        limit = await self.risk_repository.create_or_update_limit(
            self.db,
            user_id=user_id,
            limit_type=limit_type,
            value=0.0,  # Value doesn't matter when disabling
            enabled=False,
        )
        if limit:
            logger.info(
                f"Disabled risk limit {limit_type} for user {user_id}",
                extra={"user_id": user_id, "limit_type": limit_type},
            )
        return limit

    async def save_risk_metrics(self, user_id: str, metrics: Dict[str, Any]) -> None:
        """
        Save risk metrics snapshot for a user.
        This could be stored in a separate RiskMetrics table or as part of portfolio.

        Args:
            user_id: User ID
            metrics: Dictionary of metric_name -> value mappings
        """
        # For now, log metrics (could be stored in database if needed)
        logger.info(
            f"Risk metrics for user {user_id}: {metrics}",
            extra={"user_id": user_id, "metrics": metrics},
        )

        # TODO: Store in RiskMetrics table if needed for historical tracking

    async def get_risk_history(
        self, user_id: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get risk history (alerts, limit changes) for a user.

        Args:
            user_id: User ID
            days: Number of days of history to retrieve

        Returns:
            List of risk history entries
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # ✅ Data access delegated to repository
        # Get all alerts and filter by date (repository doesn't support date filtering yet)
        alerts = await self.risk_repository.get_user_alerts(
            self.db,
            user_id=user_id,
            resolved=None,
            acknowledged=None,
            limit=None,  # Get all alerts
        )

        # Filter by date
        alerts = [a for a in alerts if a.created_at >= cutoff_date]

        history = []
        for alert in alerts:
            history.append(
                {
                    "type": "alert",
                    "timestamp": alert.created_at.isoformat(),
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "acknowledged": alert.acknowledged,
                }
            )

        # Get limit changes (would need a RiskLimitHistory table for full tracking)
        # For now, just return alerts

        return history

    async def persist_risk_state(self, user_id: str, state: Dict[str, Any]) -> None:
        """
        Persist complete risk state for a user (limits, metrics, alerts).

        Args:
            user_id: User ID
            state: Complete risk state dictionary
        """
        # Save limits
        if "limits" in state:
            await self.save_risk_limits(user_id, state["limits"])

        # Save metrics
        if "metrics" in state:
            await self.save_risk_metrics(user_id, state["metrics"])

        logger.info(f"Persisted risk state for user {user_id}")
