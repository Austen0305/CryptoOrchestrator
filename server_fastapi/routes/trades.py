from __future__ import annotations
import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

# Rate limiting imports
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address

    from ..rate_limit_config import get_rate_limit, limiter

    LIMITER_AVAILABLE = True
except ImportError:
    LIMITER_AVAILABLE = False
    Limiter = None
    get_remote_address = None
    limiter = None
    get_rate_limit = lambda x: x  # No-op fallback
    logger.warning("SlowAPI not available, rate limiting disabled")

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..dependencies.pnl import get_pnl_service
from ..dependencies.trading import (
    get_dex_trading_service,
    get_safe_trading_system,
)
from ..middleware.cache_manager import cached
from ..models.trade import Trade
from ..services.kyc_service import kyc_service
from ..services.pnl_service import PnLService
from ..services.trading.dex_trading_service import DEXTradingService
from ..services.trading.safe_trading_system import SafeTradingSystem
from ..services.two_factor_service import two_factor_service
from ..utils.query_optimizer import QueryOptimizer
from ..utils.route_helpers import _get_user_id
from ..utils.trading_utils import normalize_trading_mode

router = APIRouter()

# Use shared limiter from rate_limit_config (with test-specific high limits in test mode)
# If limiter is not available, create a no-op decorator
if not LIMITER_AVAILABLE or limiter is None:
    # Create a no-op decorator if limiter is not available
    class NoOpLimiter:
        def limit(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

    limiter = NoOpLimiter()
    get_rate_limit = lambda x: x  # No-op fallback


# Pydantic models
class TradeCreate(BaseModel):
    botId: str | None = None
    pair: str
    side: str  # 'buy' or 'sell'
    type: str | None = (
        "market"  # 'market', 'limit', 'stop', 'stop-limit', 'take-profit', 'trailing-stop'
    )
    amount: float
    price: float | None = None  # Required for limit orders
    stop: float | None = None  # Stop price for stop orders
    take_profit: float | None = None  # Take profit price
    trailing_stop_percent: float | None = None  # Trailing stop percentage
    time_in_force: str | None = "GTC"  # 'GTC', 'IOC', 'FOK'
    mode: str = "paper"  # 'paper' or 'real'
    chain_id: int | None = Field(
        1, description="Blockchain chain ID (1=Ethereum, 8453=Base, etc.)"
    )
    mfa_token: str | None = None  # 2FA token for real money trades


class TradeResponse(BaseModel):
    id: str
    botId: str | None = None
    pair: str
    side: str
    type: str | None = None  # 'market', 'limit', 'stop'
    amount: float
    price: float
    total: float | None = None  # amount * price
    timestamp: str
    status: str  # 'completed', 'pending', 'failed'
    pnl: float | None = None
    mode: str | None = None  # 'paper' or 'real'
    chain_id: int | None = None  # Blockchain chain ID
    transaction_hash: str | None = None  # Blockchain transaction hash
    order_id: str | None = None


class PaginatedTradeResponse(BaseModel):
    data: list[TradeResponse]
    pagination: dict[str, Any]


# Note: All trades are now stored in database (Trade model)
# Removed in-memory trades_store - using database only
# Services are now provided via dependency injection


@router.get("/", response_model=list[TradeResponse])
@cached(ttl=60, prefix="trades")  # 60s TTL for trade lists
async def get_trades(
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    botId: str | None = Query(None),
    mode: str | None = Query(None, pattern="^(paper|real|live)$"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """Get trades from database with optional filtering by bot ID and mode, with pagination"""
    try:
        user_id = _get_user_id(current_user)

        normalized_mode = normalize_trading_mode(mode)

        # Build query with eager loading to prevent N+1 queries
        query = select(Trade).where(Trade.user_id == user_id)

        # Filter by bot ID if provided
        if botId:
            query = query.where(Trade.bot_id == botId)

        # Filter by mode if provided
        if normalized_mode:
            query = query.where(Trade.mode == normalized_mode)

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            selectinload(Trade.user), selectinload(Trade.bot), selectinload(Trade.order)
        )

        # Order by executed_at descending (most recent first)
        query = query.order_by(
            Trade.executed_at.desc()
            if hasattr(Trade.executed_at, "desc")
            else Trade.timestamp.desc()
        )

        # Apply pagination
        query = QueryOptimizer.paginate_query(query, page=page, page_size=page_size)

        # Get total count for pagination metadata
        count_query = (
            select(func.count()).select_from(Trade).where(Trade.user_id == user_id)
        )
        if botId:
            count_query = count_query.where(Trade.bot_id == botId)
        if normalized_mode:
            count_query = count_query.where(Trade.mode == normalized_mode)
        total_result = await db_session.execute(count_query)
        total = total_result.scalar() or 0

        # Execute query
        result = await db_session.execute(query)
        db_trades = list(result.scalars().all())

        # Convert to response format
        response_trades = []
        for trade in db_trades:
            total = trade.total or (trade.amount * trade.price)
            timestamp_str = (
                trade.executed_at.isoformat()
                if trade.executed_at
                else trade.timestamp.isoformat()
            )

            response_trades.append(
                TradeResponse(
                    id=str(trade.id),
                    botId=trade.bot_id,
                    pair=trade.pair or trade.symbol,
                    side=trade.side,
                    type=trade.order_type,
                    amount=trade.amount,
                    price=trade.price,
                    total=total,
                    timestamp=timestamp_str,
                    status=trade.status,
                    pnl=trade.pnl,
                    mode=trade.mode,
                    chain_id=trade.chain_id,
                    transaction_hash=None,  # Will be set after DEX execution
                    order_id=trade.order_id,
                )
            )

        return response_trades
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get trades: {e}", exc_info=True)
        # Return empty array instead of 500 error for better UX during development
        logger.warning(f"Returning empty trades list due to error: {e}")
        return []


@router.get("/profit-calendar")
async def get_profit_calendar(
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    month: str = Query(..., description="Month in format YYYY-MM"),
):
    """Get daily profit data for a calendar month"""
    try:
        user_id = _get_user_id(current_user)

        # Parse month
        from datetime import datetime

        try:
            datetime.strptime(month, "%Y-%m")  # Validate date format
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid month format. Use YYYY-MM"
            )

        # For now, return empty calendar data
        # In a real implementation, this would aggregate daily profits from trades
        return {"daily_profits": []}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profit calendar: {e}", exc_info=True)
        # Return empty calendar instead of error
        return {"daily_profits": []}


@router.post("/", response_model=TradeResponse)
@limiter.limit(
    get_rate_limit("10/minute")
)  # Rate limit: 10/minute in production, 10000/minute in tests
async def create_trade(
    trade: TradeCreate,
    request: Request,  # Required for rate limiting
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    safe_trading_system: Annotated[SafeTradingSystem, Depends(get_safe_trading_system)],
    dex_service: Annotated[DEXTradingService, Depends(get_dex_trading_service)],
    pnl_service: Annotated[PnLService, Depends(get_pnl_service)],
):
    """Create a new trade and execute it through the trading orchestrator with safety validation"""
    try:
        user_id = _get_user_id(current_user)

        # Prepare trade details for validation
        trade_details = {
            "symbol": trade.pair,
            "action": trade.side,
            "quantity": trade.amount,
            "price": trade.price,
            "bot_id": trade.botId,
            "user_id": user_id,
            "mode": trade.mode,
        }

        # Check KYC requirement for real money trades
        if trade.mode == "real":
            trade_value = trade.amount * (trade.price or 0)
            requires_kyc = await kyc_service.require_kyc_for_trading(
                user_id, trade_value
            )
            if requires_kyc:
                is_verified = await kyc_service.is_verified(user_id)
                if not is_verified:
                    raise HTTPException(
                        status_code=403,
                        detail="KYC verification required for this trade amount. Please complete KYC verification.",
                    )

        # Verify 2FA for real money trades if required
        if trade.mode == "real" and two_factor_service.require_2fa_for_trading(user_id):
            if not trade.mfa_token:
                raise HTTPException(
                    status_code=400, detail="2FA token required for real money trades"
                )

            if not two_factor_service.verify_token(user_id, trade.mfa_token):
                raise HTTPException(status_code=401, detail="Invalid 2FA token")

        # Validate trade with safe trading system
        validation_result = await safe_trading_system.validate_trade(trade_details)

        if not validation_result["valid"]:
            logger.warning(f"Trade validation failed: {validation_result['errors']}")
            raise HTTPException(
                status_code=400,
                detail=f"Trade validation failed: {'; '.join(validation_result['errors'])}",
            )

        # Log warnings if any
        if validation_result["warnings"]:
            logger.warning(
                f"Trade warnings: {'; '.join(validation_result['warnings'])}"
            )

        # Reserve funds in wallet for real money trades
        if trade.mode == "real" or trade.mode == "live":
            try:
                from ..services.wallet_trading_integration import (
                    WalletTradingIntegration,
                )

                # Calculate trade cost
                trade_value = trade.amount * (trade.price or 0)
                if trade_value <= 0:
                    # For market orders, estimate cost (will be updated after execution)
                    trade_value = (
                        trade.amount * 50000
                    )  # Estimate with current market price

                estimated_fee = trade_value * 0.001  # 0.1% fee estimate
                total_cost = trade_value + estimated_fee

                # Reserve funds using existing db_session
                wallet_integration = WalletTradingIntegration(db_session)

                # Reserve funds
                funds_reserved = await wallet_integration.reserve_funds_for_trade(
                    user_id=user_id,
                    amount=total_cost,
                    currency="USD",  # Could be determined from trade pair
                )

                if not funds_reserved:
                    # Get current balance for better error message
                    try:
                        current_balance = (
                            await wallet_integration.get_available_balance(
                                user_id=user_id, currency="USD"
                            )
                        )
                        raise HTTPException(
                            status_code=400,
                            detail=f"Insufficient wallet balance. Available: ${current_balance:.2f}, Required: ${total_cost:.2f}",
                        )
                    except Exception:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Insufficient wallet balance. Required: ${total_cost:.2f}. Please deposit funds or reduce trade size.",
                        )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error reserving funds for trade: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500, detail="Failed to reserve funds for trade"
                )

        # Save trade to database first
        # Normalize mode: "live" -> "real"
        normalized_mode = "real" if trade.mode == "live" else trade.mode

        trade_id = None

        db_trade = Trade(
            user_id=user_id,
            bot_id=trade.botId,
            chain_id=trade.chain_id or 1,  # Default to Ethereum
            symbol=trade.pair,
            pair=trade.pair,
            side=trade.side,
            order_type=trade.type or "market",
            amount=trade.amount,
            price=trade.price or 0.0,
            cost=(trade.amount * (trade.price or 0.0)),
            fee=0.0,  # Will be updated after execution
            mode=normalized_mode,
            executed_at=datetime.utcnow(),
            success=False,  # Will be updated after execution
            status="pending",
            timestamp=datetime.utcnow(),
        )

        db_session.add(db_trade)
        await db_session.commit()
        await db_session.refresh(db_trade)

        trade_id = str(db_trade.id)

        # Execute the trade based on mode
        if trade.mode == "real" or trade.mode == "live":
            try:
                user_id = _get_user_id(current_user)
                if not user_id:
                    raise HTTPException(
                        status_code=401, detail="User not authenticated"
                    )

                # Execute real money trade via DEX
                chain_id = trade.chain_id or 1  # Default to Ethereum

                # Convert pair to token addresses (simplified - in production, use token registry)
                # For now, assume format like "ETH/USDC" or token addresses
                sell_token = (
                    trade.pair.split("/")[0] if "/" in trade.pair else trade.pair
                )
                buy_token = trade.pair.split("/")[1] if "/" in trade.pair else "USDC"

                # Convert amount to wei/units (simplified - in production, handle decimals properly)
                sell_amount = str(int(trade.amount * 1e18))  # Assume 18 decimals

                # Execute DEX swap
                swap_result = await dex_service.execute_custodial_swap(
                    user_id=user_id,
                    sell_token=sell_token if trade.side == "sell" else buy_token,
                    buy_token=buy_token if trade.side == "sell" else sell_token,
                    sell_amount=sell_amount,
                    chain_id=chain_id,
                    slippage_percentage=0.5,  # Default 0.5% slippage
                    user_tier="free",  # Get from user profile
                    db=db_session,
                )

                if swap_result and swap_result.get("success"):
                    order_result = {
                        "success": True,
                        "order_id": swap_result.get("transaction_hash"),
                        "price": trade.price or 0.0,
                        "status": "completed",
                        "transaction_hash": swap_result.get("transaction_hash"),
                    }
                else:
                    raise HTTPException(
                        status_code=500, detail="DEX swap execution failed"
                    )

                # Update trade in database and calculate P&L
                db_trade = await db_session.get(Trade, int(trade_id))
                if db_trade:
                    db_trade.status = order_result.get("status", "completed")
                    db_trade.order_id = order_result.get(
                        "order_id"
                    ) or order_result.get("transaction_hash")
                    db_trade.transaction_hash = order_result.get("transaction_hash")
                    db_trade.success = order_result.get(
                        "status"
                    ) == "completed" or order_result.get("success", False)
                    db_trade.fee = order_result.get("fee", 0.0)
                    if order_result.get("filled"):
                        db_trade.amount = order_result.get("filled", trade.amount)

                    # ✅ Use injected service - Calculate P&L for sell trades using FIFO accounting
                    if trade.side == "sell" and db_trade.status == "completed":
                        # Get execution price from order result or use requested price
                        execution_price = (
                            order_result.get("price") or trade.price or db_trade.price
                        )

                        # Calculate position P&L using FIFO method
                        # Calculate position P&L for tracking (not used in response but logged)
                        await pnl_service.calculate_position_pnl(
                            user_id=user_id,
                            symbol=trade.pair,
                            current_price=execution_price,
                            mode="real",
                        )

                        # For sell trades, calculate realized P&L
                        # Get previous buy trades for this symbol to calculate cost basis

                        buy_trades_query = (
                            select(Trade)
                            .where(
                                and_(
                                    Trade.user_id == user_id,
                                    Trade.pair == trade.pair,
                                    Trade.side == "buy",
                                    Trade.mode == "real",
                                    Trade.status == "completed",
                                    Trade.success.is_(True),
                                )
                            )
                            .order_by(Trade.timestamp)
                        )

                        buy_result = await db_session.execute(buy_trades_query)
                        buy_trades = list(buy_result.scalars().all())

                        # Calculate realized P&L using FIFO
                        sell_amount = db_trade.amount
                        realized_pnl = 0.0
                        total_cost_basis = 0.0

                        for buy_trade in buy_trades:
                            if sell_amount <= 0:
                                break

                            if buy_trade.amount <= sell_amount:
                                # Use entire buy trade
                                cost_basis = buy_trade.amount * buy_trade.price + (
                                    buy_trade.fee or 0.0
                                )
                                total_cost_basis += cost_basis
                                sell_amount -= buy_trade.amount
                            else:
                                # Use partial buy trade
                                cost_basis = sell_amount * buy_trade.price + (
                                    sell_amount / buy_trade.amount
                                ) * (buy_trade.fee or 0.0)
                                total_cost_basis += cost_basis
                                sell_amount = 0

                        # Calculate realized P&L
                        sell_value = db_trade.amount * execution_price
                        realized_pnl = (
                            sell_value - total_cost_basis - (db_trade.fee or 0.0)
                        )
                        pnl_percent = (
                            (realized_pnl / total_cost_basis * 100)
                            if total_cost_basis > 0
                            else 0.0
                        )

                        db_trade.pnl = realized_pnl
                        db_trade.pnl_percent = pnl_percent
                    else:
                        # For buy trades, P&L is 0 until position is closed
                        db_trade.pnl = 0.0
                        db_trade.pnl_percent = 0.0

                    await db_session.commit()

                # Record trade result in safe trading system for risk monitoring
                pnl = db_trade.pnl if db_trade else 0.0
                await safe_trading_system.record_trade_result(trade_details, pnl)

                logger.info(
                    f"Real money trade executed: trade_id={trade_id}, order_id={order_result.get('order_id')}"
                )

            except ValueError as e:
                logger.error(f"Validation error for real money trade: {e}")
                # Update trade status in database
                db_trade = await db_session.get(Trade, int(trade_id))
                if db_trade:
                    db_trade.status = "failed"
                    db_trade.success = False
                    db_trade.error_message = str(e)
                    await db_session.commit()
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Failed to execute real money trade: {e}")
                # Update trade status in database
                db_trade = await db_session.get(Trade, int(trade_id))
                if db_trade:
                    db_trade.status = "failed"
                    db_trade.success = False
                    db_trade.error_message = str(e)
                    await db_session.commit()
                raise HTTPException(
                    status_code=500, detail=f"Failed to execute trade: {str(e)}"
                )
        else:
            # Paper trade - mark as completed immediately
            # Update trade in database with proper P&L calculation
            db_trade = await db_session.get(Trade, int(trade_id))
            if db_trade:
                db_trade.status = "completed"
                db_trade.success = True
                db_trade.chain_id = 1  # Default to Ethereum for paper trading

                # ✅ Use injected service - Calculate P&L for paper trades using FIFO accounting
                if trade.side == "sell":
                    execution_price = trade.price or db_trade.price

                    # Calculate position P&L for tracking (not used in response but logged)
                    await pnl_service.calculate_position_pnl(
                        user_id=user_id,
                        symbol=trade.pair,
                        current_price=execution_price,
                        mode="paper",
                    )

                    # Get previous buy trades for FIFO calculation

                    buy_trades_query = (
                        select(Trade)
                        .where(
                            and_(
                                Trade.user_id == user_id,
                                Trade.pair == trade.pair,
                                Trade.side == "buy",
                                Trade.mode == "paper",
                                Trade.status == "completed",
                                Trade.success.is_(True),
                            )
                        )
                        .order_by(Trade.timestamp)
                    )

                    buy_result = await db_session.execute(buy_trades_query)
                    buy_trades = list(buy_result.scalars().all())

                    # Calculate realized P&L using FIFO
                    sell_amount = db_trade.amount
                    realized_pnl = 0.0
                    total_cost_basis = 0.0

                    for buy_trade in buy_trades:
                        if sell_amount <= 0:
                            break

                        if buy_trade.amount <= sell_amount:
                            cost_basis = buy_trade.amount * buy_trade.price + (
                                buy_trade.fee or 0.0
                            )
                            total_cost_basis += cost_basis
                            sell_amount -= buy_trade.amount
                        else:
                            cost_basis = sell_amount * buy_trade.price + (
                                sell_amount / buy_trade.amount
                            ) * (buy_trade.fee or 0.0)
                            total_cost_basis += cost_basis
                            sell_amount = 0

                    # Calculate realized P&L
                    sell_value = db_trade.amount * execution_price
                    realized_pnl = sell_value - total_cost_basis - (db_trade.fee or 0.0)
                    pnl_percent = (
                        (realized_pnl / total_cost_basis * 100)
                        if total_cost_basis > 0
                        else 0.0
                    )

                    db_trade.pnl = realized_pnl
                    db_trade.pnl_percent = pnl_percent
                else:
                    # For buy trades, P&L is 0 until position is closed
                    db_trade.pnl = 0.0
                    db_trade.pnl_percent = 0.0

                await db_session.commit()

            # Record paper trade result in safe trading system
            pnl = db_trade.pnl if db_trade else 0.0
            await safe_trading_system.record_trade_result(trade_details, pnl)

            # Log paper trade for audit (optional, but good for tracking)
            try:
                from ..services.audit.audit_logger import audit_logger

                audit_logger.log_trade(
                    user_id=user_id,
                    trade_id=trade_id,
                    chain_id=1,  # Default to Ethereum for paper trading
                    symbol=trade.pair,
                    side=trade.side,
                    amount=trade.amount,
                    price=trade.price or 0,
                    mode="paper",
                    transaction_hash=None,  # Paper trading doesn't have blockchain transactions
                    bot_id=trade.botId,
                    mfa_used=False,
                    risk_checks_passed=True,
                    success=True,
                )
            except Exception as e:
                logger.warning(f"Failed to log paper trade to audit: {e}")

        # Fetch trade from database to return
        db_trade = await db_session.get(Trade, int(trade_id))
        if db_trade:
            total = db_trade.total or (db_trade.amount * db_trade.price)
            timestamp_str = (
                db_trade.executed_at.isoformat()
                if db_trade.executed_at
                else db_trade.timestamp.isoformat()
            )

            return TradeResponse(
                id=str(db_trade.id),
                botId=db_trade.bot_id,
                pair=db_trade.pair or db_trade.symbol,
                side=db_trade.side,
                type=db_trade.order_type,
                amount=db_trade.amount,
                price=db_trade.price,
                total=total,
                timestamp=timestamp_str,
                status=db_trade.status,
                pnl=db_trade.pnl,
                mode=db_trade.mode,
                chain_id=db_trade.chain_id,
                transaction_hash=db_trade.transaction_hash,
                order_id=db_trade.order_id,
            )

        # Fallback if trade not found
        raise HTTPException(status_code=404, detail="Trade not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create trade: {e}")
        raise HTTPException(status_code=500, detail="Failed to create trade")
