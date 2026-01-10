import logging
import asyncio
from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.risk_repository import RiskRepository

logger = logging.getLogger(__name__)


class BotConfig(BaseModel):
    risk_per_trade: float
    stop_loss: float
    take_profit: float


class Trade(BaseModel):
    id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    amount: float
    price: float
    timestamp: int
    total: float
    total_with_fee: float
    fee: float
    pnl: float | None = None


class Portfolio(BaseModel):
    total_balance: float
    available_balance: float
    positions: dict[str, dict[str, Any]]
    successful_trades: int | None = 0
    failed_trades: int | None = 0


class MarketData(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class RiskMetrics(BaseModel):
    current_drawdown: float
    max_drawdown: float
    daily_loss: float
    position_size: float
    total_exposure: float
    risk_per_trade: float


class RiskLimits(BaseModel):
    max_drawdown: float = 0.10  # 10% max drawdown
    max_daily_loss: float = 0.05  # 5% max daily loss
    max_position_size: float = 0.10  # 10% of portfolio per position
    max_total_exposure: float = 0.50  # 50% max total exposure
    stop_loss_multiplier: float = 1.5  # Stop loss at 1.5x risk per trade
    take_profit_multiplier: float = 3.0  # Take profit at 3x risk per trade
    min_position_size: float = (
        0.0001  # Minimum position size for micro trading (0.01% of portfolio)
    )
    micro_mode_enabled: bool = True  # Enable micro trading mode by default
    persistent_mode: bool = (
        True  # Enable persistent mode - bots don't stop automatically
    )


class RiskManagementEngine:
    def __init__(self, db: AsyncSession | None = None):
        self.db = db
        self.default_limits = RiskLimits()
        self.historical_volatility: float = 0.0
        self.last_volatility_update: int = 0
        self.volatility_update_interval = 1000 * 60 * 15  # 15 minutes in milliseconds
        # ✅ Repository injected via dependency injection (Service Layer Pattern)
        self._risk_repository: RiskRepository | None = RiskRepository()

    async def update_historical_volatility(self, exchange_service: Any = None) -> None:
        """Update historical volatility from exchange data"""
        now = int(datetime.utcnow().timestamp() * 1000)
        if now - self.last_volatility_update < self.volatility_update_interval:
            return

        try:
            # Use injected service or fallback to singleton
            from ..services.market_data import get_market_data_service

            market_service = exchange_service or get_market_data_service()

            # Use BTC/USD as proxy for overall market volatility if no specific symbol provided
            # (In a real system we'd calculate per-symbol volatility)
            candles = await market_service.get_backfill("BTC/USD", 0)

            if not candles:
                # If no data yet, use default but don't crash
                logger.debug("No market data available for volatility calculation yet")
                return

            # Convert to MarketData objects
            historical_data = [
                MarketData(
                    timestamp=c[0],
                    open=c[1],
                    high=c[2],
                    low=c[3],
                    close=c[4],
                    volume=c[5],
                )
                for c in candles
            ]

            if historical_data:
                self.historical_volatility = self.calculate_volatility_index(
                    historical_data
                )
                self.last_volatility_update = now
                logger.info(
                    f"Updated historical volatility: {self.historical_volatility:.4f}"
                )
            else:
                logger.debug("Insufficient data for volatility calculation")

        except Exception as error:
            logger.error(f"Failed to update historical volatility: {error}")

    def calculate_volatility_index(self, historical_data: list[MarketData]) -> float:
        """Calculate volatility index from historical data"""
        if len(historical_data) < 2:
            return 0.02  # Default volatility

        import numpy as np

        prices = [data.close for data in historical_data]
        returns = []

        for i in range(1, len(prices)):
            ret = np.log(prices[i] / prices[i - 1])
            returns.append(ret)

        return np.std(returns) if returns else 0.02

    async def calculate_risk_metrics(
        self, bot_id: str, portfolio: Portfolio, storage: Any
    ) -> RiskMetrics:
        """Calculate comprehensive risk metrics for a bot"""
        try:
            # Smart trade fetching: Try storage (backtesting) then DB (live)
            trades = []
            if hasattr(storage, "get_trades"):
                if asyncio.iscoroutinefunction(storage.get_trades):
                    trades = await storage.get_trades(bot_id)
                else:
                    trades = storage.get_trades(bot_id)

            # If valid trades not found in storage and we have a DB session, try DB
            if not trades and self.db:
                try:
                    from ..repositories.trade_repository import TradeRepository

                    repo = TradeRepository()
                    db_trades = await repo.get_by_bot(self.db, bot_id, limit=500)

                    # Map DB trades to local Trade model
                    trades = [
                        Trade(
                            id=str(t.id),
                            symbol=t.symbol,
                            side=t.side,
                            amount=float(t.amount),
                            price=float(t.price),
                            timestamp=int(t.created_at.timestamp() * 1000),
                            total=float(t.total) if t.total else 0.0,
                            total_with_fee=float(t.total) if t.total else 0.0,
                            fee=float(t.fee) if hasattr(t, "fee") and t.fee else 0.0,
                            pnl=float(t.pnl) if t.pnl else None,
                        )
                        for t in db_trades
                    ]
                except Exception as e:
                    logger.warning(
                        f"Failed to fetch trades from DB for risk metrics: {e}"
                    )

            # Ensure trades is a list
            trades = trades or []

            # Calculate current drawdown
            equity_curve = self.calculate_equity_curve(trades, portfolio.total_balance)
            current_drawdown = self.calculate_current_drawdown(equity_curve)

            # Calculate max drawdown
            max_drawdown = self.calculate_max_drawdown(equity_curve)

            # Calculate daily P&L
            daily_pnl = self.calculate_daily_pnl(trades)
            daily_loss = abs(min(daily_pnl)) if daily_pnl else 0.0

            # Calculate position metrics
            position_size = self.calculate_current_position_size(portfolio)
            total_exposure = self.calculate_total_exposure(portfolio)

            return RiskMetrics(
                current_drawdown=current_drawdown,
                max_drawdown=max_drawdown,
                daily_loss=daily_loss,
                position_size=position_size,
                total_exposure=total_exposure,
                risk_per_trade=0.02,  # Mock value - would come from bot config
            )
        except Exception as error:
            logger.error(f"Error calculating risk metrics: {error}")
            raise

    async def should_stop_trading(
        self, user_id: str, portfolio: Portfolio, metrics: RiskMetrics | None = None
    ) -> tuple[bool, str | None]:
        """Determine if trading should stop based on risk limits"""
        # If persistent mode is enabled, never stop trading automatically
        if self.default_limits.persistent_mode:
            return False, None

        try:
            # ✅ Get user-specific limits from database if available
            limits = self.default_limits
            if self._risk_repository and self.db:
                user_limits = await self._risk_repository.get_user_limits(
                    self.db, user_id
                )
                for limit in user_limits:
                    if limit.limit_type == "max_drawdown":
                        limits.max_drawdown = limit.value
                    elif limit.limit_type == "max_daily_loss":
                        limits.max_daily_loss = limit.value
                    elif limit.limit_type == "max_position_size":
                        limits.max_position_size = limit.value
                    elif limit.limit_type == "max_total_exposure":
                        limits.max_total_exposure = limit.value

            # Use provided metrics or calculate them
            if metrics is None:
                # Would call self.calculate_risk_metrics() in real implementation
                metrics = RiskMetrics(
                    current_drawdown=0.05,
                    max_drawdown=0.08,
                    daily_loss=0.02,
                    position_size=0.15,
                    total_exposure=0.30,
                    risk_per_trade=0.02,
                )

            # Check limits and create alerts
            if metrics.current_drawdown >= limits.max_drawdown:
                message = f"Max drawdown exceeded: {metrics.current_drawdown:.2%} >= {limits.max_drawdown:.2%}"
                await self._create_alert(
                    user_id=user_id,
                    alert_type="drawdown",
                    severity=(
                        "critical"
                        if metrics.current_drawdown >= limits.max_drawdown * 1.5
                        else "high"
                    ),
                    message=message,
                    current_value=metrics.current_drawdown,
                    threshold_value=limits.max_drawdown,
                )
                return True, message

            if metrics.daily_loss >= limits.max_daily_loss:
                message = f"Daily loss limit exceeded: {metrics.daily_loss:.2%} >= {limits.max_daily_loss:.2%}"
                await self._create_alert(
                    user_id=user_id,
                    alert_type="daily_loss",
                    severity=(
                        "critical"
                        if metrics.daily_loss >= limits.max_daily_loss * 1.5
                        else "high"
                    ),
                    message=message,
                    current_value=metrics.daily_loss,
                    threshold_value=limits.max_daily_loss,
                )
                return True, message

            if metrics.total_exposure >= limits.max_total_exposure:
                message = f"Total exposure limit exceeded: {metrics.total_exposure:.2%} >= {limits.max_total_exposure:.2%}"
                await self._create_alert(
                    user_id=user_id,
                    alert_type="exposure",
                    severity="high",
                    message=message,
                    current_value=metrics.total_exposure,
                    threshold_value=limits.max_total_exposure,
                )
                return True, message

            return False, None
        except Exception as error:
            logger.error(
                f"Error checking if trading should stop: {error}", exc_info=True
            )
            return False, None

    async def _create_alert(
        self,
        user_id: str,
        alert_type: str,
        severity: str,
        message: str,
        current_value: float | None = None,
        threshold_value: float | None = None,
    ):
        """Create a risk alert in the database"""
        if self._risk_repository and self.db:
            try:
                await self._risk_repository.create_alert(
                    self.db,
                    user_id=user_id,
                    alert_type=alert_type,
                    severity=severity,
                    message=message,
                    current_value=current_value,
                    threshold_value=threshold_value,
                )
                logger.info(
                    f"Risk alert created: {alert_type} for user {user_id}",
                    extra={
                        "user_id": user_id,
                        "alert_type": alert_type,
                        "severity": severity,
                    },
                )
            except Exception as e:
                logger.error(f"Error creating risk alert: {e}", exc_info=True)

    def calculate_position_size_for_trade(
        self, bot_config: BotConfig, portfolio: Portfolio, current_price: float
    ) -> float:
        """Calculate position size for a new trade using Kelly Criterion"""
        available_balance = portfolio.available_balance

        # Calculate Kelly Criterion
        wins = portfolio.successful_trades or 0
        losses = portfolio.failed_trades or 0
        total_trades = wins + losses

        kelly_fraction = 0.0
        if total_trades > 0:
            win_rate = wins / total_trades
            win_multiplier = bot_config.take_profit / bot_config.stop_loss
            loss_multiplier = 1.0

            kelly_fraction = (
                win_rate * win_multiplier - (1 - win_rate) * loss_multiplier
            ) / win_multiplier
            # Use half-Kelly for more conservative sizing
            kelly_fraction = max(0.0, kelly_fraction * 0.5)
        else:
            # Start conservative with 1% if no trade history
            kelly_fraction = 0.01

        # Calculate position size based on risk and Kelly Criterion
        risk_amount = available_balance * bot_config.risk_per_trade * kelly_fraction
        stop_loss_amount = current_price * bot_config.stop_loss

        if stop_loss_amount == 0:
            return 0.0

        position_size = risk_amount / stop_loss_amount
        max_position_size = (
            available_balance * self.default_limits.max_position_size / current_price
        )

        # Apply micro trading limits if enabled
        final_position_size = min(position_size, max_position_size)

        if self.default_limits.micro_mode_enabled:
            # Ensure position size doesn't go below minimum for micro trading
            min_position_value = (
                available_balance * self.default_limits.min_position_size
            )
            min_position_size = min_position_value / current_price

            # For small balances, allow micro positions but cap at a reasonable maximum
            if available_balance < 1000:  # Less than $1000 balance
                final_position_size = max(final_position_size, min_position_size)
                # Cap at 1% of available balance for safety
                final_position_size = min(
                    final_position_size, available_balance * 0.01 / current_price
                )

        return final_position_size

    def calculate_dynamic_stop_loss(
        self, entry_price: float, current_price: float, bot_config: BotConfig
    ) -> float:
        """Calculate dynamic trailing stop loss"""
        risk_amount = entry_price * bot_config.risk_per_trade
        stop_loss_distance = risk_amount / (
            entry_price * self.default_limits.stop_loss_multiplier
        )

        # Trailing stop loss
        trailing_stop = current_price * (1 - stop_loss_distance)

        # Ensure stop loss is below entry for long positions
        return min(trailing_stop, entry_price * (1 - bot_config.stop_loss))

    def calculate_take_profit(self, entry_price: float, bot_config: BotConfig) -> float:
        """Calculate take profit level"""
        return entry_price * (
            1 + bot_config.take_profit * self.default_limits.take_profit_multiplier
        )

    def calculate_equity_curve(
        self, trades: list[Trade], initial_balance: float
    ) -> list[float]:
        """Calculate equity curve from trade history"""
        balance = initial_balance
        equity = [balance]

        # Group trades by day (simplified)
        daily_trades: dict[int, list[Trade]] = {}

        for trade in trades:
            day = trade.timestamp // (24 * 60 * 60 * 1000)  # Convert to days
            if day not in daily_trades:
                daily_trades[day] = []
            daily_trades[day].append(trade)

        # Calculate daily equity
        for day in sorted(daily_trades.keys()):
            day_trades = daily_trades[day]
            for trade in day_trades:
                if trade.side == "buy":
                    balance -= trade.total_with_fee
                else:
                    balance += trade.total - trade.fee
            equity.append(balance)

        return equity

    def calculate_current_drawdown(self, equity_curve: list[float]) -> float:
        """Calculate current drawdown from equity curve"""
        if not equity_curve:
            return 0.0

        peak = max(equity_curve)
        current = equity_curve[-1]

        return (peak - current) / peak if peak > 0 else 0.0

    def calculate_max_drawdown(self, equity_curve: list[float]) -> float:
        """Calculate maximum drawdown from equity curve"""
        if len(equity_curve) < 2:
            return 0.0

        max_drawdown = 0.0
        peak = equity_curve[0]

        for value in equity_curve[1:]:
            if value > peak:
                peak = value

            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    def calculate_daily_pnl(self, trades: list[Trade]) -> list[float]:
        """Calculate daily profit and loss"""
        daily_pnl: dict[int, float] = {}

        for trade in trades:
            day = trade.timestamp // (24 * 60 * 60 * 1000)
            pnl = (
                -trade.total_with_fee
                if trade.side == "buy"
                else trade.total - trade.fee
            )

            daily_pnl[day] = daily_pnl.get(day, 0.0) + pnl

        return list(daily_pnl.values())

    def calculate_current_position_size(self, portfolio: Portfolio) -> float:
        """Calculate current position size as percentage of portfolio"""
        total_value = sum(
            pos.get("total_value", 0.0) for pos in portfolio.positions.values()
        )
        return (
            total_value / portfolio.total_balance
            if portfolio.total_balance > 0
            else 0.0
        )

    def calculate_total_exposure(self, portfolio: Portfolio) -> float:
        """Calculate total exposure (same as position size for simplicity)"""
        return self.calculate_current_position_size(portfolio)

    async def update_risk_limits(
        self, user_id: str, limits: dict[str, Any], db: AsyncSession | None = None
    ) -> None:
        """Update risk limits configuration (persists to database if db provided)"""
        # Update in-memory limits
        for key, value in limits.items():
            if hasattr(self.default_limits, key):
                setattr(self.default_limits, key, value)

        # Persist to database if repository available
        if db and not self._risk_repository:
            self._risk_repository = RiskRepository(db)

        if self._risk_repository:
            # Map field names to limit types
            limit_type_map = {
                "max_drawdown": "max_drawdown",
                "max_daily_loss": "max_daily_loss",
                "max_position_size": "max_position_size",
                "max_total_exposure": "max_total_exposure",
            }

            for key, value in limits.items():
                limit_type = limit_type_map.get(key)
                if limit_type and self.db:
                    try:
                        await self._risk_repository.create_or_update_limit(
                            self.db,
                            user_id=user_id,
                            limit_type=limit_type,
                            value=value,
                            enabled=True,
                        )
                    except Exception as e:
                        logger.error(f"Error updating risk limit: {e}", exc_info=True)

    async def get_risk_limits(self, user_id: str | None = None) -> RiskLimits:
        """Get current risk limits (from database if user_id provided)"""
        if user_id and self._risk_repository and self.db:
            user_limits = await self._risk_repository.get_user_limits(self.db, user_id)
            limits = RiskLimits()
            for limit in user_limits:
                if limit.limit_type == "max_drawdown":
                    limits.max_drawdown = limit.value
                elif limit.limit_type == "max_daily_loss":
                    limits.max_daily_loss = limit.value
                elif limit.limit_type == "max_position_size":
                    limits.max_position_size = limit.value
                elif limit.limit_type == "max_total_exposure":
                    limits.max_total_exposure = limit.value
            return limits
        return self.default_limits


# Global instance
risk_management_engine = RiskManagementEngine()
