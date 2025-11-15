from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import logging
import jwt
import os
from datetime import datetime
from ..services.exchange_service import default_exchange
from ..services.trading_orchestrator import trading_orchestrator
from ..services.trading.safe_trading_system import SafeTradingSystem

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
    amount: float
    price: float
    mode: str = "paper"  # 'paper' or 'live'

class TradeResponse(BaseModel):
    id: str
    botId: Optional[str]
    pair: str
    side: str
    amount: float
    price: float
    timestamp: str
    status: str
    pnl: Optional[float] = None

# In-memory trade storage (in production, use database)
trades_store = {}

# Initialize safe trading system
safe_trading_system = SafeTradingSystem()

@router.get("/", response_model=List[TradeResponse])
async def get_trades(
    botId: Optional[str] = Query(None),
    mode: Optional[str] = Query(None, pattern="^(paper|live)$"),
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
            response_trades.append(TradeResponse(
                id=trade["id"],
                botId=trade.get("botId"),
                pair=trade["pair"],
                side=trade["side"],
                amount=trade["amount"],
                price=trade["price"],
                timestamp=trade["timestamp"],
                status=trade["status"],
                pnl=trade.get("pnl")
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

        # Execute the trade if it's live mode
        if trade.mode == "live":
            try:
                # Use exchange service to place the order
                order_result = await default_exchange.place_order(
                    pair=trade.pair,
                    side=trade.side,
                    order_type="limit",  # or "market" based on price
                    amount=trade.amount,
                    price=trade.price if trade.price else None
                )

                # Update trade status based on order result
                new_trade["status"] = order_result.get("status", "completed")
                new_trade["exchange_order_id"] = order_result.get("id")

                # Record trade result in safe trading system for risk monitoring
                pnl = 0.0  # In live trading, this would be calculated from actual execution
                await safe_trading_system.record_trade_result(trade_details, pnl)

                logger.info(f"Live trade executed: {new_trade}")

            except Exception as e:
                logger.error(f"Failed to execute live trade: {e}")
                new_trade["status"] = "failed"
                new_trade["error"] = str(e)
        else:
            # Paper trade - mark as completed immediately
            new_trade["status"] = "completed"

            # Calculate mock P&L for paper trades
            pnl = 0.0
            if trade.side == "sell":
                # Mock profit/loss calculation
                pnl = trade.amount * (trade.price - 45000)  # Mock entry price
                new_trade["pnl"] = pnl

            # Record paper trade result in safe trading system
            await safe_trading_system.record_trade_result(trade_details, pnl)

        return TradeResponse(
            id=new_trade["id"],
            botId=new_trade.get("botId"),
            pair=new_trade["pair"],
            side=new_trade["side"],
            amount=new_trade["amount"],
            price=new_trade["price"],
            timestamp=new_trade["timestamp"],
            status=new_trade["status"],
            pnl=new_trade.get("pnl")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create trade: {e}")
        raise HTTPException(status_code=500, detail="Failed to create trade")
