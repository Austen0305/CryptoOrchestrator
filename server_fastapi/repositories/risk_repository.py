"""
Risk Repository
Data access layer for risk alerts and limits
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.risk_alert import RiskAlert
from ..models.risk_limit import RiskLimit

logger = logging.getLogger(__name__)


class RiskRepository:
    """Repository for risk alerts and limits"""

    def __init__(self):
        # ✅ Repository pattern: No db in __init__, pass session to methods
        pass

    async def create_alert(
        self,
        session: AsyncSession,
        user_id: str,
        alert_type: str,
        severity: str,
        message: str,
        current_value: float | None = None,
        threshold_value: float | None = None,
    ) -> RiskAlert:
        """Create a new risk alert"""
        alert = RiskAlert(
            user_id=user_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            current_value=current_value,
            threshold_value=threshold_value,
            acknowledged=False,
            resolved=False,
        )
        session.add(alert)
        await session.commit()
        await session.refresh(alert)
        return alert

    async def get_user_alerts(
        self,
        session: AsyncSession,
        user_id: str,
        resolved: bool | None = None,
        acknowledged: bool | None = None,
        limit: int | None = None,
    ) -> list[RiskAlert]:
        """Get risk alerts for a user with eager loading"""
        stmt = select(RiskAlert).where(RiskAlert.user_id == user_id)

        if resolved is not None:
            stmt = stmt.where(RiskAlert.resolved.is_(resolved))
        if acknowledged is not None:
            stmt = stmt.where(RiskAlert.acknowledged.is_(acknowledged))

        stmt = stmt.order_by(RiskAlert.created_at.desc())

        if limit:
            stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def acknowledge_alert(
        self, session: AsyncSession, alert_id: int
    ) -> RiskAlert | None:
        """Acknowledge a risk alert"""
        stmt = (
            update(RiskAlert)
            .where(RiskAlert.id == alert_id)
            .values(acknowledged=True, acknowledged_at=datetime.now(UTC))
        )
        await session.execute(stmt)
        await session.commit()

        stmt = select(RiskAlert).where(RiskAlert.id == alert_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def resolve_alert(
        self, session: AsyncSession, alert_id: int
    ) -> RiskAlert | None:
        """Resolve a risk alert"""
        stmt = (
            update(RiskAlert)
            .where(RiskAlert.id == alert_id)
            .values(resolved=True, resolved_at=datetime.now(UTC))
        )
        await session.execute(stmt)
        await session.commit()

        stmt = select(RiskAlert).where(RiskAlert.id == alert_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_limits(
        self, session: AsyncSession, user_id: str
    ) -> list[RiskLimit]:
        """Get risk limits for a user"""
        stmt = (
            select(RiskLimit)
            .where(RiskLimit.user_id == user_id)
            .where(RiskLimit.enabled.is_(True))
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create_or_update_limit(
        self,
        session: AsyncSession,
        user_id: str,
        limit_type: str,
        value: float,
        enabled: bool = True,
    ) -> RiskLimit:
        """Create or update a risk limit"""
        # Check if limit exists
        stmt = select(RiskLimit).where(
            and_(RiskLimit.user_id == user_id, RiskLimit.limit_type == limit_type)
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.value = value
            existing.enabled = enabled
            await session.commit()
            await session.refresh(existing)
            return existing
        else:
            limit = RiskLimit(
                user_id=user_id,
                limit_type=limit_type,
                value=value,
                enabled=enabled,
            )
            session.add(limit)
            await session.commit()
            await session.refresh(limit)
            return limit

    async def get_alert_by_id(
        self, session: AsyncSession, alert_id: int
    ) -> RiskAlert | None:
        """Get risk alert by ID"""
        # Note: RiskAlert doesn't have is_deleted (inherits from Base, TimestampMixin only)
        stmt = select(RiskAlert).where(RiskAlert.id == alert_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_limit_by_user_and_type(
        self, session: AsyncSession, user_id: str, limit_type: str
    ) -> RiskLimit | None:
        """Get a specific risk limit by user and type"""
        stmt = select(RiskLimit).where(
            and_(RiskLimit.user_id == user_id, RiskLimit.limit_type == limit_type)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
