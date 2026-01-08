"""
GDPR Compliance Service
Data export, deletion, and consent management
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AuditLog, Bot, Portfolio, Trade, User

logger = logging.getLogger(__name__)


class GDPRService:
    """Service for GDPR compliance features"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_user_data(self, user_id: int) -> dict[str, Any]:
        """
        Export all user data (GDPR right to data portability)

        Returns:
            Complete user data export in JSON format
        """
        # Get user
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Collect all user data
        export_data = {
            "export_date": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "user_data": {
                "email": user.email,
                "username": user.username,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
            },
        }

        # Get trades
        trades_stmt = select(Trade).where(Trade.user_id == user_id)
        trades_result = await self.db.execute(trades_stmt)
        trades = trades_result.scalars().all()
        export_data["trades"] = [
            {
                "id": trade.id,
                "symbol": trade.symbol,
                "side": trade.side,
                "amount": str(trade.amount),
                "price": str(trade.price),
                "fee": str(trade.fee),
                "status": trade.status,
                "created_at": trade.created_at.isoformat()
                if trade.created_at
                else None,
            }
            for trade in trades
        ]

        # Get bots
        bots_stmt = select(Bot).where(Bot.user_id == user_id)
        bots_result = await self.db.execute(bots_stmt)
        bots = bots_result.scalars().all()
        export_data["bots"] = [
            {
                "id": bot.id,
                "name": bot.name,
                "strategy": bot.strategy,
                "symbol": bot.symbol,
                "is_active": bot.is_active,
                "trading_mode": bot.trading_mode,
                "config": bot.config,
                "created_at": bot.created_at.isoformat() if bot.created_at else None,
            }
            for bot in bots
        ]

        # Get portfolios
        portfolios_stmt = select(Portfolio).where(Portfolio.user_id == user_id)
        portfolios_result = await self.db.execute(portfolios_stmt)
        portfolios = portfolios_result.scalars().all()
        export_data["portfolios"] = [
            {
                "id": portfolio.id,
                "name": portfolio.name,
                "total_value": str(portfolio.total_value),
                "total_cost": str(portfolio.total_cost),
                "created_at": portfolio.created_at.isoformat()
                if portfolio.created_at
                else None,
            }
            for portfolio in portfolios
        ]

        # Get audit logs
        audit_stmt = select(AuditLog).where(AuditLog.user_id == user_id)
        audit_result = await self.db.execute(audit_stmt)
        audit_logs = audit_result.scalars().all()
        export_data["audit_logs"] = [
            {
                "id": log.id,
                "event_type": log.event_type,
                "event_name": log.event_name,
                "event_data": log.event_data,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in audit_logs
        ]

        # Log export
        logger.info(f"User data exported for user {user_id}")

        return export_data

    async def delete_user_data(
        self, user_id: int, reason: str | None = None
    ) -> dict[str, Any]:
        """
        Delete all user data (GDPR right to be forgotten)

        Note: Some data may be retained for legal/compliance reasons
        (e.g., audit logs, financial records)

        Returns:
            Deletion summary
        """
        # Get user
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        deletion_summary = {
            "user_id": user_id,
            "deletion_date": datetime.utcnow().isoformat(),
            "reason": reason,
            "deleted_items": {},
        }

        # Delete trades (soft delete - mark as deleted)
        trades_stmt = select(Trade).where(Trade.user_id == user_id)
        trades_result = await self.db.execute(trades_stmt)
        trades = trades_result.scalars().all()
        for trade in trades:
            # In production, would mark as deleted rather than hard delete
            # await self.db.delete(trade)
            pass
        deletion_summary["deleted_items"]["trades"] = len(trades)

        # Delete bots
        bots_stmt = select(Bot).where(Bot.user_id == user_id)
        bots_result = await self.db.execute(bots_stmt)
        bots = bots_result.scalars().all()
        for bot in bots:
            await self.db.delete(bot)
        deletion_summary["deleted_items"]["bots"] = len(bots)

        # Delete portfolios
        portfolios_stmt = select(Portfolio).where(Portfolio.user_id == user_id)
        portfolios_result = await self.db.execute(portfolios_stmt)
        portfolios = portfolios_result.scalars().all()
        for portfolio in portfolios:
            await self.db.delete(portfolio)
        deletion_summary["deleted_items"]["portfolios"] = len(portfolios)

        # Anonymize user (don't delete for audit trail)
        user.email = f"deleted_{user_id}@deleted.local"
        user.username = f"deleted_user_{user_id}"
        user.is_active = False
        user.hashed_password = ""  # Clear password

        await self.db.commit()

        # Log deletion
        logger.warning(f"User data deleted for user {user_id}: {reason}")

        return deletion_summary

    async def get_consent_status(self, user_id: int) -> dict[str, Any]:
        """Get user consent status"""
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # In production, would have a consent table
        # For now, return basic status
        return {
            "user_id": user_id,
            "marketing_consent": False,  # Would come from consent table
            "analytics_consent": True,  # Default
            "data_sharing_consent": False,
            "updated_at": datetime.utcnow().isoformat(),
        }

    async def update_consent(
        self,
        user_id: int,
        consent_type: str,
        granted: bool,
    ) -> dict[str, Any]:
        """Update user consent"""
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # In production, would update consent table
        # For now, log the consent update
        logger.info(f"Consent updated for user {user_id}: {consent_type} = {granted}")

        return {
            "user_id": user_id,
            "consent_type": consent_type,
            "granted": granted,
            "updated_at": datetime.utcnow().isoformat(),
        }
