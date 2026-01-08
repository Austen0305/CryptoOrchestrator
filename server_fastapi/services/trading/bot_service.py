from __future__ import annotations

"""
Unified bot service facade
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .bot_control_service import BotControlService
from .bot_creation_service import BotCreationService
from .bot_monitoring_service import BotMonitoringService
from .bot_trading_service import BotTradingService

logger = logging.getLogger(__name__)


class BotService:
    """Unified facade for all bot operations"""

    def __init__(self, db_session: AsyncSession | None = None):
        self.creation = BotCreationService(session=db_session)
        self.control = BotControlService(session=db_session)
        self.monitoring = BotMonitoringService(session=db_session)
        self.trading = BotTradingService(session=db_session)

    # Creation operations
    async def create_bot(
        self,
        user_id: int,
        name: str,
        symbol: str,
        strategy: str,
        parameters: dict[str, Any],
    ) -> str | None:
        """Create a new bot"""
        return await self.creation.create_bot(
            user_id, name, symbol, strategy, parameters
        )

    async def update_bot(
        self, bot_id: str, user_id: int, updates: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update an existing bot and return the updated bot configuration"""
        return await self.creation.update_bot(bot_id, user_id, updates)

    async def delete_bot(self, bot_id: str, user_id: int) -> bool:
        """Delete a bot"""
        return await self.creation.delete_bot(bot_id, user_id)

    async def get_bot_config(self, bot_id: str, user_id: int) -> dict[str, Any] | None:
        """Get bot configuration"""
        return await self.creation.get_bot_config(bot_id, user_id)

    async def list_user_bots(self, user_id: int) -> list[Any]:
        """List all bots for a user"""
        return await self.creation.list_user_bots(user_id)

    async def validate_bot_config(self, strategy: str, config: dict[str, Any]) -> bool:
        """Validate bot configuration"""
        return await self.creation.validate_bot_config(strategy, config)

    # Control operations
    async def start_bot(self, bot_id: str, user_id: int) -> bool:
        """Start a trading bot"""
        return await self.control.start_bot(bot_id, user_id)

    async def stop_bot(self, bot_id: str, user_id: int) -> bool:
        """Stop a trading bot"""
        return await self.control.stop_bot(bot_id, user_id)

    async def get_bot_status(self, bot_id: str, user_id: int) -> dict[str, Any] | None:
        """Get bot status"""
        return await self.control.get_bot_status(bot_id, user_id)

    async def is_bot_active(self, bot_id: str, user_id: int) -> bool:
        """Check if bot is active"""
        return await self.control.is_bot_active(bot_id, user_id)

    async def get_bot_state(self, bot_id: str, user_id: int) -> str:
        """Get bot state"""
        return await self.control.get_bot_state(bot_id, user_id)

    async def bulk_stop_user_bots(self, user_id: int) -> int:
        """Stop all user bots"""
        return await self.control.bulk_stop_user_bots(user_id)

    # Monitoring operations
    async def check_bot_health(self, bot_id: str, user_id: int) -> dict[str, Any]:
        """Check bot health"""
        return await self.monitoring.check_bot_health(bot_id, user_id)

    async def get_bot_alerts(self, bot_id: str, user_id: int) -> list[Any]:
        """Get bot alerts"""
        return await self.monitoring.get_bot_alerts(bot_id, user_id)

    async def get_bot_performance(self, bot_id: str, user_id: int) -> dict[str, Any]:
        """Get bot performance metrics"""
        return await self.monitoring.get_bot_performance(bot_id, user_id)

    async def validate_bot_start_conditions(
        self, bot_id: str, user_id: int
    ) -> dict[str, Any]:
        """Validate start conditions"""
        return await self.monitoring.validate_bot_start_conditions(bot_id, user_id)

    async def monitor_active_bots(self, user_id: int) -> dict[str, Any]:
        """Monitor active bots"""
        return await self.monitoring.monitor_active_bots(user_id)

    async def emergency_stop_bot(
        self, bot_id: str, user_id: int, reason: str = "manual_emergency"
    ) -> bool:
        """Emergency stop bot"""
        return await self.monitoring.emergency_stop_bot(bot_id, user_id, reason)

    async def emergency_stop_all_user_bots(
        self, user_id: int, reason: str = "system_emergency"
    ) -> int:
        """Emergency stop all user bots"""
        return await self.monitoring.emergency_stop_all_user_bots(user_id, reason)

    async def get_system_safety_status(self) -> dict[str, Any]:
        """Get system safety status"""
        return await self.monitoring.get_system_safety_status()

    # Trading operations
    async def execute_trading_cycle(self, bot_config: dict[str, Any]) -> dict[str, Any]:
        """Execute trading cycle"""
        return await self.trading.execute_trading_cycle(bot_config)

    async def run_bot_loop(self, bot_id: str, user_id: int):
        """Run bot trading loop"""
        return await self.trading.run_bot_loop(bot_id, user_id)


# Dependency injection functions
def get_bot_service(db_session: AsyncSession | None = None) -> BotService:
    """Get bot service instance"""
    return BotService(db_session=db_session)


def get_bot_creation_service(
    db_session: AsyncSession | None = None,
) -> BotCreationService:
    """Get bot creation service instance"""
    return BotCreationService(session=db_session)


def get_bot_control_service(
    db_session: AsyncSession | None = None,
) -> BotControlService:
    """Get bot control service instance"""
    return BotControlService(session=db_session)


def get_bot_monitoring_service(
    db_session: AsyncSession | None = None,
) -> BotMonitoringService:
    """Get bot monitoring service instance"""
    return BotMonitoringService(session=db_session)


def get_bot_trading_service(
    db_session: AsyncSession | None = None,
) -> BotTradingService:
    """Get bot trading service instance"""
    return BotTradingService(session=db_session)
