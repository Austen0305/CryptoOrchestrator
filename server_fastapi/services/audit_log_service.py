"""
Audit Log Service
Comprehensive audit logging with integrity protection
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.audit_logs import AuditLog

logger = logging.getLogger(__name__)


class AuditLogService:
    """Service for comprehensive audit logging"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        event_type: str,
        event_category: str,  # user_action, system_event, data_change, security, trading
        event_name: str,
        event_data: dict[str, Any],
        user_id: int | None = None,
        session_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        compliance_flags: list[str] | None = None,
        retention_days: int = 2555,  # 7 years default for financial compliance
    ) -> AuditLog:
        """
        Log an audit event with integrity protection

        Args:
            event_type: Type of event
            event_category: Category (user_action, system_event, etc.)
            event_name: Human-readable event name
            event_data: Full event details
            user_id: User who performed the action
            session_id: Session identifier
            ip_address: Source IP address
            user_agent: User agent string
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            compliance_flags: Compliance requirements (GDPR, SOX, MiFID II, etc.)
            retention_days: Days to retain this log

        Returns:
            Created audit log entry
        """
        # Get previous hash for chain integrity
        previous_hash = await self._get_latest_hash()

        # Create audit log entry
        audit_log = AuditLog(
            event_type=event_type,
            event_category=event_category,
            event_name=event_name,
            event_data=event_data,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            previous_hash=previous_hash,
            compliance_flags=compliance_flags or [],
            retention_until=datetime.now(UTC) + timedelta(days=retention_days),
        )

        # Calculate integrity hash
        audit_log.integrity_hash = audit_log.calculate_integrity_hash()

        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)

        logger.info(f"Audit log created: {event_type} - {event_name}")

        return audit_log

    async def _get_latest_hash(self) -> str | None:
        """Get the hash of the most recent audit log entry"""
        stmt = (
            select(AuditLog.integrity_hash).order_by(desc(AuditLog.created_at)).limit(1)
        )
        result = await self.db.execute(stmt)
        latest = result.scalar_one_or_none()
        return latest

    async def get_audit_logs(
        self,
        event_type: str | None = None,
        event_category: str | None = None,
        user_id: int | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs with filtering"""
        stmt = select(AuditLog)

        conditions = []
        if event_type:
            conditions.append(AuditLog.event_type == event_type)
        if event_category:
            conditions.append(AuditLog.event_category == event_category)
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)
        if resource_id:
            conditions.append(AuditLog.resource_id == resource_id)
        if start_date:
            conditions.append(AuditLog.created_at >= start_date)
        if end_date:
            conditions.append(AuditLog.created_at <= end_date)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(desc(AuditLog.created_at)).limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def verify_integrity(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Verify integrity of audit log chain

        Returns:
            Integrity verification results
        """
        stmt = select(AuditLog).order_by(AuditLog.created_at)

        if start_date:
            stmt = stmt.where(AuditLog.created_at >= start_date)
        if end_date:
            stmt = stmt.where(AuditLog.created_at <= end_date)

        result = await self.db.execute(stmt)
        logs = list(result.scalars().all())

        if not logs:
            return {
                "valid": True,
                "total_logs": 0,
                "verified_logs": 0,
                "invalid_logs": [],
            }

        invalid_logs = []
        previous_hash = None

        for i, log in enumerate(logs):
            # Check previous hash chain
            if i > 0 and log.previous_hash != previous_hash:
                invalid_logs.append(
                    {
                        "log_id": log.id,
                        "issue": "previous_hash_mismatch",
                        "expected": previous_hash,
                        "actual": log.previous_hash,
                    }
                )

            # Verify integrity hash
            expected_hash = log.calculate_integrity_hash()
            if log.integrity_hash != expected_hash:
                invalid_logs.append(
                    {
                        "log_id": log.id,
                        "issue": "integrity_hash_mismatch",
                        "expected": expected_hash,
                        "actual": log.integrity_hash,
                    }
                )

            previous_hash = log.integrity_hash

        return {
            "valid": len(invalid_logs) == 0,
            "total_logs": len(logs),
            "verified_logs": len(logs) - len(invalid_logs),
            "invalid_logs": invalid_logs,
        }

    async def get_audit_summary(
        self,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get audit log summary statistics"""
        start_date = datetime.now(UTC) - timedelta(days=days)

        # Count by category
        stmt = (
            select(
                AuditLog.event_category,
                func.count(AuditLog.id).label("count"),
            )
            .where(AuditLog.created_at >= start_date)
            .group_by(AuditLog.event_category)
        )

        result = await self.db.execute(stmt)
        category_counts = {row.event_category: row.count for row in result.all()}

        # Count by type
        stmt = (
            select(
                AuditLog.event_type,
                func.count(AuditLog.id).label("count"),
            )
            .where(AuditLog.created_at >= start_date)
            .group_by(AuditLog.event_type)
        )

        result = await self.db.execute(stmt)
        type_counts = {row.event_type: row.count for row in result.all()}

        # Total count
        stmt = select(func.count(AuditLog.id)).where(AuditLog.created_at >= start_date)
        result = await self.db.execute(stmt)
        total_count = result.scalar() or 0

        return {
            "period_days": days,
            "total_events": total_count,
            "by_category": category_counts,
            "by_type": type_counts,
        }
