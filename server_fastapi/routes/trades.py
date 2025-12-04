from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time
from datetime import datetime
from ..services.exchange_service import default_exchange
from ..services.trading_orchestrator import trading_orchestrator
from ..services.trading.safe_trading_system import SafeTradingSystem
from ..services.trading.real_money_service import real_money_trading_service
from ..services.auth.exchange_key_service import exchange_key_service
from ..services.two_factor_service import two_factor_service
from ..services.kyc_service import kyc_service
from ..dependencies.auth import get_current_user
from ..database import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class TradeCreate(BaseModel):
    botId: Optional[str] = None
    pair: str
    side: str  # 'buy' or 'sell'
    type: Optional[str] = (
        "market"  # 'market', 'limit', 'stop', 'stop-limit', 'take-profit', 'trailing-stop'
    )
    amount: float
    price: Optional[float] = None  # Required for limit orders
    stop: Optional[float] = None  # Stop price for stop orders
    take_profit: Optional[float] = None  # Take profit price
    trailing_stop_percent: Optional[float] = None  # Trailing stop percentage
    time_in_force: Optional[str] = "GTC"  # 'GTC', 'IOC', 'FOK'
    mode: str = "paper"  # 'paper' or 'real'
    exchange: Optional[str] = None  # Exchange to use (e.g., 'binance', 'kraken')
    mfa_token: Optional[str] = None  # 2FA token for real money trades


class TradeResponse(BaseModel):
    id: str
    botId: Optional[str] = None
    pair: str
    side: str
    type: Optional[str] = None  # 'market', 'limit', 'stop'
    amount: float
    price: float
    total: Optional[float] = None  # amount * price
    timestamp: str
    status: str  # 'completed', 'pending', 'failed'
    pnl: Optional[float] = None
    mode: Optional[str] = None  # 'paper' or 'real'
    exchange: Optional[str] = None  # Exchange name
    order_id: Optional[str] = None


# Note: All trades are now stored in database (Trade model)
# Removed in-memory trades_store - using database only

# Initialize safe trading system
safe_trading_system = SafeTradingSystem()


@router.get("/", response_model=List[TradeResponse])
async def get_trades(
    botId: Optional[str] = Query(None),
    mode: Optional[str] = Query(None, pattern="^(paper|real|live)$"),
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get trades from database with optional filtering by bot ID and mode"""
    try:
        from sqlalchemy import select
        from ..models.trade import Trade

        user_id = current_user.get("id") or current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            logger.warning(f"User ID not found in current_user: {current_user}")
            return []

        # Normalize mode: "live" -> "real"
        normalized_mode = "real" if mode == "live" else mode

        # Get trades from database
        query = select(Trade).where(Trade.user_id == user_id)

        # Filter by bot ID if provided
        if botId:
            query = query.where(Trade.bot_id == botId)

        # Filter by mode if provided
        if normalized_mode:
            query = query.where(Trade.mode == normalized_mode)

        # Order by executed_at descending (most recent first)
        query = query.order_by(
            Trade.executed_at.desc()
            if hasattr(Trade.executed_at, "desc")
            else Trade.timestamp.desc()
        )

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
                    exchange=trade.exchange,
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
    month: str = Query(..., description="Month in format YYYY-MM"),
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get daily profit data for a calendar month"""
    try:
        user_id = current_user.get("user_id") or current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Parse month
        from datetime import datetime
        try:
            month_date = datetime.strptime(month, "%Y-%m")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")

        # For now, return empty calendar data
        # In a real implementation, this would aggregate daily profits from trades
        return {
            "daily_profits": []
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profit calendar: {e}", exc_info=True)
        # Return empty calendar instead of error
        return {
            "daily_profits": []
        }


@router.post("/", response_model=TradeResponse)
async def create_trade(
    trade: TradeCreate,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Create a new trade and execute it through the trading orchestrator with safety validation"""
    try:
        user_id = current_user.get("user_id", 1)

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
                from ..database import get_db_session

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
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient wallet balance. Required: ${total_cost:.2f}",
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error reserving funds for trade: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500, detail="Failed to reserve funds for trade"
                )

        # Save trade to database first
        from ..models.trade import Trade

        # Normalize mode: "live" -> "real"
        normalized_mode = "real" if trade.mode == "live" else trade.mode

        trade_id = None

        db_trade = Trade(
            user_id=user_id,
            bot_id=trade.botId,
            exchange=trade.exchange or "paper",
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
                user_id = current_user.get("sub") or current_user.get("user_id")
                if not user_id:
                    raise HTTPException(
                        status_code=401, detail="User not authenticated"
                    )

                # Get user's exchange API keys
                # Use exchange from trade request, or default to first available exchange
                exchange = trade.exchange or "binance"

                # Get user's available exchanges
                api_keys = await exchange_key_service.list_api_keys(str(user_id))
                if api_keys:
                    # Use the exchange from trade if available, otherwise use first validated exchange
                    available_exchanges = [
                        k["exchange"] for k in api_keys if k.get("is_validated")
                    ]
                    if exchange not in available_exchanges and available_exchanges:
                        exchange = available_exchanges[0]
                    elif not available_exchanges:
                        raise HTTPException(
                            status_code=400,
                            detail="No validated API keys found. Please add and validate an exchange API key.",
                        )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="No API keys found. Please add an exchange API key in Settings.",
                    )

                # Execute real money trade with advanced order type support
                order_result = (
                    await real_money_trading_service.execute_real_money_trade(
                        user_id=str(user_id),
                        exchange=exchange,
                        pair=trade.pair,
                        side=trade.side,
                        order_type=trade.type or "market",
                        amount=trade.amount,
                        price=trade.price,
                        bot_id=trade.botId,
                        mfa_token=trade.mfa_token,
                        stop=trade.stop,
                        take_profit=trade.take_profit,
                        trailing_stop_percent=trade.trailing_stop_percent,
                        time_in_force=trade.time_in_force,
                    )
                )

                # Update trade in database and calculate P&L
                db_trade = await db_session.get(Trade, int(trade_id))
                if db_trade:
                    db_trade.status = order_result.get("status", "completed")
                    db_trade.order_id = order_result.get("order_id")
                    db_trade.success = order_result.get("status") == "completed"
                    db_trade.fee = order_result.get("fee", 0.0)
                    if order_result.get("filled"):
                        db_trade.amount = order_result.get("filled", trade.amount)

                    # Calculate P&L for sell trades using FIFO accounting
                    if trade.side == "sell" and db_trade.status == "completed":
                        from ..services.pnl_service import PnLService

                        pnl_service = PnLService(db_session)

                        # Get execution price from order result or use requested price
                        execution_price = (
                            order_result.get("price") or trade.price or db_trade.price
                        )

                        # Calculate position P&L using FIFO method
                        position_pnl = await pnl_service.calculate_position_pnl(
                            user_id=user_id,
                            symbol=trade.pair,
                            current_price=execution_price,
                            mode="real",
                        )

                        # For sell trades, calculate realized P&L
                        # Get previous buy trades for this symbol to calculate cost basis
                        from sqlalchemy import select, and_

                        buy_trades_query = (
                            select(Trade)
                            .where(
                                and_(
                                    Trade.user_id == user_id,
                                    Trade.pair == trade.pair,
                                    Trade.side == "buy",
                                    Trade.mode == "real",
                                    Trade.status == "completed",
                                    Trade.success == True,
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
                db_trade.exchange = "paper"

                # Calculate P&L for paper trades using FIFO accounting
                if trade.side == "sell":
                    from ..services.pnl_service import PnLService

                    pnl_service = PnLService(db_session)

                    execution_price = trade.price or db_trade.price

                    # Calculate position P&L
                    position_pnl = await pnl_service.calculate_position_pnl(
                        user_id=user_id,
                        symbol=trade.pair,
                        current_price=execution_price,
                        mode="paper",
                    )

                    # Get previous buy trades for FIFO calculation
                    from sqlalchemy import select, and_

                    buy_trades_query = (
                        select(Trade)
                        .where(
                            and_(
                                Trade.user_id == user_id,
                                Trade.pair == trade.pair,
                                Trade.side == "buy",
                                Trade.mode == "paper",
                                Trade.status == "completed",
                                Trade.success == True,
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
                    exchange="paper",
                    symbol=trade.pair,
                    side=trade.side,
                    amount=trade.amount,
                    price=trade.price or 0,
                    mode="paper",
                    bot_id=trade.botId,
                    mfa_used=False,
                    risk_checks_passed=True,
                    success=True,
                    order_type=trade.type or "market",
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
                exchange=db_trade.exchange,
                order_id=db_trade.order_id,
            )

        # Fallback if trade not found
        raise HTTPException(status_code=404, detail="Trade not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create trade: {e}")
        raise HTTPException(status_code=500, detail="Failed to create trade")
