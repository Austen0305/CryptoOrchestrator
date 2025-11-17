from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import logging
import jwt
import os
import time
from datetime import datetime
from ..services.exchange_service import default_exchange
from ..services.trading_orchestrator import trading_orchestrator
from ..services.trading.safe_trading_system import SafeTradingSystem
from ..services.trading.real_money_service import real_money_trading_service
from ..services.auth.exchange_key_service import exchange_key_service

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Pydantic models
class TradeCreate(BaseModel):
    botId: Optional[str] = None
    pair: str
    side: str  # 'buy' or 'sell'
    type: Optional[str] = "market"  # 'market', 'limit', or 'stop'
    amount: float
    price: Optional[float] = None  # Required for limit orders
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

# In-memory trade storage (in production, use database)
trades_store = {}

# Initialize safe trading system
safe_trading_system = SafeTradingSystem()

@router.get("/", response_model=List[TradeResponse])
async def get_trades(
    botId: Optional[str] = Query(None),
    mode: Optional[str] = Query(None, pattern="^(paper|real|live)$"),
    current_user: dict = Depends(get_current_user)
):
    """Get trades with optional filtering by bot ID and mode"""
    try:
        user_id = current_user.get("user_id", 1)  # Default to user 1 for now

        # Get all trades for this user
        user_trades = [trade for trade in trades_store.values() if trade.get("user_id") == user_id]

        # Filter by bot ID if provided
        if botId:
            user_trades = [t for t in user_trades if t.get("botId") == botId]

        # Filter by mode if provided
        if mode:
            user_trades = [t for t in user_trades if t.get("mode") == mode]

        # Convert to response format
        response_trades = []
        for trade in user_trades:
            total = trade.get("total") or (trade.get("amount", 0) * trade.get("price", 0))
            response_trades.append(TradeResponse(
                id=trade.get("id", ""),
                botId=trade.get("botId"),
                pair=trade.get("pair", ""),
                side=trade.get("side", trade.get("type", "buy")),
                type=trade.get("type", "market"),
                amount=trade.get("amount", 0),
                price=trade.get("price", 0),
                total=total,
                timestamp=trade.get("timestamp", ""),
                status=trade.get("status", "completed"),
                pnl=trade.get("pnl"),
                mode=trade.get("mode", "paper"),
                exchange=trade.get("exchange"),
                order_id=trade.get("order_id")
            ))

        return response_trades
    except Exception as e:
        logger.error(f"Failed to get trades: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trades")

@router.post("/", response_model=TradeResponse)
async def create_trade(trade: TradeCreate, current_user: dict = Depends(get_current_user)):
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
            "mode": trade.mode
        }

        # Validate trade with safe trading system
        validation_result = await safe_trading_system.validate_trade(trade_details)

        if not validation_result["valid"]:
            logger.warning(f"Trade validation failed: {validation_result['errors']}")
            raise HTTPException(
                status_code=400,
                detail=f"Trade validation failed: {'; '.join(validation_result['errors'])}"
            )

        # Log warnings if any
        if validation_result["warnings"]:
            logger.warning(f"Trade warnings: {'; '.join(validation_result['warnings'])}")

        # Generate trade ID
        trade_id = f"trade_{len(trades_store) + 1}"

        # Create trade record
        new_trade = {
            "id": trade_id,
            "user_id": user_id,
            "botId": trade.botId,
            "pair": trade.pair,
            "side": trade.side,
            "amount": trade.amount,
            "price": trade.price,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "pending",
            "pnl": None,
            "mode": trade.mode,
            "validation_result": validation_result
        }

        # Store the trade
        trades_store[trade_id] = new_trade

        # Execute the trade based on mode
        if trade.mode == "real" or trade.mode == "live":
            try:
                user_id = current_user.get("sub") or current_user.get("user_id")
                if not user_id:
                    raise HTTPException(status_code=401, detail="User not authenticated")

                # Get user's exchange API keys
                # Use exchange from trade request, or default to first available exchange
                exchange = trade.exchange or "binance"
                
                # Get user's available exchanges
                api_keys = await exchange_key_service.list_api_keys(str(user_id))
                if api_keys:
                    # Use the exchange from trade if available, otherwise use first validated exchange
                    available_exchanges = [k["exchange"] for k in api_keys if k.get("is_validated")]
                    if exchange not in available_exchanges and available_exchanges:
                        exchange = available_exchanges[0]
                    elif not available_exchanges:
                        raise HTTPException(
                            status_code=400,
                            detail="No validated API keys found. Please add and validate an exchange API key."
                        )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="No API keys found. Please add an exchange API key in Settings."
                    )
                
                # Execute real money trade
                order_result = await real_money_trading_service.execute_real_money_trade(
                    user_id=str(user_id),
                    exchange=exchange,
                    pair=trade.pair,
                    side=trade.side,
                    order_type=trade.type or "market",
                    amount=trade.amount,
                    price=trade.price,
                    bot_id=trade.botId,
                    mfa_token=trade.mfa_token,
                )

                # Update trade status based on order result
                new_trade["status"] = order_result.get("status", "completed")
                new_trade["exchange_order_id"] = order_result.get("order_id")
                new_trade["filled"] = order_result.get("filled", 0)
                new_trade["remaining"] = order_result.get("remaining", trade.amount)

                # Record trade result in safe trading system for risk monitoring
                pnl = 0.0  # Will be calculated when position is closed
                await safe_trading_system.record_trade_result(trade_details, pnl)

                logger.info(f"Real money trade executed: {new_trade}")

            except ValueError as e:
                logger.error(f"Validation error for real money trade: {e}")
                new_trade["status"] = "failed"
                new_trade["error"] = str(e)
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Failed to execute real money trade: {e}")
                new_trade["status"] = "failed"
                new_trade["error"] = str(e)
                raise HTTPException(status_code=500, detail=f"Failed to execute trade: {str(e)}")
        else:
            # Paper trade - mark as completed immediately
            new_trade["status"] = "completed"
            new_trade["exchange"] = "paper"  # Paper trades don't use real exchanges

            # Calculate mock P&L for paper trades
            pnl = 0.0
            if trade.side == "sell":
                # Mock profit/loss calculation
                pnl = trade.amount * (trade.price - 45000)  # Mock entry price
                new_trade["pnl"] = pnl

            # Record paper trade result in safe trading system
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
                    order_type=trade.type or "market"
                )
            except Exception as e:
                logger.warning(f"Failed to log paper trade to audit: {e}")

        return TradeResponse(
            id=new_trade["id"],
            botId=new_trade.get("botId"),
            pair=new_trade["pair"],
            side=new_trade["side"],
            type=new_trade.get("type", "market"),
            amount=new_trade["amount"],
            price=new_trade["price"],
            total=new_trade.get("total") or (new_trade["amount"] * (new_trade["price"] or 0)),
            timestamp=new_trade["timestamp"],
            status=new_trade["status"],
            pnl=new_trade.get("pnl"),
            mode=new_trade.get("mode", "paper"),
            exchange=new_trade.get("exchange"),
            order_id=new_trade.get("order_id") or new_trade.get("exchange_order_id")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create trade: {e}")
        raise HTTPException(status_code=500, detail="Failed to create trade")
