import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..dependencies.pnl import get_pnl_service
from ..middleware.cache_manager import cached
from ..services.analytics_engine import analytics_engine
from ..services.coingecko_service import CoinGeckoService
from ..services.pnl_service import PnLService
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


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
    positions: dict[str, Position]
    profitLoss24h: float
    profitLossTotal: float
    successfulTrades: int | None = None
    failedTrades: int | None = None
    totalTrades: int | None = None
    winRate: float | None = None
    averageWin: float | None = None
    averageLoss: float | None = None


@router.get("/{mode}")
@cached(ttl=300, prefix="portfolio")  # 5min TTL for portfolio data
async def get_portfolio(
    mode: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    pnl_service: Annotated[PnLService, Depends(get_pnl_service)],
) -> Portfolio:
    """Get portfolio for paper or real trading mode"""
    try:
        from ..utils.trading_utils import normalize_trading_mode

        mode = normalize_trading_mode(mode)

        if mode not in ["paper", "real"]:
            raise HTTPException(
                status_code=400, detail="Mode must be 'paper' or 'real'"
            )

        user_id = _get_user_id(current_user)

        if mode == "real":
            # Get real portfolio data from blockchain wallets (DEX-only)
            try:
                from ..repositories.wallet_repository import WalletRepository
                from ..services.blockchain.balance_service import get_balance_service

                balance_service = get_balance_service()
                wallet_repo = WalletRepository(db)
                coingecko = CoinGeckoService()

                # Get all user wallets across all chains
                user_id_str = str(user_id)
                wallets = await wallet_repo.get_wallets_by_user(user_id_str)

                if not wallets:
                    # No wallets found - return empty portfolio with helpful message
                    logger.info(f"No wallets found for user {user_id_str}")
                    return Portfolio(
                        totalBalance=0.0,
                        availableBalance=0.0,
                        positions={},
                        profitLoss24h=0.0,
                        profitLossTotal=0.0,
                        successfulTrades=0,
                        failedTrades=0,
                        totalTrades=0,
                        winRate=0.0,
                        averageWin=0.0,
                        averageLoss=0.0,
                    )

                positions = {}
                total_balance = 0.0
                available_balance = 0.0

                # Aggregate balances from all wallets
                for wallet in wallets:
                    chain_id = wallet.chain_id if hasattr(wallet, "chain_id") else 1
                    wallet_address = (
                        wallet.wallet_address
                        if hasattr(wallet, "wallet_address")
                        else wallet.address
                    )

                    try:
                        # Get native token balance (ETH, MATIC, etc.)
                        native_balance = await balance_service.get_eth_balance(
                            chain_id=chain_id, address=wallet_address, use_cache=True
                        )

                        if native_balance and native_balance > 0:
                            # Get native token symbol based on chain
                            chain_symbols = {
                                1: "ETH",  # Ethereum
                                8453: "ETH",  # Base
                                42161: "ETH",  # Arbitrum
                                137: "MATIC",  # Polygon
                                43114: "AVAX",  # Avalanche
                                56: "BNB",  # BNB Chain
                            }
                            asset_symbol = chain_symbols.get(chain_id, "ETH")

                            # Get current price
                            price_symbol = f"{asset_symbol}/USD"
                            current_price = (
                                await coingecko.get_price(price_symbol) or 0.0
                            )
                            total_value = float(native_balance) * current_price

                            # Aggregate positions by symbol (sum across chains)
                            if asset_symbol in positions:
                                positions[asset_symbol].amount += float(native_balance)
                                positions[asset_symbol].totalValue += total_value
                            else:
                                # ✅ Use injected service
                                pair_symbol = f"{asset_symbol}/USD"

                                try:
                                    position_pnl = (
                                        await pnl_service.calculate_position_pnl(
                                            user_id=user_id,
                                            symbol=pair_symbol,
                                            current_price=current_price,
                                            mode="real",
                                        )
                                    )
                                    average_price = position_pnl.get(
                                        "average_price", current_price
                                    )
                                    profit_loss = position_pnl.get("pnl", 0.0)
                                    profit_loss_percent = position_pnl.get(
                                        "pnl_percent", 0.0
                                    )
                                except Exception as e:
                                    logger.warning(
                                        f"Failed to calculate P&L for {asset_symbol}: {e}"
                                    )
                                    average_price = current_price
                                    profit_loss = 0.0
                                    profit_loss_percent = 0.0

                                positions[asset_symbol] = Position(
                                    asset=asset_symbol,
                                    amount=float(native_balance),
                                    averagePrice=average_price,
                                    currentPrice=current_price,
                                    totalValue=total_value,
                                    profitLoss=profit_loss,
                                    profitLossPercent=profit_loss_percent,
                                )

                            total_balance += total_value
                            if asset_symbol in ["USDC", "USDT", "DAI"]:
                                available_balance += float(native_balance)

                        # Get ERC-20 token balances (USDC, USDT, etc.)
                        # Common token addresses per chain
                        common_tokens = {
                            1: {  # Ethereum
                                "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0c3606eB48",
                                "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                                "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                                "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
                            },
                            8453: {  # Base
                                "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                            },
                            42161: {  # Arbitrum
                                "USDC": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
                            },
                        }

                        chain_tokens = common_tokens.get(chain_id, {})
                        for token_symbol, token_address in chain_tokens.items():
                            try:
                                token_balance = await balance_service.get_token_balance(
                                    chain_id=chain_id,
                                    address=wallet_address,
                                    token_address=token_address,
                                )

                                if token_balance and token_balance > 0:
                                    # Get current price
                                    if token_symbol in ["USDC", "USDT", "DAI"]:
                                        current_price = 1.0  # Stablecoins
                                        total_value = float(token_balance)
                                        available_balance += float(token_balance)
                                    else:
                                        price_symbol = f"{token_symbol}/USD"
                                        current_price = (
                                            await coingecko.get_price(price_symbol)
                                            or 0.0
                                        )
                                        total_value = (
                                            float(token_balance) * current_price
                                        )

                                    # Aggregate positions
                                    if token_symbol in positions:
                                        positions[token_symbol].amount += float(
                                            token_balance
                                        )
                                        positions[
                                            token_symbol
                                        ].totalValue += total_value
                                    else:
                                        # ✅ Use injected service
                                        pair_symbol = f"{token_symbol}/USD"

                                        try:
                                            position_pnl = await pnl_service.calculate_position_pnl(
                                                user_id=user_id,
                                                symbol=pair_symbol,
                                                current_price=current_price,
                                                mode="real",
                                            )
                                            average_price = position_pnl.get(
                                                "average_price", current_price
                                            )
                                            profit_loss = position_pnl.get("pnl", 0.0)
                                            profit_loss_percent = position_pnl.get(
                                                "pnl_percent", 0.0
                                            )
                                        except Exception as e:
                                            logger.warning(
                                                f"Failed to calculate P&L for {token_symbol}: {e}"
                                            )
                                            average_price = current_price
                                            profit_loss = 0.0
                                            profit_loss_percent = 0.0

                                        positions[token_symbol] = Position(
                                            asset=token_symbol,
                                            amount=float(token_balance),
                                            averagePrice=average_price,
                                            currentPrice=current_price,
                                            totalValue=total_value,
                                            profitLoss=profit_loss,
                                            profitLossPercent=profit_loss_percent,
                                        )

                                    total_balance += total_value
                            except Exception as e:
                                logger.warning(
                                    f"Failed to get {token_symbol} balance on chain {chain_id}: {e}"
                                )
                                continue

                    except Exception as e:
                        logger.warning(
                            f"Failed to get balances for wallet {wallet_address} on chain {chain_id}: {e}"
                        )
                        continue

                # Get analytics data for performance metrics
                try:
                    analytics_params = {"user_id": user_id, "type": "summary"}
                    analytics_result = await analytics_engine.analyze(analytics_params)

                    successful_trades = analytics_result.get("successfulTrades", 0)
                    failed_trades = analytics_result.get("failedTrades", 0)
                    total_trades = successful_trades + failed_trades
                    win_rate = (
                        successful_trades / total_trades if total_trades > 0 else 0.0
                    )
                    average_win = analytics_result.get("averageWin", 0.0)
                    average_loss = analytics_result.get("averageLoss", 0.0)

                except Exception as e:
                    logger.warning(f"Failed to get analytics data: {e}")
                    successful_trades = failed_trades = total_trades = win_rate = (
                        average_win
                    ) = average_loss = 0

                # ✅ Use injected service - Calculate P&L from trade history using PnLService
                try:
                    profit_loss_24h = await pnl_service.calculate_24h_pnl(
                        str(user_id), "real"
                    )
                    profit_loss_total = await pnl_service.calculate_total_pnl(
                        str(user_id), "real"
                    )
                except Exception as e:
                    logger.warning(f"Failed to calculate portfolio P&L: {e}")
                    profit_loss_24h = 0.0
                    profit_loss_total = 0.0

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
                    averageLoss=average_loss,
                )

            except Exception as e:
                logger.error(f"Failed to get live portfolio: {e}")
                # Return empty portfolio instead of mock data
                try:
                    # Try to get at least P&L data
                    profit_loss_24h = await pnl_service.calculate_24h_pnl(
                        str(user_id), "real"
                    )
                    profit_loss_total = await pnl_service.calculate_total_pnl(
                        str(user_id), "real"
                    )
                except Exception:
                    profit_loss_24h = 0.0
                    profit_loss_total = 0.0

                return Portfolio(
                    totalBalance=0.0,
                    availableBalance=0.0,
                    positions={},
                    profitLoss24h=profit_loss_24h,
                    profitLossTotal=profit_loss_total,
                    successfulTrades=0,
                    failedTrades=0,
                    totalTrades=0,
                    winRate=0.0,
                    averageWin=0.0,
                    averageLoss=0.0,
                )

        else:  # paper mode
            # Get paper trading portfolio from database
            try:
                from ..services.backtesting.paper_trading_service import (
                    PaperTradingService,
                )

                paper_service = PaperTradingService()
                paper_portfolio = await paper_service.get_paper_portfolio(str(user_id))

                # ✅ Use injected service - Calculate P&L from trade history
                try:
                    profit_loss_24h = await pnl_service.calculate_24h_pnl(
                        str(user_id), "paper"
                    )
                except Exception as e:
                    logger.warning(f"Failed to calculate 24h P&L: {e}")
                    profit_loss_24h = 0.0

                try:
                    profit_loss_total = await pnl_service.calculate_total_pnl(
                        str(user_id), "paper"
                    )
                except Exception as e:
                    logger.warning(f"Failed to calculate total P&L: {e}")
                    profit_loss_total = 0.0

                # Build positions with real P&L calculations
                positions = {}
                total_balance = paper_portfolio.total_balance or 100000.0
                available_balance = paper_portfolio.available_balance or 95000.0

                # Get current prices for positions
                for position in paper_portfolio.positions or []:
                    symbol = position.symbol
                    amount = position.quantity

                    # Get current price
                    try:
                        # Get price from CoinGecko instead of exchange
                        coingecko = CoinGeckoService()
                        ticker = await coingecko.get_price(
                            symbol
                        )  # CoinGecko handles symbol conversion
                        current_price = float(ticker) if ticker else 0.0
                    except:
                        current_price = 0.0

                    # Calculate P&L from trade history
                    try:
                        position_pnl = await pnl_service.calculate_position_pnl(
                            user_id=str(user_id),
                            symbol=f"{symbol}/USD",
                            current_price=current_price,
                            mode="paper",
                        )
                        average_price = position_pnl.get("average_price", current_price)
                        profit_loss = position_pnl.get("pnl", 0.0)
                        profit_loss_percent = position_pnl.get("pnl_percent", 0.0)
                    except Exception as e:
                        logger.warning(f"Failed to calculate P&L for {symbol}: {e}")
                        average_price = current_price
                        profit_loss = 0.0
                        profit_loss_percent = 0.0

                    positions[symbol] = Position(
                        asset=symbol,
                        amount=amount,
                        averagePrice=average_price,
                        currentPrice=current_price,
                        totalValue=amount * current_price,
                        profitLoss=profit_loss,
                        profitLossPercent=profit_loss_percent,
                    )

                # Get analytics data
                try:
                    analytics_params = {"user_id": str(user_id), "type": "summary"}
                    analytics_result = await analytics_engine.analyze(analytics_params)
                    successful_trades = analytics_result.get("successfulTrades", 0)
                    failed_trades = analytics_result.get("failedTrades", 0)
                    total_trades = successful_trades + failed_trades
                    win_rate = (
                        successful_trades / total_trades if total_trades > 0 else 0.0
                    )
                    average_win = analytics_result.get("averageWin", 0.0)
                    average_loss = analytics_result.get("averageLoss", 0.0)
                except Exception as e:
                    logger.warning(f"Failed to get analytics data: {e}")
                    successful_trades = failed_trades = total_trades = win_rate = (
                        average_win
                    ) = average_loss = 0

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
                    averageLoss=average_loss,
                )

            except Exception as e:
                logger.error(f"Failed to get paper portfolio: {e}")
                # ✅ Use injected service - Fallback to minimal portfolio if paper trading service fails
                try:
                    profit_loss_24h = await pnl_service.calculate_24h_pnl(
                        str(user_id), "paper"
                    )
                    profit_loss_total = await pnl_service.calculate_total_pnl(
                        str(user_id), "paper"
                    )
                except:
                    profit_loss_24h = 0.0
                    profit_loss_total = 0.0

                return Portfolio(
                    totalBalance=100000.0,
                    availableBalance=95000.0,
                    positions={},
                    profitLoss24h=profit_loss_24h,
                    profitLossTotal=profit_loss_total,
                    successfulTrades=0,
                    failedTrades=0,
                    totalTrades=0,
                    winRate=0.0,
                    averageWin=0.0,
                    averageLoss=0.0,
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting portfolio for mode {mode}: {e}", exc_info=True)
        # Return minimal portfolio instead of 500 error for better UX during development
        logger.warning(f"Returning minimal portfolio due to error: {e}")
        try:
            user_id = _get_user_id(current_user)
        except HTTPException:
            user_id = "unknown"  # Fallback for error case
        return Portfolio(
            totalBalance=100000.0,
            availableBalance=95000.0,
            positions={},
            profitLoss24h=0.0,
            profitLossTotal=0.0,
            successfulTrades=0,
            failedTrades=0,
            totalTrades=0,
            winRate=0.0,
            averageWin=0.0,
            averageLoss=0.0,
        )
