from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging
import jwt
import os
from ..services.exchange_service import default_exchange
from ..services.analytics_engine import analytics_engine

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

class Position(BaseModel):
    asset: str
    amount: float
    averagePrice: float
    currentPrice: float
    totalValue: float
    profitLoss: float
    profitLossPercent: float

class Portfolio(BaseModel):
    totalBalance: float
    availableBalance: float
    positions: Dict[str, Position]
    profitLoss24h: float
    profitLossTotal: float
    successfulTrades: Optional[int] = None
    failedTrades: Optional[int] = None
    totalTrades: Optional[int] = None
    winRate: Optional[float] = None
    averageWin: Optional[float] = None
    averageLoss: Optional[float] = None

@router.get("/{mode}")
async def get_portfolio(mode: str, current_user: dict = Depends(get_current_user)) -> Portfolio:
    """Get portfolio for paper or live trading mode"""
    try:
        if mode not in ["paper", "live"]:
            raise HTTPException(status_code=400, detail="Mode must be 'paper' or 'live'")

        user_id = current_user.get("user_id", 1)

        if mode == "live":
            # Get real portfolio data from exchange
            try:
                balance = await default_exchange.get_balance()
                positions = {}

                total_balance = 0.0
                available_balance = 0.0

                for asset, amount in balance.items():
                    if amount > 0:
                        # Get current price for each asset
                        if asset == "USD" or asset == "USDT" or asset == "USDC":
                            # Stablecoins - value is 1:1
                            current_price = 1.0
                            total_value = amount
                        else:
                            # Get price from exchange for crypto assets
                            pair = f"{asset}/USD"
                            current_price = await default_exchange.get_market_price(pair)
                            if current_price is None:
                                current_price = 0.0
                            total_value = amount * current_price

                        total_balance += total_value

                        # For now, assume available balance is the USD amount
                        if asset == "USD":
                            available_balance = amount

                        # Create position if it's a trading asset (not USD)
                        if asset != "USD" and asset != "USDT" and asset != "USDC":
                            # Mock average price and P&L calculation
                            average_price = current_price * 0.95  # Assume bought at 5% lower price
                            profit_loss = (current_price - average_price) * amount
                            profit_loss_percent = (profit_loss / (average_price * amount)) * 100

                            positions[asset] = Position(
                                asset=asset,
                                amount=amount,
                                averagePrice=average_price,
                                currentPrice=current_price,
                                totalValue=total_value,
                                profitLoss=profit_loss,
                                profitLossPercent=profit_loss_percent
                            )

                # Get analytics data for performance metrics
                try:
                    analytics_params = {"user_id": user_id, "type": "summary"}
                    analytics_result = await analytics_engine.analyze(analytics_params)

                    successful_trades = analytics_result.get("successfulTrades", 0)
                    failed_trades = analytics_result.get("failedTrades", 0)
                    total_trades = successful_trades + failed_trades
                    win_rate = successful_trades / total_trades if total_trades > 0 else 0.0
                    average_win = analytics_result.get("averageWin", 0.0)
                    average_loss = analytics_result.get("averageLoss", 0.0)

                except Exception as e:
                    logger.warning(f"Failed to get analytics data: {e}")
                    successful_trades = failed_trades = total_trades = win_rate = average_win = average_loss = 0

                # Calculate 24h P&L (mock for now)
                profit_loss_24h = total_balance * 0.02  # Assume 2% 24h change
                profit_loss_total = total_balance - 100000  # Assume started with $100k

                return Portfolio(
                    totalBalance=total_balance,
                    availableBalance=available_balance,
                    positions=positions,
                    profitLoss24h=profit_loss_24h,
                    profitLossTotal=profit_loss_total,
                    successfulTrades=successful_trades,
                    failedTrades=failed_trades,
                    totalTrades=total_trades,
                    winRate=win_rate,
                    averageWin=average_win,
                    averageLoss=average_loss
                )

            except Exception as e:
                logger.error(f"Failed to get live portfolio: {e}")
                # Fall back to mock data
                return Portfolio(
                    totalBalance=50000.0,
                    availableBalance=48000.0,
                    positions={
                        "BTC": Position(
                            asset="BTC",
                            amount=0.5,
                            averagePrice=49000.0,
                            currentPrice=50000.0,
                            totalValue=25000.0,
                            profitLoss=500.0,
                            profitLossPercent=2.0
                        )
                    },
                    profitLoss24h=320.75,
                    profitLossTotal=1820.0,
                    successfulTrades=23,
                    failedTrades=8,
                    totalTrades=31,
                    winRate=0.742,
                    averageWin=145.25,
                    averageLoss=-125.50
                )

        else:  # paper mode
            # Mock paper trading portfolio
            return Portfolio(
                totalBalance=100000.0,
                availableBalance=95000.0,
                positions={
                    "BTC": Position(
                        asset="BTC",
                        amount=1.2,
                        averagePrice=48000.0,
                        currentPrice=50000.0,
                        totalValue=60000.0,
                        profitLoss=4800.0,
                        profitLossPercent=8.0
                    ),
                    "ETH": Position(
                        asset="ETH",
                        amount=10.0,
                        averagePrice=3200.0,
                        currentPrice=3500.0,
                        totalValue=35000.0,
                        profitLoss=3000.0,
                        profitLossPercent=9.4
                    )
                },
                profitLoss24h=1250.50,
                profitLossTotal=7800.0,
                successfulTrades=45,
                failedTrades=12,
                totalTrades=57,
                winRate=0.789,
                averageWin=215.50,
                averageLoss=-180.25
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting portfolio for mode {mode}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get portfolio")
