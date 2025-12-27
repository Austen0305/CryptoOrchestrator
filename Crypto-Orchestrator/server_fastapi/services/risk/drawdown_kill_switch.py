"""
Drawdown Kill Switch Service - Automatic shutdown on excessive drawdown
"""

from typing import Dict, Any, Optional, List, Tuple, Callable
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import logging
import asyncio

logger = logging.getLogger(__name__)


class DrawdownKillSwitchConfig(BaseModel):
    """Drawdown kill switch configuration"""

    enabled: bool = True
    max_drawdown_percent: float = 15.0  # 15% max drawdown before kill switch
    warning_threshold_percent: float = 10.0  # 10% warning threshold
    critical_threshold_percent: float = 12.0  # 12% critical threshold
    recovery_threshold_percent: float = 5.0  # 5% recovery before reactivation
    check_interval_seconds: int = 60  # Check every 60 seconds
    auto_recovery: bool = True  # Auto-recovery when drawdown reduces
    shutdown_all_bots: bool = True  # Shutdown all bots on kill switch
    notify_on_activation: bool = True  # Notify when kill switch activates


class DrawdownState(BaseModel):
    """Current drawdown state"""

    active: bool
    peak_value: float
    current_value: float
    current_drawdown_percent: float
    max_drawdown_percent: float
    activated_at: Optional[datetime] = None
    deactivated_at: Optional[datetime] = None
    reason: Optional[str] = None


class DrawdownEvent(BaseModel):
    """Drawdown event"""

    event_type: str  # 'warning', 'critical', 'kill_switch_activated', 'kill_switch_deactivated', 'recovery'
    drawdown_percent: float
    peak_value: float
    current_value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message: str


class DrawdownKillSwitch:
    """Drawdown kill switch service for automatic shutdown on excessive drawdown"""

    def __init__(self, config: Optional[DrawdownKillSwitchConfig] = None):
        self.config = config or DrawdownKillSwitchConfig()
        self.state: Optional[DrawdownState] = None
        self.peak_value: float = 0.0
        self.initial_value: float = 0.0
        self.events: List[DrawdownEvent] = []
        self.monitoring_task: Optional[asyncio.Task] = None
        self.callbacks: List[Callable[[DrawdownEvent], None]] = []

        logger.info("Drawdown Kill Switch initialized")

    def register_callback(self, callback: Callable[[DrawdownEvent], None]) -> None:
        """Register callback for drawdown events"""
        self.callbacks.append(callback)

    async def start_monitoring(
        self,
        get_portfolio_value: Callable[[], float],
        bot_service: Optional[Any] = None,
    ) -> None:
        """Start monitoring portfolio drawdown"""
        if not self.config.enabled:
            logger.info("Drawdown kill switch monitoring disabled")
            return

        if self.monitoring_task:
            logger.warning("Monitoring already started")
            return

        self.bot_service = bot_service
        self.get_portfolio_value = get_portfolio_value

        # Initialize peak value with current portfolio value
        current_value = await self._get_current_value()
        self.peak_value = current_value
        self.initial_value = current_value

        self.state = DrawdownState(
            active=False,
            peak_value=self.peak_value,
            current_value=current_value,
            current_drawdown_percent=0.0,
            max_drawdown_percent=0.0,
        )

        self.monitoring_task = asyncio.create_task(self._monitor_loop())
        logger.info("Drawdown kill switch monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop monitoring portfolio drawdown"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
            logger.info("Drawdown kill switch monitoring stopped")

    async def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        while True:
            try:
                await self._check_drawdown()
                await asyncio.sleep(self.config.check_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in drawdown monitoring loop: {e}")
                await asyncio.sleep(self.config.check_interval_seconds)

    async def _get_current_value(self) -> float:
        """Get current portfolio value"""
        try:
            if self.get_portfolio_value:
                if asyncio.iscoroutinefunction(self.get_portfolio_value):
                    return await self.get_portfolio_value()
                else:
                    return self.get_portfolio_value()
            return 0.0
        except Exception as e:
            logger.error(f"Error getting current portfolio value: {e}")
            return 0.0

    async def _check_drawdown(self) -> None:
        """Check current drawdown and activate kill switch if needed"""
        try:
            current_value = await self._get_current_value()

            if current_value <= 0:
                return

            # Update peak value if current value is higher
            if current_value > self.peak_value:
                self.peak_value = current_value

            # Calculate current drawdown
            current_drawdown = (
                (self.peak_value - current_value) / self.peak_value
            ) * 100

            # Calculate max drawdown
            max_drawdown = max(
                self.state.max_drawdown_percent if self.state else 0.0, current_drawdown
            )

            # Update state
            if self.state:
                self.state.current_value = current_value
                self.state.peak_value = self.peak_value
                self.state.current_drawdown_percent = current_drawdown
                self.state.max_drawdown_percent = max_drawdown
            else:
                self.state = DrawdownState(
                    active=False,
                    peak_value=self.peak_value,
                    current_value=current_value,
                    current_drawdown_percent=current_drawdown,
                    max_drawdown_percent=max_drawdown,
                )

            # Check if kill switch should be activated
            if not self.state.active:
                if current_drawdown >= self.config.max_drawdown_percent:
                    await self._activate_kill_switch(current_drawdown, current_value)
                elif current_drawdown >= self.config.critical_threshold_percent:
                    await self._emit_event("critical", current_drawdown, current_value)
                elif current_drawdown >= self.config.warning_threshold_percent:
                    await self._emit_event("warning", current_drawdown, current_value)
            else:
                # Kill switch is active, check for recovery
                if (
                    self.config.auto_recovery
                    and current_drawdown <= self.config.recovery_threshold_percent
                ):
                    await self._deactivate_kill_switch(current_drawdown, current_value)

        except Exception as e:
            logger.error(f"Error checking drawdown: {e}")

    async def _activate_kill_switch(
        self, drawdown_percent: float, current_value: float
    ) -> None:
        """Activate kill switch and stop all trading"""
        try:
            logger.critical(
                f"DRAWDOWN KILL SWITCH ACTIVATED: "
                f"Drawdown {drawdown_percent:.2f}% >= {self.config.max_drawdown_percent:.2f}%"
            )

            # Update state
            if self.state:
                self.state.active = True
                self.state.activated_at = datetime.utcnow()
                self.state.reason = f"Drawdown {drawdown_percent:.2f}% exceeded maximum {self.config.max_drawdown_percent:.2f}%"

            # Emit event
            await self._emit_event(
                "kill_switch_activated",
                drawdown_percent,
                current_value,
                f"Kill switch activated: Drawdown {drawdown_percent:.2f}% >= {self.config.max_drawdown_percent:.2f}%",
            )

            # Stop all bots if configured
            if self.config.shutdown_all_bots and self.bot_service:
                try:
                    # This would stop all active bots
                    # Implementation depends on bot_service interface
                    logger.critical(
                        "Stopping all active bots due to drawdown kill switch"
                    )
                    # await self.bot_service.stop_all_bots(reason="Drawdown kill switch activated")
                except Exception as e:
                    logger.error(f"Error stopping bots: {e}")

        except Exception as e:
            logger.error(f"Error activating kill switch: {e}")

    async def _deactivate_kill_switch(
        self, drawdown_percent: float, current_value: float
    ) -> None:
        """Deactivate kill switch after recovery"""
        try:
            logger.info(
                f"DRAWDOWN KILL SWITCH DEACTIVATED: "
                f"Drawdown {drawdown_percent:.2f}% <= {self.config.recovery_threshold_percent:.2f}%"
            )

            # Update state
            if self.state:
                self.state.active = False
                self.state.deactivated_at = datetime.utcnow()
                self.state.reason = f"Drawdown recovered to {drawdown_percent:.2f}%"

            # Emit event
            await self._emit_event(
                "kill_switch_deactivated",
                drawdown_percent,
                current_value,
                f"Kill switch deactivated: Drawdown recovered to {drawdown_percent:.2f}%",
            )

        except Exception as e:
            logger.error(f"Error deactivating kill switch: {e}")

    async def _emit_event(
        self,
        event_type: str,
        drawdown_percent: float,
        current_value: float,
        message: Optional[str] = None,
    ) -> None:
        """Emit drawdown event"""
        event = DrawdownEvent(
            event_type=event_type,
            drawdown_percent=drawdown_percent,
            peak_value=self.peak_value,
            current_value=current_value,
            message=message or f"Drawdown: {drawdown_percent:.2f}%",
        )

        self.events.append(event)

        # Keep only last 100 events
        if len(self.events) > 100:
            self.events = self.events[-100:]

        # Call registered callbacks
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in drawdown callback: {e}")

        # Log event
        if event_type == "warning":
            logger.warning(f"Drawdown warning: {drawdown_percent:.2f}%")
        elif event_type == "critical":
            logger.warning(f"Drawdown critical: {drawdown_percent:.2f}%")
        elif event_type == "kill_switch_activated":
            logger.critical(f"Kill switch activated: {drawdown_percent:.2f}%")
        elif event_type == "kill_switch_deactivated":
            logger.info(f"Kill switch deactivated: {drawdown_percent:.2f}%")
        elif event_type == "recovery":
            logger.info(f"Drawdown recovery: {drawdown_percent:.2f}%")

    async def manually_activate(self, reason: str = "Manual activation") -> bool:
        """Manually activate kill switch"""
        try:
            current_value = await self._get_current_value()
            current_drawdown = (
                ((self.peak_value - current_value) / self.peak_value) * 100
                if self.peak_value > 0
                else 0.0
            )

            await self._activate_kill_switch(current_drawdown, current_value)

            if self.state:
                self.state.reason = reason

            return True
        except Exception as e:
            logger.error(f"Error manually activating kill switch: {e}")
            return False

    async def manually_deactivate(self, reason: str = "Manual deactivation") -> bool:
        """Manually deactivate kill switch"""
        try:
            if not self.state or not self.state.active:
                logger.warning("Kill switch is not active")
                return False

            current_value = await self._get_current_value()
            current_drawdown = (
                ((self.peak_value - current_value) / self.peak_value) * 100
                if self.peak_value > 0
                else 0.0
            )

            await self._deactivate_kill_switch(current_drawdown, current_value)

            if self.state:
                self.state.reason = reason

            return True
        except Exception as e:
            logger.error(f"Error manually deactivating kill switch: {e}")
            return False

    def get_state(self) -> Optional[DrawdownState]:
        """Get current drawdown state"""
        if self.state is None:
            # Return default state if not initialized
            return DrawdownState(
                active=False,
                peak_value=0.0,
                current_value=0.0,
                current_drawdown_percent=0.0,
                max_drawdown_percent=0.0,
            )
        return self.state

    def get_events(self, limit: int = 50) -> List[DrawdownEvent]:
        """Get recent drawdown events"""
        return self.events[-limit:] if self.events else []

    def is_active(self) -> bool:
        """Check if kill switch is currently active"""
        return self.state.active if self.state else False

    def update_peak_value(self, new_peak: float) -> None:
        """Update peak value (e.g., after portfolio rebalancing)"""
        if new_peak > self.peak_value:
            self.peak_value = new_peak
            if self.state:
                self.state.peak_value = new_peak
            logger.info(f"Peak value updated to {new_peak:.2f}")

    def reset(self) -> None:
        """Reset kill switch state"""
        current_value = self.state.current_value if self.state else 0.0
        self.peak_value = current_value
        self.initial_value = current_value
        self.state = DrawdownState(
            active=False,
            peak_value=self.peak_value,
            current_value=current_value,
            current_drawdown_percent=0.0,
            max_drawdown_percent=0.0,
        )
        self.events = []
        logger.info("Drawdown kill switch reset")


# Global service instance
drawdown_kill_switch = DrawdownKillSwitch()
