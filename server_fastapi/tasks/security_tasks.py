"""
Security-related Celery tasks
Periodic tasks for security monitoring, audit log verification, and fraud detection
"""

from celery import shared_task
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_context
from ..services.security.security_event_alerting import (
    get_security_event_alerting_service,
)
from ..services.audit.audit_logger import audit_logger

logger = logging.getLogger(__name__)


@shared_task(name="security.verify_audit_log_integrity")
async def verify_audit_log_integrity_task():
    """
    Periodic task to verify audit log integrity

    Runs every hour to check for tampering
    """
    try:
        security_service = get_security_event_alerting_service()

        # Use database context if needed
        async with get_db_context() as db:
            is_valid = await security_service.verify_audit_log_integrity()

            if not is_valid:
                logger.critical(
                    "Audit log integrity verification failed in periodic task!"
                )

            return {
                "integrity_verified": is_valid,
                "timestamp": datetime.utcnow().isoformat(),
            }

    except Exception as e:
        logger.error(
            f"Error in audit log integrity verification task: {e}", exc_info=True
        )
        return {"error": str(e)}


@shared_task(name="security.monitor_security_events")
async def monitor_security_events_task():
    """
    Periodic task to monitor security events and generate alerts

    Runs every 15 minutes to check for security issues
    """
    try:
        security_service = get_security_event_alerting_service()

        async with get_db_context() as db:
            monitoring_data = await security_service.monitor_security_events(db=db)

            # Log summary
            logger.info(
                f"Security monitoring: {monitoring_data.get('total_events_24h', 0)} events in last 24h, "
                f"{monitoring_data.get('active_alerts', 0)} active alerts"
            )

            return monitoring_data

    except Exception as e:
        logger.error(f"Error in security monitoring task: {e}", exc_info=True)
        return {"error": str(e)}


@shared_task(name="security.cleanup_old_security_events")
async def cleanup_old_security_events_task():
    """
    Periodic task to clean up old security event data

    Runs daily to maintain performance
    """
    try:
        # Clean up old audit logs (retention: 90 days)
        audit_logger.cleanup_old_logs(retention_days=90)

        logger.info("Cleaned up old security events and audit logs")

        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error cleaning up old security events: {e}", exc_info=True)
        return {"error": str(e)}
