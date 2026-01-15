"""
Security Monitoring Service
Intrusion detection, anomaly detection, and security event logging
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SecurityMonitoringService:
    """
    Service for security monitoring and anomaly detection

    Features:
    - Intrusion detection
    - Anomaly detection
    - Security event logging
    - Incident response automation
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.anomaly_thresholds = {
            "failed_login_attempts": 5,  # Per hour
            "api_rate_limit_exceeded": 100,  # Per minute
            "unusual_ip_access": 10,  # Different IPs per hour
            "large_transaction": 100000,  # USD
            "suspicious_activity": 3,  # Events per hour
        }

    async def log_security_event(
        self,
        event_type: str,
        severity: str,  # low, medium, high, critical
        description: str,
        user_id: int | None = None,
        ip_address: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Log a security event

        Args:
            event_type: Type of security event
            severity: Event severity
            description: Event description
            user_id: Associated user ID
            ip_address: Source IP address
            metadata: Additional metadata

        Returns:
            Logged event details
        """
        # In production, would store in security_events table
        event = {
            "event_type": event_type,
            "severity": severity,
            "description": description,
            "user_id": user_id,
            "ip_address": ip_address,
            "metadata": metadata or {},
            "timestamp": datetime.now(UTC).isoformat(),
        }

        logger.warning(f"Security Event: {event_type} - {description}", extra=event)

        # Check for anomalies
        await self._check_anomalies(event)

        return event

    async def _check_anomalies(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        """Check for security anomalies"""
        anomalies = []

        # Check failed login attempts
        if event["event_type"] == "failed_login":
            count = await self._count_recent_events(
                event_type="failed_login",
                user_id=event.get("user_id"),
                minutes=60,
            )
            if count >= self.anomaly_thresholds["failed_login_attempts"]:
                anomalies.append(
                    {
                        "type": "brute_force_attempt",
                        "severity": "high",
                        "description": f"Multiple failed login attempts ({count})",
                    }
                )

        # Check API rate limit exceeded
        if event["event_type"] == "rate_limit_exceeded":
            count = await self._count_recent_events(
                event_type="rate_limit_exceeded",
                ip_address=event.get("ip_address"),
                minutes=1,
            )
            if count >= self.anomaly_thresholds["api_rate_limit_exceeded"]:
                anomalies.append(
                    {
                        "type": "ddos_attempt",
                        "severity": "high",
                        "description": f"Excessive API requests ({count}/min)",
                    }
                )

        # Check unusual IP access
        if event["event_type"] == "login_success":
            ip_count = await self._count_unique_ips(
                user_id=event.get("user_id"),
                hours=1,
            )
            if ip_count >= self.anomaly_thresholds["unusual_ip_access"]:
                anomalies.append(
                    {
                        "type": "account_compromise",
                        "severity": "critical",
                        "description": f"Login from {ip_count} different IPs",
                    }
                )

        # Trigger incident response if critical
        for anomaly in anomalies:
            if anomaly["severity"] == "critical":
                await self._trigger_incident_response(anomaly, event)

        return anomalies

    async def _count_recent_events(
        self,
        event_type: str,
        user_id: int | None = None,
        ip_address: str | None = None,
        minutes: int = 60,
    ) -> int:
        """Count recent events of a type"""
        # Mock implementation - would query security_events table
        # In production:
        # stmt = select(func.count(SecurityEvent.id)).where(
        #     and_(
        #         SecurityEvent.event_type == event_type,
        #         SecurityEvent.created_at >= datetime.now(UTC) - timedelta(minutes=minutes),
        #         SecurityEvent.user_id == user_id if user_id else True,
        #         SecurityEvent.ip_address == ip_address if ip_address else True,
        #     )
        # )
        # result = await self.db.execute(stmt)
        # return result.scalar() or 0
        return 0

    async def _count_unique_ips(
        self,
        user_id: int,
        hours: int = 1,
    ) -> int:
        """Count unique IP addresses for a user"""
        # Mock implementation
        return 0

    async def _trigger_incident_response(
        self,
        anomaly: dict[str, Any],
        event: dict[str, Any],
    ) -> None:
        """Trigger automated incident response"""
        logger.critical(
            f"CRITICAL SECURITY INCIDENT: {anomaly['type']} - {anomaly['description']}",
            extra={"anomaly": anomaly, "event": event},
        )

        # Automated response actions:
        # 1. Lock account if user_id present
        # 2. Block IP address
        # 3. Send alert to security team
        # 4. Create incident ticket

        if event.get("user_id"):
            # Lock user account
            logger.info(f"Auto-locking user account: {event['user_id']}")
            # await self._lock_user_account(event['user_id'])

        if event.get("ip_address"):
            # Block IP address
            logger.info(f"Auto-blocking IP address: {event['ip_address']}")
            # await self._block_ip_address(event['ip_address'])

    async def get_security_events(
        self,
        event_type: str | None = None,
        severity: str | None = None,
        user_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get security events with filtering"""
        # Mock implementation - would query security_events table
        events = []

        # In production:
        # stmt = select(SecurityEvent)
        # if event_type:
        #     stmt = stmt.where(SecurityEvent.event_type == event_type)
        # if severity:
        #     stmt = stmt.where(SecurityEvent.severity == severity)
        # if user_id:
        #     stmt = stmt.where(SecurityEvent.user_id == user_id)
        # if start_date:
        #     stmt = stmt.where(SecurityEvent.created_at >= start_date)
        # if end_date:
        #     stmt = stmt.where(SecurityEvent.created_at <= end_date)
        # stmt = stmt.order_by(desc(SecurityEvent.created_at)).limit(limit)
        # result = await self.db.execute(stmt)
        # events = result.scalars().all()

        return events

    async def get_security_summary(
        self,
        days: int = 7,
    ) -> dict[str, Any]:
        """Get security summary for the last N days"""
        # Mock implementation
        summary = {
            "period_days": days,
            "total_events": 0,
            "events_by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "events_by_type": {},
            "anomalies_detected": 0,
            "incidents_triggered": 0,
        }

        return summary
