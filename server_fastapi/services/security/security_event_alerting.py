"""
Security Event Alerting Service
Integrates security events with alerting system and fraud detection
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..alerting.alerting_service import (
    AlertChannel,
    AlertingService,
    AlertRule,
    AlertSeverity,
)
from ..audit.audit_logger import audit_logger
from ..fraud_detection.fraud_detection_service import FraudDetectionService

logger = logging.getLogger(__name__)


class SecurityEventAlertingService:
    """
    Service for alerting on security events

    Features:
    - Security event detection and alerting
    - Integration with audit logging
    - Fraud detection alerts
    - Audit log tampering detection
    - Real-time security monitoring
    """

    def __init__(self, alerting_service: AlertingService | None = None):
        self.alerting_service = alerting_service or AlertingService()
        self.fraud_detection = FraudDetectionService()

        # Security event counters (for rate limiting alerts)
        self.event_counts: dict[str, int] = {}
        self.event_timestamps: dict[str, list[datetime]] = {}

        # Register security alert rules
        self._register_security_rules()

    def _register_security_rules(self) -> None:
        """Register default security alert rules"""
        # Failed login attempts
        self.alerting_service.register_rule(
            AlertRule(
                name="high_failed_logins",
                metric="failed_login_attempts",
                threshold=10,
                operator="gt",
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
                duration=300,  # 5 minutes
                cooldown=3600,  # 1 hour
            )
        )

        # Suspicious activity detected
        self.alerting_service.register_rule(
            AlertRule(
                name="suspicious_activity",
                metric="suspicious_activity_score",
                threshold=0.7,
                operator="gt",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.PAGERDUTY],
                duration=60,  # 1 minute
                cooldown=1800,  # 30 minutes
            )
        )

        # Audit log tampering
        self.alerting_service.register_rule(
            AlertRule(
                name="audit_log_tampering",
                metric="audit_log_integrity",
                threshold=0,  # Any tampering = alert
                operator="lt",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.PAGERDUTY],
                duration=0,  # Immediate
                cooldown=3600,  # 1 hour
            )
        )

        # Fraud detection alerts
        self.alerting_service.register_rule(
            AlertRule(
                name="fraud_detected",
                metric="fraud_risk_score",
                threshold=0.7,
                operator="gt",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.PAGERDUTY],
                duration=60,
                cooldown=1800,
            )
        )

        # Unauthorized access attempts
        self.alerting_service.register_rule(
            AlertRule(
                name="unauthorized_access",
                metric="unauthorized_access_count",
                threshold=1,
                operator="gt",
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
                duration=60,
                cooldown=1800,
            )
        )

        # Token rotation events
        self.alerting_service.register_rule(
            AlertRule(
                name="token_rotation_suspicious",
                metric="token_rotation_count",
                threshold=5,
                operator="gt",
                severity=AlertSeverity.MEDIUM,
                channels=[AlertChannel.EMAIL],
                duration=300,
                cooldown=3600,
            )
        )

    async def handle_security_event(
        self,
        event_type: str,
        user_id: int | None,
        details: dict[str, Any],
        db: AsyncSession | None = None,
    ) -> None:
        """
        Handle a security event and trigger appropriate alerts

        Args:
            event_type: Type of security event
            user_id: User ID (if applicable)
            details: Event details
            db: Database session
        """
        try:
            # Log to audit log
            audit_logger.log_security_event(
                user_id=user_id or 0,
                event_type=event_type,
                details=details,
            )

            # Track event for rate limiting
            self._track_event(event_type, user_id)

            # Trigger appropriate alerts based on event type
            if event_type == "failed_login":
                await self._handle_failed_login(user_id, details)
            elif event_type == "suspicious_activity":
                await self._handle_suspicious_activity(user_id, details, db)
            elif event_type == "unauthorized_access":
                await self._handle_unauthorized_access(user_id, details)
            elif event_type == "token_rotation":
                await self._handle_token_rotation(user_id, details)
            elif event_type == "fraud_detected":
                await self._handle_fraud_detected(user_id, details)
            elif event_type == "audit_tampering":
                await self._handle_audit_tampering(details)
            elif event_type == "account_lockout":
                await self._handle_account_lockout(user_id, details)

        except Exception as e:
            logger.error(f"Error handling security event: {e}", exc_info=True)

    def _track_event(self, event_type: str, user_id: int | None) -> None:
        """Track event for rate limiting and pattern detection"""
        key = f"{event_type}:{user_id or 'anonymous'}"

        if key not in self.event_counts:
            self.event_counts[key] = 0
            self.event_timestamps[key] = []

        self.event_counts[key] += 1
        self.event_timestamps[key].append(datetime.now(UTC))

        # Clean old timestamps (keep last 24 hours)
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        self.event_timestamps[key] = [
            ts for ts in self.event_timestamps[key] if ts > cutoff
        ]

    async def _handle_failed_login(
        self, user_id: int | None, details: dict[str, Any]
    ) -> None:
        """Handle failed login event"""
        failed_count = details.get("failed_count", 1)

        # Trigger alert if threshold exceeded
        await self.alerting_service.evaluate_rule("high_failed_logins", failed_count)

    async def _handle_suspicious_activity(
        self,
        user_id: int | None,
        details: dict[str, Any],
        db: AsyncSession | None,
    ) -> None:
        """Handle suspicious activity event"""
        activity_score = details.get("risk_score", 0.0)

        # Trigger alert
        await self.alerting_service.evaluate_rule("suspicious_activity", activity_score)

        # If high risk, also run fraud detection
        if activity_score >= 0.7 and user_id and db:
            fraud_result = await self.fraud_detection.analyze_transaction(
                user_id=user_id,
                transaction_type=details.get("transaction_type", "unknown"),
                amount=details.get("amount", 0),
                currency=details.get("currency", "USD"),
                metadata=details,
                db=db,
            )

            if fraud_result.get("is_fraud"):
                await self._handle_fraud_detected(user_id, fraud_result)

    async def _handle_unauthorized_access(
        self, user_id: int | None, details: dict[str, Any]
    ) -> None:
        """Handle unauthorized access attempt"""
        await self.alerting_service.evaluate_rule("unauthorized_access", 1)  # Count

    async def _handle_token_rotation(
        self, user_id: int | None, details: dict[str, Any]
    ) -> None:
        """Handle token rotation event"""
        rotation_count = details.get("rotation_count", 1)
        reason = details.get("reason", "unknown")

        # Only alert if suspicious reason
        if reason in ["suspicious_login_location", "suspicious_activity"]:
            await self.alerting_service.evaluate_rule(
                "token_rotation_suspicious", rotation_count
            )

    async def _handle_fraud_detected(
        self, user_id: int | None, details: dict[str, Any]
    ) -> None:
        """Handle fraud detection event"""
        risk_score = details.get("risk_score", 0.0)

        await self.alerting_service.evaluate_rule("fraud_detected", risk_score)

    async def _handle_audit_tampering(self, details: dict[str, Any]) -> None:
        """Handle audit log tampering detection"""
        # Critical alert - immediate notification
        await self.alerting_service.evaluate_rule(
            "audit_log_tampering",
            0,  # Any tampering = 0 (below threshold)
        )

    async def _handle_account_lockout(
        self, user_id: int | None, details: dict[str, Any]
    ) -> None:
        """Handle account lockout event"""
        # Log and potentially alert on repeated lockouts
        lockout_count = details.get("lockout_count", 1)

        if lockout_count > 3:
            # Multiple lockouts = suspicious
            await self.alerting_service.evaluate_rule(
                "suspicious_activity",
                0.6,  # Medium-high risk
            )

    async def verify_audit_log_integrity(self) -> bool:
        """
        Verify audit log integrity and alert on tampering

        Returns:
            True if integrity verified, False if tampering detected
        """
        try:
            # Use audit logger's verification
            is_valid = audit_logger._verify_hash_chain()

            if not is_valid:
                # Critical security event - alert immediately
                await self.handle_security_event(
                    event_type="audit_tampering",
                    user_id=None,
                    details={
                        "verification_failed": True,
                        "timestamp": datetime.now(UTC).isoformat(),
                        "message": "Audit log hash chain verification failed - possible tampering",
                    },
                )

                logger.critical("AUDIT LOG TAMPERING DETECTED!")

            return is_valid

        except Exception as e:
            logger.error(f"Error verifying audit log integrity: {e}", exc_info=True)
            return False

    async def monitor_security_events(
        self,
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Monitor and analyze security events

        Returns:
            Dict with security metrics and alerts
        """
        try:
            # Verify audit log integrity
            audit_integrity = await self.verify_audit_log_integrity()

            # Get recent security events from audit log
            recent_events = audit_logger.get_audit_logs(
                event_type="security_event",
                start_date=datetime.now(UTC) - timedelta(hours=24),
                limit=100,
            )

            # Analyze event patterns
            event_summary = {
                "audit_integrity": audit_integrity,
                "total_events_24h": len(recent_events),
                "event_types": {},
                "high_risk_events": [],
                "active_alerts": len(self.alerting_service.active_alerts),
            }

            # Count event types
            for event in recent_events:
                event_type = event.get("security_event_type", "unknown")
                event_summary["event_types"][event_type] = (
                    event_summary["event_types"].get(event_type, 0) + 1
                )

                # Flag high-risk events
                if event_type in [
                    "suspicious_activity",
                    "unauthorized_access",
                    "fraud_detected",
                ]:
                    event_summary["high_risk_events"].append(event)

            return event_summary

        except Exception as e:
            logger.error(f"Error monitoring security events: {e}", exc_info=True)
            return {"error": str(e)}


# Global instance
_security_event_alerting_service: SecurityEventAlertingService | None = None


def get_security_event_alerting_service() -> SecurityEventAlertingService:
    """Get security event alerting service instance"""
    global _security_event_alerting_service
    if _security_event_alerting_service is None:
        _security_event_alerting_service = SecurityEventAlertingService()
    return _security_event_alerting_service
