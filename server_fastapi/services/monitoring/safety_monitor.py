"""
Safety monitoring service
"""

from typing import Dict, List, Optional
from pydantic import BaseModel
import sqlite3
import os
import time
import uuid
import logging

logger = logging.getLogger(__name__)


class SafetyAlert(BaseModel):
    id: str
    type: str
    severity: str
    message: str
    timestamp: int
    resolved: bool


class SafetyMonitor:
    """Safety monitoring and alerting service"""

    def __init__(self, db_path: str = "data/safety_monitor.db"):
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Initialize SQLite database and create tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS safety_alerts (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            """
            )
            logger.info(f"Safety monitor database initialized at {self.db_path}")

    async def _save_alert(self, alert: SafetyAlert):
        """Save alert to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO safety_alerts (id, type, severity, message, timestamp, resolved)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        alert.id,
                        alert.type,
                        alert.severity,
                        alert.message,
                        alert.timestamp,
                        alert.resolved,
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to save alert {alert.id}: {e}")
            raise

    async def check_safety_conditions(self) -> List[SafetyAlert]:
        """Check various safety conditions and generate alerts"""
        alerts = []

        # Check system health (placeholder - integrate with actual system monitoring)
        # Check database connectivity
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("SELECT 1").fetchone()
        except Exception as e:
            alert = SafetyAlert(
                id=str(uuid.uuid4()),
                type="system",
                severity="critical",
                message=f"Database connectivity failure: {str(e)}",
                timestamp=int(time.time() * 1000),
                resolved=False,
            )
            alerts.append(alert)
            await self._save_alert(alert)

        # Check memory usage (placeholder - would integrate with psutil or similar)
        # Check disk space (placeholder)
        # Check network connectivity (placeholder)

        return alerts

    async def monitor_position_sizes(
        self, portfolio: Dict[str, any]
    ) -> Optional[SafetyAlert]:
        """Monitor position sizes for risk limits"""
        # Define risk limits (these could be configurable)
        MAX_POSITION_SIZE_PERCENT = 20.0  # Max 20% of portfolio per position
        MAX_TOTAL_EXPOSURE_PERCENT = 80.0  # Max 80% total exposure

        total_portfolio_value = portfolio.get("total_value", 0)
        positions = portfolio.get("positions", {})

        if total_portfolio_value <= 0:
            return None

        # Check individual position sizes
        for symbol, position in positions.items():
            position_value = abs(position.get("value", 0))
            position_percent = (position_value / total_portfolio_value) * 100

            if position_percent > MAX_POSITION_SIZE_PERCENT:
                alert = SafetyAlert(
                    id=str(uuid.uuid4()),
                    type="position_size",
                    severity="high",
                    message=f"Position size for {symbol} exceeds limit: {position_percent:.2f}% (max: {MAX_POSITION_SIZE_PERCENT}%)",
                    timestamp=int(time.time() * 1000),
                    resolved=False,
                )
                await self._save_alert(alert)
                return alert

        # Check total exposure
        total_exposure = sum(abs(pos.get("value", 0)) for pos in positions.values())
        exposure_percent = (total_exposure / total_portfolio_value) * 100

        if exposure_percent > MAX_TOTAL_EXPOSURE_PERCENT:
            alert = SafetyAlert(
                id=str(uuid.uuid4()),
                type="total_exposure",
                severity="high",
                message=f"Total portfolio exposure exceeds limit: {exposure_percent:.2f}% (max: {MAX_TOTAL_EXPOSURE_PERCENT}%)",
                timestamp=int(time.time() * 1000),
                resolved=False,
            )
            await self._save_alert(alert)
            return alert

        return None

    async def monitor_drawdown(
        self, portfolio_value: float, peak_value: float
    ) -> Optional[SafetyAlert]:
        """Monitor portfolio drawdown"""
        if peak_value <= 0:
            return None

        drawdown_percent = ((peak_value - portfolio_value) / peak_value) * 100

        # Define drawdown thresholds
        WARNING_THRESHOLD = 10.0  # 10% drawdown
        CRITICAL_THRESHOLD = 20.0  # 20% drawdown

        if drawdown_percent >= CRITICAL_THRESHOLD:
            alert = SafetyAlert(
                id=str(uuid.uuid4()),
                type="drawdown",
                severity="critical",
                message=".2f",
                timestamp=int(time.time() * 1000),
                resolved=False,
            )
            await self._save_alert(alert)
            return alert
        elif drawdown_percent >= WARNING_THRESHOLD:
            alert = SafetyAlert(
                id=str(uuid.uuid4()),
                type="drawdown",
                severity="medium",
                message=".2f",
                timestamp=int(time.time() * 1000),
                resolved=False,
            )
            await self._save_alert(alert)
            return alert

        return None

    async def emergency_stop(self) -> bool:
        """Execute emergency stop procedure"""
        try:
            # Create emergency alert
            alert = SafetyAlert(
                id=str(uuid.uuid4()),
                type="emergency_stop",
                severity="critical",
                message="Emergency stop activated - all trading halted",
                timestamp=int(time.time() * 1000),
                resolved=False,
            )
            await self._save_alert(alert)

            # Integrate with trading orchestrator to halt all bots
            try:
                from ..trading_orchestrator import trading_orchestrator

                await trading_orchestrator.emergency_stop_all()
                logger.warning("Emergency stop: All trading bots halted")
            except Exception as e:
                logger.error(f"Failed to halt trading bots during emergency stop: {e}")

            # Send notifications to all users
            try:
                from ..notification_service import NotificationService

                notification_service = NotificationService()
                # In production, would send to all active users
                logger.info("Emergency stop notifications would be sent to all users")
            except Exception as e:
                logger.error(f"Failed to send emergency stop notifications: {e}")

            # Log emergency stop event
            logger.critical(f"EMERGENCY STOP ACTIVATED: {reason}")
            await self._save_alert(
                SafetyAlert(
                    id=str(uuid.uuid4()),
                    type="emergency_stop",
                    severity="critical",
                    message=f"Emergency stop activated: {reason}",
                    timestamp=int(time.time() * 1000),
                    resolved=False,
                )
            )

            logger.critical("Emergency stop activated")
            return True
        except Exception as e:
            logger.error(f"Emergency stop failed: {e}")
            return False

    async def get_active_alerts(self) -> List[SafetyAlert]:
        """Get all active safety alerts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT id, type, severity, message, timestamp, resolved
                    FROM safety_alerts
                    WHERE resolved = FALSE
                    ORDER BY timestamp DESC
                """
                )
                rows = cursor.fetchall()

                alerts = []
                for row in rows:
                    alerts.append(
                        SafetyAlert(
                            id=row[0],
                            type=row[1],
                            severity=row[2],
                            message=row[3],
                            timestamp=row[4],
                            resolved=bool(row[5]),
                        )
                    )
                return alerts
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []
