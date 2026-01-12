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
from ..services.market_data_service import get_market_data_service
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
        market_data = get_market_data_service()

        if mode == "real":
            # Get real portfolio data from blockchain wallets (DEX-only)
            try:
                from ..repositories.wallet_repository import WalletRepository
                from ..services.blockchain.balance_service import get_balance_service

                balance_service = get_balance_service()
                wallet_repo = WalletRepository(db)

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

                # 1. Aggregate balances across all wallets
                aggregated_balances = {}  # symbol -> amount
                available_balance = 0.0

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
                            aggregated_balances[asset_symbol] = aggregated_balances.get(
                                asset_symbol, 0.0
                            ) + float(native_balance)

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
                                    aggregated_balances[token_symbol] = (
                                        aggregated_balances.get(token_symbol, 0.0)
                                        + float(token_balance)
                                    )
                                    if token_symbol in ["USDC", "USDT", "DAI"]:
                                        available_balance += float(token_balance)
                            except Exception as e:
                                logger.debug(
                                    f"Failed to get {token_symbol} balance: {e}"
                                )

                    except Exception as e:
                        logger.warning(
                            f"Failed to get balances for wallet {wallet_address}: {e}"
                        )

                # 2. Batch fetch prices and calculate P&L
                symbols = list(aggregated_balances.keys())
                price_symbols = [f"{s}/USD" for s in symbols]

                # Use batch price fetching
                current_prices_raw = await market_data.get_prices_batch(price_symbols)
                current_prices = {
                    s: current_prices_raw.get(f"{s}/USD") or 0.0 for s in symbols
                }
                # Fix for stablecoins
                for s in ["USDC", "USDT", "DAI"]:
                    if s in current_prices and current_prices[s] == 0:
                        current_prices[s] = 1.0

                # Batch calculate P&L
                batch_pnl = await pnl_service.calculate_batch_position_pnl(
                    user_id=user_id,
                    symbols=price_symbols,
                    current_prices={f"{s}/USD": current_prices[s] for s in symbols},
                    mode="real",
                )

                # 3. Build final positions
                positions = {}
                total_balance = 0.0

                for asset_symbol, amount in aggregated_balances.items():
                    price_symbol = f"{asset_symbol}/USD"
                    current_price = current_prices.get(asset_symbol, 0.0)
                    total_value = amount * current_price
                    total_balance += total_value

                    pnl_data = batch_pnl.get(price_symbol, {})
                    positions[asset_symbol] = Position(
                        asset=asset_symbol,
                        amount=amount,
                        averagePrice=pnl_data.get("average_price", current_price),
                        currentPrice=current_price,
                        totalValue=total_value,
                        profitLoss=pnl_data.get("pnl", 0.0),
                        profitLossPercent=pnl_data.get("pnl_percent", 0.0),
                    )

                # Get performance metrics
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
                except Exception:
                    successful_trades = failed_trades = total_trades = win_rate = (
                        average_win
                    ) = average_loss = 0

                # Portfolio-level P&L
                profit_loss_24h = await pnl_service.calculate_24h_pnl(
                    str(user_id), "real"
                )
                profit_loss_total = await pnl_service.calculate_total_pnl(
                    str(user_id), "real"
                )

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
                logger.error(f"Failed to get live portfolio: {e}", exc_info=True)
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

        else:  # paper mode
            try:
                from ..services.backtesting.paper_trading_service import (
                    PaperTradingService,
                )

                paper_service = PaperTradingService()
                paper_portfolio = await paper_service.get_paper_portfolio(str(user_id))

                # 1. Collect symbols and balances
                paper_positions = paper_portfolio.positions or []
                symbols = [p.symbol for p in paper_positions]
                price_symbols = [f"{s}/USD" for s in symbols]

                # 2. Batch fetch prices and calculate P&L
                current_prices_raw = await market_data.get_prices_batch(price_symbols)
                current_prices = {
                    s: current_prices_raw.get(f"{s}/USD") or 0.0 for s in symbols
                }

                batch_pnl = await pnl_service.calculate_batch_position_pnl(
                    user_id=user_id,
                    symbols=price_symbols,
                    current_prices={f"{s}/USD": current_prices[s] for s in symbols},
                    mode="paper",
                )

                # 3. Build positions
                positions = {}
                for pos in paper_positions:
                    symbol = pos.symbol
                    price_symbol = f"{symbol}/USD"
                    current_price = current_prices.get(symbol, 0.0)
                    pnl_data = batch_pnl.get(price_symbol, {})

                    positions[symbol] = Position(
                        asset=symbol,
                        amount=pos.quantity,
                        averagePrice=pnl_data.get("average_price", current_price),
                        currentPrice=current_price,
                        totalValue=pos.quantity * current_price,
                        profitLoss=pnl_data.get("pnl", 0.0),
                        profitLossPercent=pnl_data.get("pnl_percent", 0.0),
                    )

                # Portfolio-level metrics
                profit_loss_24h = await pnl_service.calculate_24h_pnl(
                    str(user_id), "paper"
                )
                profit_loss_total = await pnl_service.calculate_total_pnl(
                    str(user_id), "paper"
                )

                # Analytics
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
                except Exception:
                    successful_trades = failed_trades = total_trades = win_rate = (
                        average_win
                    ) = average_loss = 0

                return Portfolio(
                    totalBalance=paper_portfolio.total_balance or 0.0,
                    availableBalance=paper_portfolio.available_balance or 0.0,
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
                logger.error(f"Failed to get paper portfolio: {e}", exc_info=True)
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting portfolio for mode {mode}: {e}", exc_info=True)
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
