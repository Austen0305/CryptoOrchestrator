"""
Strategy Routes - API endpoints for strategy management
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import uuid

from ..services.strategy.template_service import StrategyTemplateService, StrategyType, StrategyCategory
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strategies", tags=["Strategies"])


# Pydantic models
class StrategyBase(BaseModel):
    name: str
    description: Optional[str] = None
    strategy_type: str
    category: str
    config: Dict[str, Any] = Field(default_factory=dict)
    logic: Optional[Dict[str, Any]] = None


class StrategyCreate(StrategyBase):
    """Create strategy request"""
    template_id: Optional[str] = None  # If creating from template


class StrategyUpdate(BaseModel):
    """Update strategy request"""
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    logic: Optional[Dict[str, Any]] = None


class StrategyResponse(StrategyBase):
    """Strategy response"""
    id: str
    user_id: int
    version: str
    parent_strategy_id: Optional[str] = None
    is_template: bool = False
    is_public: bool = False
    is_published: bool = False
    backtest_sharpe_ratio: Optional[float] = None
    backtest_win_rate: Optional[float] = None
    backtest_total_return: Optional[float] = None
    backtest_max_drawdown: Optional[float] = None
    usage_count: int = 0
    rating: float = 0.0
    rating_count: int = 0
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StrategyVersionResponse(BaseModel):
    """Strategy version response"""
    id: str
    strategy_id: str
    version: str
    name: str
    config: Dict[str, Any]
    logic: Optional[Dict[str, Any]] = None
    change_description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


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
strategies_db: Dict[str, StrategyResponse] = {}
strategy_versions_db: Dict[str, List[StrategyVersionResponse]] = {}


@router.get("/templates", response_model=List[Dict])
async def get_templates(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all strategy templates"""
    try:
        if category:
            templates = StrategyTemplateService.get_templates_by_category(category)
        else:
            templates = StrategyTemplateService.get_all_templates()
        return templates
    except Exception as e:
        logger.error(f"Error fetching templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch templates")


@router.get("/templates/{template_id}", response_model=Dict)
async def get_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific template"""
    try:
        template = StrategyTemplateService.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching template: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch template")


@router.post("", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    strategy: StrategyCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new strategy"""
    try:
        # If creating from template, load template config
        if strategy.template_id:
            template = StrategyTemplateService.get_template(strategy.template_id)
            if not template:
                raise HTTPException(status_code=404, detail="Template not found")
            # Merge template config with user overrides
            strategy.config = {**template.config, **strategy.config}
            strategy.logic = strategy.logic or template.logic
            strategy.strategy_type = strategy.strategy_type or template.strategy_type.value
            strategy.category = strategy.category or template.category.value
            if not strategy.name:
                strategy.name = f"{template.name} (Custom)"
            if not strategy.description:
                strategy.description = template.description
        
        strategy_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        new_strategy = StrategyResponse(
            id=strategy_id,
            user_id=current_user["id"],
            name=strategy.name,
            description=strategy.description,
            strategy_type=strategy.strategy_type,
            category=strategy.category,
            config=strategy.config,
            logic=strategy.logic,
            version="1.0.0",
            created_at=now,
            updated_at=now
        )
        
        strategies_db[strategy_id] = new_strategy
        return new_strategy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating strategy: {e}")
        raise HTTPException(status_code=500, detail="Failed to create strategy")


@router.get("", response_model=List[StrategyResponse])
async def list_strategies(
    current_user: dict = Depends(get_current_user),
    include_public: bool = False
):
    """List user's strategies"""
    try:
        user_strategies = [
            s for s in strategies_db.values()
            if s.user_id == current_user["id"] or (include_public and s.is_public)
        ]
        return user_strategies
    except Exception as e:
        logger.error(f"Error listing strategies: {e}")
        raise HTTPException(status_code=500, detail="Failed to list strategies")


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific strategy"""
    try:
        strategy = strategies_db.get(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Check access
        if strategy.user_id != current_user["id"] and not strategy.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return strategy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching strategy: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch strategy")


@router.patch("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: str,
    updates: StrategyUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a strategy"""
    try:
        strategy = strategies_db.get(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        if strategy.user_id != current_user["id"]:
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
            created_at=datetime.utcnow()
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
        
        strategy.updated_at = datetime.utcnow()
        
        return strategy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating strategy: {e}")
        raise HTTPException(status_code=500, detail="Failed to update strategy")


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a strategy"""
    try:
        strategy = strategies_db.get(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        if strategy.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        del strategies_db[strategy_id]
        if strategy_id in strategy_versions_db:
            del strategy_versions_db[strategy_id]
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting strategy: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete strategy")


@router.get("/{strategy_id}/versions", response_model=List[StrategyVersionResponse])
async def get_strategy_versions(
    strategy_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get strategy version history"""
    try:
        strategy = strategies_db.get(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        if strategy.user_id != current_user["id"] and not strategy.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        versions = strategy_versions_db.get(strategy_id, [])
        return versions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching strategy versions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch versions")


@router.post("/{strategy_id}/backtest", response_model=BacktestResponse)
async def backtest_strategy(
    strategy_id: str,
    backtest_request: BacktestRequest,
    current_user: dict = Depends(get_current_user)
):
    """Backtest a strategy"""
    try:
        strategy = strategies_db.get(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        if strategy.user_id != current_user["id"] and not strategy.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # TODO: Integrate with actual backtesting engine
        # For now, return mock results
        mock_results = BacktestResponse(
            strategy_id=strategy_id,
            sharpe_ratio=1.85,
            win_rate=0.65,
            total_return=0.25,
            max_drawdown=0.12,
            total_trades=150,
            winning_trades=98,
            losing_trades=52
        )
        
        return mock_results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error backtesting strategy: {e}")
        raise HTTPException(status_code=500, detail="Failed to backtest strategy")


@router.post("/{strategy_id}/publish", response_model=StrategyResponse)
async def publish_strategy(
    strategy_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Publish strategy to marketplace"""
    try:
        strategy = strategies_db.get(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        if strategy.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        strategy.is_public = True
        strategy.is_published = True
        strategy.published_at = datetime.utcnow()
        
        return strategy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing strategy: {e}")
        raise HTTPException(status_code=500, detail="Failed to publish strategy")
