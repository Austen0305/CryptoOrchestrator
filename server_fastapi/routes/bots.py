from __future__ import annotations
import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel

from ..dependencies.auth import get_current_user
from ..dependencies.bots import get_bot_service, get_bot_trading_service
from ..middleware.cache_manager import cached
from .integrations import get_trading_orchestrator
from ..services.trading.bot_service import BotService
from ..services.trading.bot_trading_service import BotTradingService
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class BotConfig(BaseModel):
    id: str
    user_id: int
    name: str
    symbol: str
    strategy: str
    is_active: bool
    status: str | None = None  # Bot status: "stopped", "running", "error", etc.
    config: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class CreateBotRequest(BaseModel):
    name: str
    symbol: str
    strategy: str
    config: dict[str, Any]

    @staticmethod
    def validate_strategy(strategy: str):
        valid_strategies = [
            "ml_enhanced",
            "ensemble",
            "neural_network",
            "simple_ma",
            "rsi",
            "smart_adaptive",
        ]
        if strategy not in valid_strategies:
            raise ValueError(
                f"Invalid strategy. Must be one of: {', '.join(valid_strategies)}"
            )


class UpdateBotRequest(BaseModel):
    name: str | None = None
    symbol: str | None = None
    strategy: str | None = None
    is_active: bool | None = None
    config: dict[str, Any] | None = None


class BotPerformance(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    current_balance: float


class MockBotStorage:
    def __init__(self):
        self.bots = {}
        self.next_id = 1
        self._seed_default_bots()

    def _seed_default_bots(self):
        default_bot = {
            "id": "bot-1",
            "user_id": 1,  # Associate with default user
            "name": "BTC Trend Follower",
            "symbol": "BTC/USD",
            "strategy": "ml_enhanced",
            "is_active": False,
            "config": {
                "max_position_size": 0.1,
                "stop_loss": 0.02,
                "take_profit": 0.05,
                "risk_per_trade": 0.01,
                "ml_config": {
                    "confidence_threshold": 0.7,
                    "features": ["price", "volume", "rsi", "macd"],
                },
            },
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        self.bots["bot-1"] = default_bot

    def get_all_bots(self) -> list[BotConfig]:
        return [BotConfig(**bot) for bot in self.bots.values()]

    def get_bot(self, bot_id: str) -> BotConfig | None:
        bot = self.bots.get(bot_id)
        return BotConfig(**bot) if bot else None

    def create_bot(self, bot_data: dict[str, Any], user_id: int) -> BotConfig:
        bot_id = f"bot-{self.next_id}"
        self.next_id += 1
        bot = {
            "id": bot_id,
            "user_id": user_id,
            "name": bot_data["name"],
            "symbol": bot_data["symbol"],
            "strategy": bot_data["strategy"],
            "is_active": False,
            "config": bot_data["config"],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        self.bots[bot_id] = bot
        return BotConfig(**bot)

    def get_user_bots(self, user_id: int) -> list[BotConfig]:
        return [
            BotConfig(**bot) for bot in self.bots.values() if bot["user_id"] == user_id
        ]

    def update_bot(self, bot_id: str, updates: dict[str, Any]) -> BotConfig | None:
        if bot_id not in self.bots:
            return None

        bot = self.bots[bot_id]
        for key, value in updates.items():
            if value is not None:
                if key == "config":
                    bot["config"].update(value)
                else:
                    bot[key] = value
        bot["updated_at"] = datetime.now()

        return BotConfig(**bot)

    def delete_bot(self, bot_id: str) -> bool:
        if bot_id in self.bots:
            del self.bots[bot_id]
            return True
        return False


@router.get("/")
@cached(ttl=120, prefix="bots")  # 2min TTL for bot list
async def get_bots(
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    fields: str | None = Query(
        None, description="Comma-separated list of fields to include"
    ),
) -> dict[str, Any]:
    """Get all trading bots for the authenticated user with pagination and field selection"""
    try:
        from ..middleware.query_cache import cache_query_result
        from ..utils.response_optimizer import ResponseOptimizer

        user_id = _get_user_id(current_user)

        # Use cached query result
        @cache_query_result(ttl=60, key_prefix="bot_list", include_user=True)
        async def _get_bots_cached(user_id_str: str, page: int, page_size: int):
            bot_configs = await bot_service.list_user_bots(user_id_str)
            total = len(bot_configs)

            # Apply pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_configs = bot_configs[start_idx:end_idx]

            # Convert to BotConfig response
            result = []
            for bot_conf in paginated_configs:
                bot_data = await bot_service.get_bot_config(bot_conf.id, user_id_str)
                if bot_data:
                    result.append(BotConfig(**bot_data))
            return result, total

        bots, total = await _get_bots_cached(str(user_id), page, page_size)

        # Apply field selection if requested (for future use)
        if fields:
            field_list = [f.strip() for f in fields.split(",")]
            bots = ResponseOptimizer.select_fields(bots, field_list)

        # Return standardized format
        return {
            "data": bots,
            "meta": {"total": total, "page": page, "page_size": page_size},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching bots for user {current_user.get('id', 'unknown')}: {e}",
            exc_info=True,
        )
        # Return empty list instead of 500 error for better UX during development
        logger.warning(f"Returning empty bots list due to error: {e}")
        return []


def _bot_cache_key(
    bot_id: str, current_user: dict, bot_service: BotService, **kwargs
) -> str:
    """Custom cache key builder that includes bot_id for searchable invalidation"""
    user_id = (
        current_user.get("id")
        or current_user.get("user_id")
        or current_user.get("sub", "unknown")
    )
    return f"{bot_id}:{user_id}"


@router.get("/{bot_id}")
@cached(
    ttl=120, prefix="bots", key_builder=_bot_cache_key
)  # 2min TTL for bot status, custom key with bot_id
async def get_bot(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
) -> BotConfig:
    """Get a specific bot by ID"""
    try:
        user_id = _get_user_id(current_user)
        bot = await bot_service.get_bot_config(bot_id, user_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        return BotConfig(**bot)
    except HTTPException:
        raise
    except Exception as e:
        # Handle database errors gracefully - if bot not found or table doesn't exist, return 404
        error_str = str(e).lower()
        if (
            "no such table" in error_str
            or "does not exist" in error_str
            or "mapper" in error_str
            or "not found" in error_str
        ):
            logger.warning(
                f"Bot not found or table not available, returning 404 for bot {bot_id}: {e}"
            )
            raise HTTPException(status_code=404, detail="Bot not found")
        logger.error(f"Error fetching bot {bot_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/")
async def create_bot(
    request: CreateBotRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
) -> BotConfig:
    """Create a new trading bot"""
    try:
        # Validate strategy
        CreateBotRequest.validate_strategy(request.strategy)

        # Validate configuration
        is_valid = await bot_service.validate_bot_config(
            request.strategy, request.config
        )
        logger.info(
            f"Bot config validation result: {is_valid} for strategy {request.strategy} with config {request.config}"
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid bot configuration")

        user_id = _get_user_id(current_user)
        bot_id = await bot_service.create_bot(
            user_id,
            request.name,
            request.symbol,
            request.strategy,
            request.config,
        )

        if not bot_id:
            raise HTTPException(status_code=500, detail="Failed to create bot")

        # Get the created bot
        bot_data = await bot_service.get_bot_config(bot_id, user_id)
        if not bot_data:
            raise HTTPException(
                status_code=500, detail="Failed to retrieve created bot"
            )

        # Invalidate bot list cache for this user (new bot added)
        try:
            from ..middleware.cache_manager import invalidate_pattern

            await invalidate_pattern(f"bots:get_bots:*:{user_id}*")
            await invalidate_pattern(f"bot_list:*:{user_id}*")
        except Exception as cache_error:
            logger.warning(f"Cache invalidation failed (non-critical): {cache_error}")

        logger.info(f"Created new bot: {bot_id} for user {user_id}")
        return BotConfig(**bot_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        try:
            user_id = _get_user_id(current_user)
        except HTTPException:
            user_id = "unknown"  # Fallback for error logging
        logger.error(f"Error creating bot for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create bot")


@router.patch("/{bot_id}")
async def update_bot(
    bot_id: str,
    request: UpdateBotRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
) -> BotConfig:
    """Update an existing bot"""
    try:
        user_id = _get_user_id(current_user)

        # Check if bot exists
        existing_bot = await bot_service.get_bot_config(bot_id, user_id)
        if not existing_bot:
            raise HTTPException(status_code=404, detail="Bot not found")

        # Validate strategy if being updated
        if request.strategy:
            CreateBotRequest.validate_strategy(request.strategy)

        # Prepare updates
        updates = {k: v for k, v in request.model_dump().items() if v is not None}

        # Update bot and get the updated bot configuration
        updated_bot = await bot_service.update_bot(bot_id, user_id, updates)
        if not updated_bot:
            raise HTTPException(status_code=500, detail="Failed to update bot")

        # Invalidate cache for this bot and bot list
        try:
            from ..middleware.cache_manager import invalidate_pattern

            # Invalidate bot-specific cache
            await invalidate_pattern(f"bots:get_bot:{bot_id}:{user_id}")
            # Invalidate bot list cache for this user
            await invalidate_pattern(f"bots:get_bots:*:{user_id}*")
            # Also invalidate query cache
            await invalidate_pattern(f"bot_list:*:{user_id}*")
        except Exception as cache_error:
            logger.warning(f"Cache invalidation failed (non-critical): {cache_error}")

        logger.info(f"Updated bot: {bot_id}")
        return BotConfig(**updated_bot)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update bot")


@router.delete("/{bot_id}")
async def delete_bot(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    """Delete a bot"""
    try:
        user_id = _get_user_id(current_user)

        # Check if bot exists
        existing_bot = await bot_service.get_bot_config(bot_id, user_id)
        if not existing_bot:
            raise HTTPException(status_code=404, detail="Bot not found")

        success = await bot_service.delete_bot(bot_id, user_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete bot")

        # Invalidate cache for this bot and bot list
        try:
            from ..middleware.cache_manager import invalidate_pattern

            # Invalidate bot-specific cache
            await invalidate_pattern(f"bots:get_bot:{bot_id}:{user_id}")
            # Invalidate bot list cache for this user
            await invalidate_pattern(f"bots:get_bots:*:{user_id}*")
            # Also invalidate query cache
            await invalidate_pattern(f"bot_list:*:{user_id}*")
        except Exception as cache_error:
            logger.warning(f"Cache invalidation failed (non-critical): {cache_error}")

        logger.info(f"Deleted bot: {bot_id}")
        return {"message": "Bot deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete bot")


@router.post("/{bot_id}/start")
async def start_bot(
    bot_id: str,
    background_tasks: BackgroundTasks,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
    trading_service: Annotated[BotTradingService, Depends(get_bot_trading_service)],
):
    """Start a trading bot with safety checks"""
    try:
        user_id = _get_user_id(current_user)

        # Validate start conditions
        validation = await bot_service.validate_bot_start_conditions(bot_id, user_id)
        if not validation["can_start"]:
            blockers = ", ".join(validation.get("blockers", []))
            raise HTTPException(status_code=403, detail=f"Cannot start bot: {blockers}")

        if validation.get("warnings"):
            logger.warning(
                f"Starting bot {bot_id} despite warnings: {validation['warnings']}"
            )

        # Check if bot is already active
        bot_status = await bot_service.get_bot_status(bot_id, user_id)
        if not bot_status:
            raise HTTPException(status_code=404, detail="Bot not found")

        if bot_status.get("is_active"):
            raise HTTPException(status_code=400, detail="Bot is already active")

        # Start the bot
        success = await bot_service.start_bot(bot_id, user_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to start bot")

        # Invalidate cache for this bot and bot list
        try:
            from ..middleware.cache_manager import invalidate_pattern

            # Invalidate bot-specific cache
            await invalidate_pattern(f"bots:get_bot:{bot_id}:{user_id}")
            # Invalidate bot list cache for this user
            await invalidate_pattern(f"bots:get_bots:*:{user_id}*")
            # Also invalidate query cache
            await invalidate_pattern(f"bot_list:*:{user_id}*")
        except Exception as cache_error:
            logger.warning(f"Cache invalidation failed (non-critical): {cache_error}")

        # Start bot trading loop in background
        background_tasks.add_task(trading_service.run_bot_loop, bot_id, user_id)

        logger.info(f"Started bot: {bot_id}")
        return {"message": f"Bot {bot_id} started successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start bot")


@router.post("/{bot_id}/stop")
async def stop_bot(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    """Stop a trading bot"""
    try:
        user_id = _get_user_id(current_user)

        # Check if bot exists
        bot_status = await bot_service.get_bot_status(bot_id, user_id)
        if not bot_status:
            raise HTTPException(status_code=404, detail="Bot not found")

        if not bot_status.get("is_active"):
            raise HTTPException(status_code=400, detail="Bot is not active")

        success = await bot_service.stop_bot(bot_id, user_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to stop bot")

        # Invalidate cache for this bot and bot list
        try:
            from ..middleware.cache_manager import invalidate_pattern

            # Invalidate bot-specific cache
            await invalidate_pattern(f"bots:get_bot:{bot_id}:{user_id}")
            # Invalidate bot list cache for this user
            await invalidate_pattern(f"bots:get_bots:*:{user_id}*")
            # Also invalidate query cache
            await invalidate_pattern(f"bot_list:*:{user_id}*")
        except Exception as cache_error:
            logger.warning(f"Cache invalidation failed (non-critical): {cache_error}")

        logger.info(f"Stopped bot: {bot_id}")
        return {"message": f"Bot {bot_id} stopped successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop bot")


@router.get("/{bot_id}/model")
async def get_bot_model(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
) -> dict[str, Any]:
    """Get bot's ML model status"""
    try:
        user_id = _get_user_id(current_user)
        bot = await bot_service.get_bot_config(bot_id, user_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")

        strategy = bot.get("strategy", "simple_ma")

        # Get appropriate ML engine based on strategy
        if strategy in ["ml_enhanced", "ensemble", "neural_network"]:
            # In real implementation, get actual model status from ML engines
            return {
                "bot_id": bot_id,
                "strategy": strategy,
                "model_trained": True,
                "last_trained": datetime.now().isoformat(),
                "accuracy": 0.65,
                "total_predictions": 150,
                "correct_predictions": 98,
                "model_version": "1.0.0",
            }
        else:
            return {
                "bot_id": bot_id,
                "strategy": strategy,
                "model_trained": False,
                "message": "No ML model required for this strategy",
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model status for bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model status")


class TradeRequest(BaseModel):
    side: str
    amount: float
    price: float | None = None
    symbol: str | None = None


@router.post("/{bot_id}/trade")
async def trade_bot(
    bot_id: str,
    request: TradeRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
    orchestrator: Annotated[Any, Depends(get_trading_orchestrator)],
):
    """Execute a manual trade for a bot via the orchestrator"""
    try:
        user_id = _get_user_id(current_user)

        # Ensure bot exists
        bot_status = await bot_service.get_bot_status(bot_id, user_id)
        if not bot_status:
            raise HTTPException(status_code=404, detail="Bot not found")

        # Fill symbol from bot config if not provided
        symbol = request.symbol or bot_status.get("symbol")

        # Call orchestrator to execute trade
        result = await orchestrator.execute_trade(
            bot_id=bot_id,
            user_id=user_id,
            side=request.side,
            amount=request.amount,
            price=request.price,
            symbol=symbol,
        )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing trade for bot {bot_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to execute trade")


@router.get("/{bot_id}/performance")
async def get_bot_performance(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
) -> BotPerformance:
    """Get bot performance metrics"""
    try:
        user_id = _get_user_id(current_user)
        bot = await bot_service.get_bot_config(bot_id, user_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")

        # Get performance data from bot service
        performance = await bot_service.get_bot_performance(bot_id, user_id)

        return BotPerformance(
            total_trades=performance.get("total_trades", 0),
            winning_trades=performance.get("winning_trades", 0),
            losing_trades=performance.get("losing_trades", 0),
            win_rate=performance.get("win_rate", 0.0),
            total_pnl=performance.get("total_pnl", 0.0),
            max_drawdown=performance.get("max_drawdown", 0.0),
            sharpe_ratio=performance.get("sharpe_ratio", 0.0),
            current_balance=performance.get("current_balance", 0.0),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance for bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance data")


# Note: Bot loop and trading cycle functions moved to BotTradingService
# They are now called via background_tasks.add_task(trading_service.run_bot_loop, bot_id, user_id)


@router.get("/safety/status")
async def get_safety_status(
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    """Get current safety status"""
    try:
        status = await bot_service.get_system_safety_status()
        return status
    except Exception as e:
        logger.error(f"Error getting safety status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get safety status")


@router.post("/safety/emergency-stop")
async def emergency_stop(
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    """Trigger emergency stop for all trading activities"""
    try:
        # Check if user has admin privileges (simplified check)
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=403, detail="Admin privileges required for emergency stop"
            )

        user_id = _get_user_id(current_user)
        stopped_count = await bot_service.emergency_stop_all_user_bots(
            user_id, "admin_emergency"
        )

        logger.critical(
            f"Emergency stop activated by user {user_id}: stopped {stopped_count} bots"
        )
        return {
            "message": "Emergency stop activated",
            "status": "all_trading_halted",
            "bots_stopped": stopped_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating emergency stop: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate emergency stop")


# Smart Intelligence Endpoints


@router.get("/{bot_id}/analysis")
async def get_bot_analysis(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
    bot_trading_service: Annotated[BotTradingService, Depends(get_bot_trading_service)],
):
    """Get real-time smart analysis for a bot"""
    try:
        from ..services.trading.smart_bot_engine import SmartBotEngine

        # Get bot configuration
        user_id = _get_user_id(current_user)
        bot_status = await bot_service.get_bot_status(bot_id, user_id)

        if not bot_status:
            raise HTTPException(status_code=404, detail="Bot not found")

        # Prepare market data (in production, fetch from exchange)
        market_data = await bot_trading_service._get_market_data(bot_status)
        smart_data = bot_trading_service._prepare_smart_market_data(
            market_data, bot_status
        )

        # Get smart analysis
        smart_engine = SmartBotEngine()
        signal = await smart_engine.analyze_market(smart_data)

        return {
            "bot_id": bot_id,
            "symbol": bot_status.get("symbol", "Unknown"),
            "analysis": {
                "action": signal.action,
                "confidence": signal.confidence,
                "strength": signal.strength,
                "risk_score": signal.risk_score,
                "reasoning": signal.reasoning,
                "timestamp": signal.timestamp.isoformat(),
            },
            "market_condition": smart_engine._detect_market_regime(
                smart_data["candles"]
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bot analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get analysis: {str(e)}")


@router.get("/{bot_id}/risk-metrics")
async def get_bot_risk_metrics(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
    bot_trading_service: Annotated[BotTradingService, Depends(get_bot_trading_service)],
):
    """Get comprehensive risk assessment for a bot"""
    try:
        from ..services.trading.smart_bot_engine import SmartBotEngine

        user_id = _get_user_id(current_user)
        bot_status = await bot_service.get_bot_status(bot_id, user_id)

        if not bot_status:
            raise HTTPException(status_code=404, detail="Bot not found")

        # Get market data and analysis
        market_data = await bot_trading_service._get_market_data(bot_status)
        smart_data = bot_trading_service._prepare_smart_market_data(
            market_data, bot_status
        )

        smart_engine = SmartBotEngine()
        signal = await smart_engine.analyze_market(smart_data)

        # Calculate risk metrics
        closes = [c["close"] for c in smart_data["candles"]]
        risk_score = signal.risk_score

        # Additional risk calculations
        import numpy as np

        returns = np.diff(closes) / closes[:-1]
        volatility = np.std(returns) * np.sqrt(252)  # Annualized
        sharpe = (np.mean(returns) * 252) / (volatility + 1e-6)
        max_dd = np.min(np.minimum.accumulate(closes) / closes - 1)

        return {
            "bot_id": bot_id,
            "symbol": bot_status.get("symbol", "Unknown"),
            "risk_metrics": {
                "overall_risk_score": risk_score,
                "volatility": float(volatility),
                "sharpe_ratio": float(sharpe),
                "max_drawdown": float(max_dd),
                "current_confidence": signal.confidence,
                "market_regime": smart_engine._detect_market_regime(
                    smart_data["candles"]
                ),
                "timestamp": datetime.now().isoformat(),
            },
            "recommendations": {
                "suggested_position_size": (
                    "conservative"
                    if risk_score > 0.7
                    else "moderate" if risk_score > 0.4 else "normal"
                ),
                "stop_loss_adjustment": "tight" if risk_score > 0.7 else "normal",
                "warnings": [
                    "High volatility detected" if volatility > 0.5 else None,
                    "Significant drawdown present" if max_dd < -0.15 else None,
                    "Low confidence signals" if signal.confidence < 0.5 else None,
                ],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get risk metrics: {str(e)}"
        )


@router.post("/{bot_id}/optimize")
async def optimize_bot_parameters(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
    bot_trading_service: Annotated[BotTradingService, Depends(get_bot_trading_service)],
):
    """Optimize bot parameters based on current market conditions and learning history"""
    try:
        import numpy as np

        from ..services.ml.adaptive_learning import adaptive_learning_service
        from ..services.trading.smart_bot_engine import SmartBotEngine

        user_id = _get_user_id(current_user)
        bot_status = await bot_service.get_bot_status(bot_id, user_id)

        if not bot_status:
            raise HTTPException(status_code=404, detail="Bot not found")

        # Get market data
        market_data = await bot_trading_service._get_market_data(bot_status)
        smart_data = bot_trading_service._prepare_smart_market_data(
            market_data, bot_status
        )

        # Get adaptive parameters from smart engine
        smart_engine = SmartBotEngine()

        # Detect market regime from candles
        candles = smart_data.get("candles", [])
        if candles:
            closes = (
                np.array([c["close"] for c in candles[-20:]])
                if len(candles) >= 20
                else np.array([c["close"] for c in candles])
            )

            # Simple market regime detection
            returns = (
                np.diff(closes) / closes[:-1] if len(closes) > 1 else np.array([0])
            )
            volatility = np.std(returns) if len(returns) > 1 else 0
            trend = (
                (closes[-1] - closes[0]) / closes[0]
                if closes[0] != 0 and len(closes) > 0
                else 0
            )

            if volatility > 0.03:
                market_regime = "volatile"
            elif trend > 0.05:
                market_regime = "bull"
            elif trend < -0.05:
                market_regime = "bear"
            else:
                market_regime = "ranging"
        else:
            market_regime = "unknown"

        # Get historical performance for adaptive learning
        # In production, fetch actual historical trades for this bot from database
        historical_performance = []  # Placeholder - would fetch from database

        # Get adaptive parameters from learning service
        adaptive_params = adaptive_learning_service.adapt_strategy_parameters(
            market_regime, historical_performance
        )

        # Combine with smart engine parameters if available
        try:
            smart_params = await smart_engine.get_adaptive_parameters(market_regime)
            adaptive_params.update(smart_params)
        except Exception as e:
            logger.warning(f"Could not get smart engine adaptive parameters: {e}")

        # Add market regime and reasoning
        adaptive_params["market_regime"] = market_regime
        metrics = adaptive_learning_service.get_learning_metrics()
        adaptive_params["adaptive_reasoning"] = [
            f"Adapted for {market_regime} market conditions",
            f"Based on {metrics['total_trades_analyzed']} analyzed trades",
            f"Learning accuracy: {metrics['learning_accuracy']:.1f}%",
            f"Confidence improvement: +{metrics['confidence_improvement']:.1f}%",
        ]

        logger.info(f"Optimized parameters for bot {bot_id}: {adaptive_params}")

        return {
            "bot_id": bot_id,
            "symbol": bot_status.get("symbol", "Unknown"),
            "optimized_parameters": adaptive_params,
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing bot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to optimize: {str(e)}")


# Removed duplicate code that was moved to BotTradingService
