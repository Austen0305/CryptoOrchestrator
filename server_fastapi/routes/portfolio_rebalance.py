"""
Portfolio Rebalancing Engine
Auto-optimize asset allocation based on risk tolerance and market conditions
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolio/rebalance", tags=["Portfolio Rebalancing"])


class RebalanceStrategy(str, Enum):
    """Rebalancing strategies"""
    EQUAL_WEIGHT = "equal_weight"
    RISK_PARITY = "risk_parity"
    MARKET_CAP = "market_cap"
    MOMENTUM = "momentum"
    MEAN_VARIANCE = "mean_variance"
    TARGET_ALLOCATION = "target_allocation"


class RebalanceFrequency(str, Enum):
    """Rebalancing frequencies"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    THRESHOLD = "threshold"  # Rebalance when drift exceeds threshold


class AssetTarget(BaseModel):
    """Target allocation for an asset"""
    symbol: str
    target_weight: float = Field(..., ge=0, le=1, description="Target weight (0-1)")
    min_weight: Optional[float] = Field(None, ge=0, le=1)
    max_weight: Optional[float] = Field(None, ge=0, le=1)


class RebalanceConfig(BaseModel):
    """Portfolio rebalancing configuration"""
    strategy: RebalanceStrategy
    frequency: RebalanceFrequency
    threshold_percent: float = Field(5.0, description="Drift threshold for threshold-based rebalancing")
    target_allocations: Optional[List[AssetTarget]] = None
    risk_tolerance: Literal["conservative", "moderate", "aggressive"] = "moderate"
    min_trade_size_usd: float = Field(10.0, description="Minimum trade size in USD")
    max_slippage_percent: float = Field(0.5, description="Maximum allowed slippage")
    dry_run: bool = Field(False, description="Simulate without executing trades")


class AssetAllocation(BaseModel):
    """Current asset allocation"""
    symbol: str
    current_value_usd: float
    current_weight: float
    target_weight: float
    drift_percent: float
    action: Literal["buy", "sell", "hold"]
    trade_amount_usd: Optional[float] = None


class RebalanceResult(BaseModel):
    """Rebalancing execution result"""
    rebalance_id: str
    timestamp: str
    strategy: str
    total_portfolio_value: float
    allocations: List[AssetAllocation]
    trades_executed: int
    total_fees: float
    estimated_slippage: float
    status: Literal["completed", "partial", "failed"]
    dry_run: bool
    execution_time_seconds: float


class RebalanceSchedule(BaseModel):
    """Scheduled rebalancing configuration"""
    id: str
    user_id: str
    config: RebalanceConfig
    enabled: bool
    next_run: str
    last_run: Optional[str] = None
    created_at: str


# Store scheduled rebalances (in production, use database)
scheduled_rebalances: Dict[str, RebalanceSchedule] = {}


class PortfolioRebalancer:
    """Portfolio rebalancing engine"""
    
    def __init__(self):
        self.rebalance_history: List[RebalanceResult] = []
    
    async def calculate_target_allocations(
        self,
        portfolio: Dict[str, float],
        config: RebalanceConfig
    ) -> Dict[str, float]:
        """Calculate target allocations based on strategy"""
        
        if config.strategy == RebalanceStrategy.EQUAL_WEIGHT:
            return await self._equal_weight_allocation(portfolio)
        
        elif config.strategy == RebalanceStrategy.RISK_PARITY:
            return await self._risk_parity_allocation(portfolio)
        
        elif config.strategy == RebalanceStrategy.MARKET_CAP:
            return await self._market_cap_allocation(portfolio)
        
        elif config.strategy == RebalanceStrategy.MOMENTUM:
            return await self._momentum_allocation(portfolio)
        
        elif config.strategy == RebalanceStrategy.MEAN_VARIANCE:
            return await self._mean_variance_allocation(portfolio, config.risk_tolerance)
        
        elif config.strategy == RebalanceStrategy.TARGET_ALLOCATION:
            if not config.target_allocations:
                raise ValueError("Target allocations required for TARGET_ALLOCATION strategy")
            return {
                asset.symbol: asset.target_weight
                for asset in config.target_allocations
            }
        
        else:
            raise ValueError(f"Unknown strategy: {config.strategy}")
    
    async def _equal_weight_allocation(self, portfolio: Dict[str, float]) -> Dict[str, float]:
        """Equal weight allocation"""
        n_assets = len(portfolio)
        return {symbol: 1.0 / n_assets for symbol in portfolio.keys()}
    
    async def _risk_parity_allocation(self, portfolio: Dict[str, float]) -> Dict[str, float]:
        """Risk parity allocation - weight assets inversely to their volatility"""
        # Fetch volatility data for each asset
        volatilities = {}
        for symbol in portfolio.keys():
            vol = await self._get_asset_volatility(symbol)
            volatilities[symbol] = vol
        
        # Calculate inverse volatility weights
        inv_vols = {s: 1.0 / v for s, v in volatilities.items()}
        total_inv_vol = sum(inv_vols.values())
        
        return {symbol: inv_vol / total_inv_vol for symbol, inv_vol in inv_vols.items()}
    
    async def _market_cap_allocation(self, portfolio: Dict[str, float]) -> Dict[str, float]:
        """Market cap weighted allocation"""
        market_caps = {}
        for symbol in portfolio.keys():
            cap = await self._get_market_cap(symbol)
            market_caps[symbol] = cap
        
        total_cap = sum(market_caps.values())
        return {symbol: cap / total_cap for symbol, cap in market_caps.items()}
    
    async def _momentum_allocation(self, portfolio: Dict[str, float]) -> Dict[str, float]:
        """Momentum-based allocation - overweight assets with positive momentum"""
        momentum_scores = {}
        for symbol in portfolio.keys():
            momentum = await self._calculate_momentum(symbol)
            momentum_scores[symbol] = max(0, momentum)  # Only positive momentum
        
        total_momentum = sum(momentum_scores.values())
        if total_momentum == 0:
            return await self._equal_weight_allocation(portfolio)
        
        return {symbol: score / total_momentum for symbol, score in momentum_scores.items()}
    
    async def _mean_variance_allocation(
        self,
        portfolio: Dict[str, float],
        risk_tolerance: str
    ) -> Dict[str, float]:
        """Mean-variance optimization (Markowitz)"""
        # Fetch expected returns and covariance matrix
        expected_returns = {}
        for symbol in portfolio.keys():
            ret = await self._get_expected_return(symbol)
            expected_returns[symbol] = ret
        
        # Simplified allocation based on risk tolerance
        risk_multiplier = {"conservative": 0.5, "moderate": 1.0, "aggressive": 1.5}[risk_tolerance]
        
        # Weight by expected return adjusted for risk tolerance
        weighted_returns = {s: r * risk_multiplier for s, r in expected_returns.items()}
        total_weighted = sum(max(0, r) for r in weighted_returns.values())
        
        if total_weighted == 0:
            return await self._equal_weight_allocation(portfolio)
        
        return {
            symbol: max(0, weighted_returns[symbol]) / total_weighted
            for symbol in portfolio.keys()
        }
    
    async def _get_asset_volatility(self, symbol: str) -> float:
        """Get 30-day volatility for asset"""
        # Mock implementation - in production, calculate from price data
        import random
        return random.uniform(0.1, 0.5)  # 10-50% volatility
    
    async def _get_market_cap(self, symbol: str) -> float:
        """Get market cap for asset"""
        # Mock implementation
        import random
        return random.uniform(1_000_000_000, 1_000_000_000_000)
    
    async def _calculate_momentum(self, symbol: str) -> float:
        """Calculate 12-month momentum"""
        # Mock implementation - calculate actual returns
        import random
        return random.uniform(-0.5, 0.5)  # -50% to +50%
    
    async def _get_expected_return(self, symbol: str) -> float:
        """Get expected return for asset"""
        # Mock implementation - use historical or forecast data
        import random
        return random.uniform(-0.1, 0.3)  # -10% to +30%
    
    async def execute_rebalance(
        self,
        user_id: str,
        portfolio: Dict[str, float],
        config: RebalanceConfig
    ) -> RebalanceResult:
        """Execute portfolio rebalancing"""
        start_time = datetime.now()
        
        # Calculate total portfolio value
        total_value = sum(portfolio.values())
        
        # Calculate target allocations
        target_allocations = await self.calculate_target_allocations(portfolio, config)
        
        # Calculate current weights
        current_weights = {
            symbol: value / total_value
            for symbol, value in portfolio.items()
        }
        
        # Determine trades needed
        allocations = []
        trades_to_execute = []
        
        for symbol in portfolio.keys():
            current_weight = current_weights.get(symbol, 0)
            target_weight = target_allocations.get(symbol, 0)
            drift = ((target_weight - current_weight) / current_weight * 100) if current_weight > 0 else 0
            
            # Determine action
            if abs(drift) < config.threshold_percent / 2:
                action = "hold"
                trade_amount = None
            elif target_weight > current_weight:
                action = "buy"
                trade_amount = (target_weight - current_weight) * total_value
            else:
                action = "sell"
                trade_amount = (current_weight - target_weight) * total_value
            
            # Only trade if above minimum size
            if trade_amount and abs(trade_amount) >= config.min_trade_size_usd:
                trades_to_execute.append({
                    "symbol": symbol,
                    "action": action,
                    "amount_usd": abs(trade_amount)
                })
            else:
                action = "hold"
                trade_amount = None
            
            allocations.append(AssetAllocation(
                symbol=symbol,
                current_value_usd=portfolio[symbol],
                current_weight=current_weight,
                target_weight=target_weight,
                drift_percent=drift,
                action=action,
                trade_amount_usd=trade_amount
            ))
        
        # Execute trades (or simulate in dry run mode)
        trades_executed = 0
        total_fees = 0.0
        estimated_slippage = 0.0
        
        if not config.dry_run and trades_to_execute:
            for trade in trades_to_execute:
                try:
                    # Execute trade via exchange service
                    result = await self._execute_trade(user_id, trade)
                    trades_executed += 1
                    total_fees += result.get("fee", 0)
                    estimated_slippage += result.get("slippage", 0)
                except Exception as e:
                    logger.error(f"Failed to execute trade: {e}")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        result = RebalanceResult(
            rebalance_id=f"rebalance_{user_id}_{int(datetime.now().timestamp())}",
            timestamp=datetime.now().isoformat(),
            strategy=config.strategy.value,
            total_portfolio_value=total_value,
            allocations=allocations,
            trades_executed=trades_executed if not config.dry_run else 0,
            total_fees=total_fees,
            estimated_slippage=estimated_slippage,
            status="completed" if trades_executed == len(trades_to_execute) else "partial",
            dry_run=config.dry_run,
            execution_time_seconds=execution_time
        )
        
        self.rebalance_history.append(result)
        return result
    
    async def _execute_trade(self, user_id: str, trade: dict) -> dict:
        """Execute a single trade"""
        # Mock implementation - integrate with exchange service
        return {
            "success": True,
            "fee": trade["amount_usd"] * 0.001,  # 0.1% fee
            "slippage": trade["amount_usd"] * 0.0005  # 0.05% slippage
        }


# Global rebalancer instance
rebalancer = PortfolioRebalancer()


@router.post("/analyze", response_model=RebalanceResult)
async def analyze_rebalance(
    user_id: str,
    portfolio: Dict[str, float],
    config: RebalanceConfig
):
    """
    Analyze portfolio and recommend rebalancing actions
    
    Does not execute trades - use for preview only
    """
    try:
        # Force dry run for analysis
        config.dry_run = True
        
        result = await rebalancer.execute_rebalance(user_id, portfolio, config)
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing rebalance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=RebalanceResult)
async def execute_rebalance(
    user_id: str,
    portfolio: Dict[str, float],
    config: RebalanceConfig,
    background_tasks: BackgroundTasks
):
    """
    Execute portfolio rebalancing
    
    Trades will be executed immediately based on configuration
    """
    try:
        result = await rebalancer.execute_rebalance(user_id, portfolio, config)
        
        # Log rebalance event
        background_tasks.add_task(
            log_rebalance_event,
            user_id,
            result
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error executing rebalance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule", response_model=RebalanceSchedule)
async def schedule_rebalance(
    user_id: str,
    config: RebalanceConfig
):
    """
    Schedule automatic portfolio rebalancing
    
    Portfolio will be rebalanced according to frequency setting
    """
    schedule_id = f"schedule_{user_id}_{int(datetime.now().timestamp())}"
    
    # Calculate next run time
    next_run = calculate_next_run(config.frequency)
    
    schedule = RebalanceSchedule(
        id=schedule_id,
        user_id=user_id,
        config=config,
        enabled=True,
        next_run=next_run.isoformat(),
        created_at=datetime.now().isoformat()
    )
    
    scheduled_rebalances[schedule_id] = schedule
    
    logger.info(f"Scheduled rebalance for user {user_id}: {schedule_id}")
    
    return schedule


@router.get("/schedules/{user_id}", response_model=List[RebalanceSchedule])
async def get_user_schedules(user_id: str):
    """Get all scheduled rebalances for a user"""
    user_schedules = [
        schedule for schedule in scheduled_rebalances.values()
        if schedule.user_id == user_id
    ]
    return user_schedules


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    """Delete a scheduled rebalance"""
    if schedule_id in scheduled_rebalances:
        del scheduled_rebalances[schedule_id]
        return {"success": True, "message": "Schedule deleted"}
    raise HTTPException(status_code=404, detail="Schedule not found")


@router.get("/history/{user_id}", response_model=List[RebalanceResult])
async def get_rebalance_history(user_id: str, limit: int = 50):
    """Get rebalancing history for a user"""
    # Filter history by user_id
    user_history = [
        result for result in rebalancer.rebalance_history
        if user_id in result.rebalance_id
    ]
    return user_history[-limit:]


def calculate_next_run(frequency: RebalanceFrequency) -> datetime:
    """Calculate next rebalance execution time"""
    now = datetime.now()
    
    if frequency == RebalanceFrequency.DAILY:
        return now + timedelta(days=1)
    elif frequency == RebalanceFrequency.WEEKLY:
        return now + timedelta(weeks=1)
    elif frequency == RebalanceFrequency.MONTHLY:
        return now + timedelta(days=30)
    elif frequency == RebalanceFrequency.QUARTERLY:
        return now + timedelta(days=90)
    else:  # THRESHOLD
        return now + timedelta(hours=1)  # Check every hour


async def log_rebalance_event(user_id: str, result: RebalanceResult):
    """Log rebalancing event for audit trail"""
    logger.info(f"Rebalance completed for user {user_id}: {result.rebalance_id}")
    # In production, save to database
