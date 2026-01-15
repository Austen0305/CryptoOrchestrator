"""
Strategy Routes - API endpoints for strategy management
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..services.strategy.template_service import (
    StrategyTemplateService,
)
from ..utils.response_optimizer import ResponseOptimizer
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strategies", tags=["Strategies"])


# Pydantic models
class StrategyBase(BaseModel):
    name: str
    description: str | None = None
    strategy_type: str
    category: str
    config: dict[str, Any] = Field(default_factory=dict)
    logic: dict[str, Any] | None = None


class StrategyCreate(StrategyBase):
    """Create strategy request"""

    template_id: str | None = None  # If creating from template


class StrategyUpdate(BaseModel):
    """Update strategy request"""

    name: str | None = None
    description: str | None = None
    config: dict[str, Any] | None = None
    logic: dict[str, Any] | None = None


class StrategyResponse(StrategyBase):
    """Strategy response"""

    id: str
    user_id: int
    version: str
    parent_strategy_id: str | None = None
    is_template: bool = False
    is_public: bool = False
    is_published: bool = False
    backtest_sharpe_ratio: float | None = None
    backtest_win_rate: float | None = None
    backtest_total_return: float | None = None
    backtest_max_drawdown: float | None = None
    usage_count: int = 0
    rating: float = 0.0
    rating_count: int = 0
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class StrategyVersionResponse(BaseModel):
    """Strategy version response"""

    id: str
    strategy_id: str
    version: str
    name: str
    config: dict[str, Any]
    logic: dict[str, Any] | None = None
    change_description: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BacktestRequest(BaseModel):
    """Backtest strategy request"""

    strategy_id: str
    start_date: str
    end_date: str
    initial_balance: float = 10000.0
    trading_pair: str = "BTC/USD"


class BacktestResponse(BaseModel):
    """Backtest results"""

    strategy_id: str
    sharpe_ratio: float
    win_rate: float
    total_return: float
    max_drawdown: float
    total_trades: int
    winning_trades: int
    losing_trades: int


# In-memory storage (replace with database in production)
strategies_db: dict[str, StrategyResponse] = {}
strategy_versions_db: dict[str, list[StrategyVersionResponse]] = {}


@router.get("/templates", response_model=list[dict])
@cached(ttl=300, prefix="strategies_templates")  # 5min TTL for templates
async def get_templates(
    current_user: Annotated[dict, Depends(get_current_user)],
    category: str | None = None,
):
    """Get all strategy templates"""
    try:
        _get_user_id(current_user)
        if category:
            templates = StrategyTemplateService.get_templates_by_category(category)
        else:
            templates = StrategyTemplateService.get_all_templates()
        return templates
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch templates")


@router.get("/templates/{template_id}", response_model=dict)
@cached(ttl=300, prefix="strategies_template")
async def get_template(
    template_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get a specific template"""
    try:
        user_id = _get_user_id(current_user)
        template = StrategyTemplateService.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching template: {e}", exc_info=True, extra={"user_id": user_id}
        )
        raise HTTPException(status_code=500, detail="Failed to fetch template")


@router.post("", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    strategy: StrategyCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Create a new strategy"""
    try:
        user_id = _get_user_id(current_user)
        # If creating from template, load template config
        if strategy.template_id:
            template = StrategyTemplateService.get_template(strategy.template_id)
            if not template:
                raise HTTPException(status_code=404, detail="Template not found")
            # Merge template config with user overrides
            strategy.config = {**template.config, **strategy.config}
            strategy.logic = strategy.logic or template.logic
            strategy.strategy_type = (
                strategy.strategy_type or template.strategy_type.value
            )
            strategy.category = strategy.category or template.category.value
            if not strategy.name:
                strategy.name = f"{template.name} (Custom)"
            if not strategy.description:
                strategy.description = template.description

        strategy_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        new_strategy = StrategyResponse(
            id=strategy_id,
            user_id=(
                int(user_id) if user_id.isdigit() else 1
            ),  # Convert to int for compatibility
            name=strategy.name,
            description=strategy.description,
            strategy_type=strategy.strategy_type,
            category=strategy.category,
            config=strategy.config,
            logic=strategy.logic,
            version="1.0.0",
            created_at=now,
            updated_at=now,
        )

        strategies_db[strategy_id] = new_strategy
        return new_strategy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error creating strategy: {e}",
            exc_info=True,
            extra={"user_id": user_id if "user_id" in locals() else None},
        )
        raise HTTPException(status_code=500, detail="Failed to create strategy")


@router.get("", response_model=list[StrategyResponse])
@cached(ttl=120, prefix="strategies_list")
async def list_strategies(
    current_user: Annotated[dict, Depends(get_current_user)],
    include_public: bool = Query(False, description="Include public strategies"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """List user's strategies with pagination"""
    try:
        user_id = _get_user_id(current_user)
        user_id_int = int(user_id) if user_id.isdigit() else 1
        all_strategies = [
            s
            for s in strategies_db.values()
            if s.user_id == user_id_int or (include_public and s.is_public)
        ]

        # Apply pagination
        total = len(all_strategies)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_strategies = all_strategies[start:end]

        # Return paginated response
        return ResponseOptimizer.paginate_response(
            paginated_strategies, page, page_size, total
        )["data"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error listing strategies: {e}",
            exc_info=True,
            extra={"user_id": user_id if "user_id" in locals() else None},
        )
        raise HTTPException(status_code=500, detail="Failed to list strategies")


@router.get("/{strategy_id}", response_model=StrategyResponse)
@cached(ttl=120, prefix="strategies")
async def get_strategy(
    strategy_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get a specific strategy"""
    try:
        user_id = _get_user_id(current_user)
        user_id_int = int(user_id) if user_id.isdigit() else 1
        strategy = strategies_db.get(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")

        # Check access
        if strategy.user_id != user_id_int and not strategy.is_public:
            raise HTTPException(status_code=403, detail="Access denied")

        return strategy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching strategy: {e}",
            exc_info=True,
            extra={"user_id": user_id if "user_id" in locals() else None},
        )
        raise HTTPException(status_code=500, detail="Failed to fetch strategy")


@router.patch("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: str,
    updates: StrategyUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Update a strategy"""
    try:
        user_id = _get_user_id(current_user)
        user_id_int = int(user_id) if user_id.isdigit() else 1
        strategy = strategies_db.get(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")

        if strategy.user_id != user_id_int:
            raise HTTPException(status_code=403, detail="Access denied")

        # Create version snapshot before update
        version_id = str(uuid.uuid4())
        version = StrategyVersionResponse(
            id=version_id,
            strategy_id=strategy_id,
            version=strategy.version,
            name=strategy.name,
            config=strategy.config,
            logic=strategy.logic,
            created_at=datetime.now(UTC),
        )

        if strategy_id not in strategy_versions_db:
            strategy_versions_db[strategy_id] = []
        strategy_versions_db[strategy_id].append(version)

        # Update strategy
        update_data = updates.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(strategy, key, value)

        # Increment version
        version_parts = strategy.version.split(".")
        if len(version_parts) == 3:
            patch_version = int(version_parts[2]) + 1
            strategy.version = f"{version_parts[0]}.{version_parts[1]}.{patch_version}"

        strategy.updated_at = datetime.now(UTC)

        return strategy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error updating strategy: {e}",
            exc_info=True,
            extra={"user_id": user_id, "strategy_id": strategy_id},
        )
        raise HTTPException(status_code=500, detail="Failed to update strategy")


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Delete a strategy"""
    try:
        user_id = _get_user_id(current_user)
        user_id_int = int(user_id) if user_id.isdigit() else 1
        strategy = strategies_db.get(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")

        if strategy.user_id != user_id_int:
            raise HTTPException(status_code=403, detail="Access denied")

        del strategies_db[strategy_id]
        if strategy_id in strategy_versions_db:
            del strategy_versions_db[strategy_id]

        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error deleting strategy: {e}",
            exc_info=True,
            extra={"user_id": user_id, "strategy_id": strategy_id},
        )
        raise HTTPException(status_code=500, detail="Failed to delete strategy")


@router.get("/{strategy_id}/versions", response_model=list[StrategyVersionResponse])
@cached(ttl=120, prefix="strategies_versions")
async def get_strategy_versions(
    strategy_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get strategy version history"""
    try:
        user_id = _get_user_id(current_user)
        user_id_int = int(user_id) if user_id.isdigit() else 1
        strategy = strategies_db.get(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")

        if strategy.user_id != user_id_int and not strategy.is_public:
            raise HTTPException(status_code=403, detail="Access denied")

        versions = strategy_versions_db.get(strategy_id, [])
        return versions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching strategy versions: {e}",
            exc_info=True,
            extra={"user_id": user_id, "strategy_id": strategy_id},
        )
        raise HTTPException(status_code=500, detail="Failed to fetch versions")


@router.post("/{strategy_id}/backtest", response_model=BacktestResponse)
async def backtest_strategy(
    strategy_id: str,
    backtest_request: BacktestRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Backtest a strategy"""
    try:
        user_id = _get_user_id(current_user)
        user_id_int = int(user_id) if user_id.isdigit() else 1
        strategy = strategies_db.get(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")

        if strategy.user_id != user_id_int and not strategy.is_public:
            raise HTTPException(status_code=403, detail="Access denied")

        # Integrate with backtesting engine
        try:
            from ..services.backtesting_engine import BacktestConfig, BacktestingEngine

            engine = BacktestingEngine()

            # Create backtest config from request
            config = BacktestConfig(
                botId=strategy_id,
                initialBalance=backtest_request.initial_balance or 10000.0,
                commission=backtest_request.commission or 0.001,
            )

            # Run backtest (requires historical data - for now use mock if data unavailable)
            # In a full implementation, fetch historical candles for the strategy's symbol
            result = await engine.run_backtest(
                config, []
            )  # Empty data will use fallback

            return BacktestResponse(
                strategy_id=strategy_id,
                sharpe_ratio=result.sharpeRatio,
                win_rate=result.winRate,
                total_return=result.totalReturn,
                max_drawdown=result.maxDrawdown,
                total_trades=result.totalTrades,
                winning_trades=int(result.totalTrades * result.winRate),
                losing_trades=int(result.totalTrades * (1 - result.winRate)),
            )
        except Exception as e:
            logger.error(
                f"Backtesting engine integration failed: {e}",
                exc_info=True,
            )
            # Return error response instead of mock data
            raise HTTPException(
                status_code=503,
                detail="Backtesting service unavailable. Please try again later.",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error backtesting strategy: {e}",
            exc_info=True,
            extra={"user_id": user_id, "strategy_id": strategy_id},
        )
        raise HTTPException(status_code=500, detail="Failed to backtest strategy")


@router.post("/{strategy_id}/publish", response_model=StrategyResponse)
async def publish_strategy(
    strategy_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Publish strategy to marketplace"""
    try:
        user_id = _get_user_id(current_user)
        user_id_int = int(user_id) if user_id.isdigit() else 1
        strategy = strategies_db.get(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")

        if strategy.user_id != user_id_int:
            raise HTTPException(status_code=403, detail="Access denied")

        strategy.is_public = True
        strategy.is_published = True
        strategy.published_at = datetime.now(UTC)

        return strategy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error publishing strategy: {e}",
            exc_info=True,
            extra={"user_id": user_id, "strategy_id": strategy_id},
        )
        raise HTTPException(status_code=500, detail="Failed to publish strategy")
