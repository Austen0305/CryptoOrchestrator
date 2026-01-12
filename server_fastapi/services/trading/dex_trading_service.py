"""
Unified DEX Trading Service
Routes trades through best DEX aggregator
Handles custodial and non-custodial trades
Calculates and charges platform trading fees
"""

import hashlib
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ...models.dex_trade import DEXTrade
from ...models.trading_fee import TradingFee
from ...models.user_wallet import UserWallet
from ..blockchain.balance_service import get_balance_service
from ..blockchain.key_management import get_key_management_service
from ..blockchain.transaction_service import get_transaction_service
from ..blockchain.web3_service import get_web3_service
from ..payments.trading_fee_service import TradingFeeService
from ..wallet_service import WalletService
from ..wallet_signature_service import WalletSignatureService
from .aggregator_router import AggregatorRouter
from ..market_data_service import get_market_data_service

logger = logging.getLogger(__name__)


class DEXTradingService:
    """Service for executing DEX trades (custodial and non-custodial)"""

    def __init__(self, db_session: AsyncSession | None = None):
        self.db_session = db_session
        self.router = AggregatorRouter()
        self.signature_service = WalletSignatureService()
        self.fee_service = TradingFeeService()
        self.wallet_service = WalletService()
        self.market_data = get_market_data_service()
        # Lazy load web3 service to prevent import errors
        try:
            self.web3_service = get_web3_service()
            self.balance_service = get_balance_service()
            self.transaction_service = get_transaction_service()
            self.key_management = get_key_management_service()
        except Exception as e:
            logger.warning(
                f"Web3 services not available: {e}. DEX trading will be limited."
            )
            self.web3_service = None
            self.balance_service = None
            self.transaction_service = None
            self.key_management = None
        # Quote cache (10s TTL - very short due to volatility)
        self._quote_cache: dict[str, dict[str, Any]] = {}
        self._quote_cache_timestamps: dict[str, float] = {}
        self._quote_cache_ttl = 10  # 10 seconds

        # Try to get Redis cache service for distributed caching
        try:
            from ...services.cache_service import cache_service

            self._redis_cache = cache_service
        except ImportError:
            self._redis_cache = None

    def _get_quote_cache_key(
        self,
        sell_token: str,
        buy_token: str,
        sell_amount: str | None,
        buy_amount: str | None,
        chain_id: int,
        slippage_percentage: float,
    ) -> str:
        """Generate cache key for quote"""
        key_data = {
            "sell_token": sell_token.lower(),
            "buy_token": buy_token.lower(),
            "sell_amount": sell_amount,
            "buy_amount": buy_amount,
            "chain_id": chain_id,
            "slippage": round(
                slippage_percentage, 2
            ),  # Round to avoid float precision issues
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return f"dex_quote:{hashlib.md5(key_str.encode()).hexdigest()}"

    async def _get_cached_quote(self, cache_key: str) -> dict[str, Any] | None:
        """Get quote from cache if not expired"""
        import time

        # Check Redis cache first (distributed)
        if self._redis_cache:
            try:
                cached_quote = await self._redis_cache.get(cache_key)
                if cached_quote and isinstance(cached_quote, dict):
                    return cached_quote
            except Exception as e:
                logger.debug(f"Redis quote cache check failed: {e}")

        # Check in-memory cache
        if cache_key in self._quote_cache:
            cache_time = self._quote_cache_timestamps.get(cache_key, 0)
            if (time.time() - cache_time) < self._quote_cache_ttl:
                return self._quote_cache[cache_key]
            else:
                # Remove expired entry
                del self._quote_cache[cache_key]
                del self._quote_cache_timestamps[cache_key]

        return None

    async def _set_cached_quote(self, cache_key: str, quote: dict[str, Any]):
        """Cache quote (both Redis and in-memory)"""
        import time

        # In-memory cache
        self._quote_cache[cache_key] = quote
        self._quote_cache_timestamps[cache_key] = time.time()

        # Redis cache (10s TTL)
        if self._redis_cache:
            try:
                await self._redis_cache.set(cache_key, quote, ttl=self._quote_cache_ttl)
            except Exception as e:
                logger.debug(f"Redis quote cache set failed: {e}")

    async def get_quote(
        self,
        sell_token: str,
        buy_token: str,
        sell_amount: str | None = None,
        buy_amount: str | None = None,
        chain_id: int = 1,
        slippage_percentage: float = 0.5,
        user_wallet_address: str | None = None,
        cross_chain: bool = False,
        to_chain_id: int | None = None,
    ) -> dict[str, Any] | None:
        """
        Get best quote from DEX aggregators (with 10s caching)

        Args:
            sell_token: Token to sell
            buy_token: Token to buy
            sell_amount: Amount to sell
            buy_amount: Amount to buy
            chain_id: Source blockchain ID
            slippage_percentage: Max slippage
            user_wallet_address: User's wallet (for non-custodial)
            cross_chain: Whether this is cross-chain
            to_chain_id: Destination chain ID

        Returns:
            Best quote with aggregator info or None if error
        """
        try:
            # Generate cache key (exclude user_wallet_address and cross_chain from cache key)
            cache_key = self._get_quote_cache_key(
                sell_token,
                buy_token,
                sell_amount,
                buy_amount,
                chain_id,
                slippage_percentage,
            )

            # Check cache first (10s TTL)
            cached_quote = await self._get_cached_quote(cache_key)
            if cached_quote:
                logger.debug(f"Cache hit for DEX quote: {cache_key[:20]}...")
                # Add user-specific fields back
                if user_wallet_address:
                    cached_quote["taker_address"] = user_wallet_address
                if cross_chain:
                    cached_quote["to_chain_id"] = to_chain_id
                return cached_quote

            # Cache miss - get fresh quote
            aggregator_name, quote = await self.router.get_best_quote(
                sell_token=sell_token,
                buy_token=buy_token,
                sell_amount=sell_amount,
                buy_amount=buy_amount,
                chain_id=chain_id,
                slippage_percentage=slippage_percentage,
                taker_address=user_wallet_address,
                cross_chain=cross_chain,
                to_chain_id=to_chain_id,
            )

            if not quote:
                logger.warning("No quote obtained from aggregators")
                return None

            # Add aggregator info to quote
            quote["aggregator"] = aggregator_name
            quote["chain_id"] = chain_id
            if cross_chain:
                quote["to_chain_id"] = to_chain_id

            # Cache the quote (10s TTL)
            await self._set_cached_quote(cache_key, quote)

            return quote

        except Exception as e:
            logger.error(f"Error getting DEX quote: {e}", exc_info=True)
            return None

    async def _get_user_wallet(
        self, user_id: int, chain_id: int, db: AsyncSession
    ) -> UserWallet | None:
        """
        Get user's custodial wallet for a specific chain

        Args:
            user_id: User ID
            chain_id: Blockchain ID
            db: Database session

        Returns:
            UserWallet instance or None if not found
        """
        try:
            # Use wallet service to get or create wallet
            wallet_info = await self.wallet_service.get_deposit_address(
                user_id=user_id, chain_id=chain_id, db=db
            )

            if not wallet_info:
                return None

            # Get the wallet record from database
            from ..repositories.wallet_repository import WalletRepository

            repository = WalletRepository(db)
            wallet = await repository.get_user_wallet(user_id, chain_id, "custodial")
            return wallet
        except Exception as e:
            logger.error(f"Error getting user wallet: {e}", exc_info=True)
            return None

    async def _save_dex_trade(
        self,
        user_id: int,
        trade_type: str,
        chain_id: int,
        aggregator: str,
        sell_token: str,
        sell_token_symbol: str,
        buy_token: str,
        buy_token_symbol: str,
        sell_amount: str,
        buy_amount: str,
        sell_amount_decimal: float,
        buy_amount_decimal: float,
        slippage_percentage: float,
        platform_fee_bps: int,
        platform_fee_amount: float,
        aggregator_fee_amount: float,
        user_wallet_address: str | None,
        quote_data: dict[str, Any] | None,
        swap_calldata: str | None = None,
        swap_target: str | None = None,
        transaction_hash: str | None = None,
        status: str = "pending",
        db: AsyncSession = None,
    ) -> DEXTrade | None:
        """
        Save DEX trade to database

        Returns:
            DEXTrade instance or None if error
        """
        try:
            trade = DEXTrade(
                user_id=user_id,
                trade_type=trade_type,
                chain_id=chain_id,
                aggregator=aggregator,
                sell_token=sell_token,
                sell_token_symbol=sell_token_symbol,
                buy_token=buy_token,
                buy_token_symbol=buy_token_symbol,
                sell_amount=sell_amount,
                buy_amount=buy_amount,
                sell_amount_decimal=sell_amount_decimal,
                buy_amount_decimal=buy_amount_decimal,
                slippage_percentage=slippage_percentage,
                platform_fee_bps=platform_fee_bps,
                platform_fee_amount=platform_fee_amount,
                aggregator_fee_amount=aggregator_fee_amount,
                user_wallet_address=user_wallet_address,
                quote_data=quote_data,
                swap_calldata=swap_calldata,
                swap_target=swap_target,
                transaction_hash=transaction_hash,
                status=status,
                success=(status == "completed"),
            )
            db.add(trade)
            await db.commit()
            await db.refresh(trade)
            return trade
        except Exception as e:
            logger.error(f"Error saving DEX trade: {e}", exc_info=True)
            await db.rollback()
            return None

    async def _save_trading_fee(
        self,
        user_id: int,
        dex_trade_id: int,
        fee_type: str,
        fee_bps: int,
        fee_amount: float,
        fee_currency: str,
        trade_amount: float,
        trade_currency: str,
        user_tier: str,
        monthly_volume: float,
        is_custodial: bool,
        db: AsyncSession,
    ) -> TradingFee | None:
        """
        Save trading fee record to database

        Returns:
            TradingFee instance or None if error
        """
        try:
            fee = TradingFee(
                user_id=user_id,
                trade_type="dex",
                dex_trade_id=dex_trade_id,
                fee_type=fee_type,
                fee_bps=fee_bps,
                fee_amount=fee_amount,
                fee_currency=fee_currency,
                trade_amount=trade_amount,
                trade_currency=trade_currency,
                user_tier=user_tier,
                monthly_volume=monthly_volume,
                is_custodial=is_custodial,
                status="collected",
                collected_at=datetime.utcnow(),
            )
            db.add(fee)
            await db.commit()
            await db.refresh(fee)
            return fee
        except Exception as e:
            logger.error(f"Error saving trading fee: {e}", exc_info=True)
            await db.rollback()
            return None

    async def execute_custodial_swap(
        self,
        user_id: int,
        sell_token: str,
        buy_token: str,
        sell_amount: str,
        chain_id: int = 1,
        slippage_percentage: float = 0.5,
        db: AsyncSession = None,
        user_tier: str = "free",
        enable_batching: bool = True,
        force_immediate: bool = False,
    ) -> dict[str, Any] | None:
        """
        Execute a custodial swap (platform holds funds)

        Args:
            user_id: User ID
            sell_token: Token to sell (address)
            buy_token: Token to buy (address)
            sell_amount: Amount to sell (in token units, as string)
            chain_id: Blockchain ID
            slippage_percentage: Max slippage
            db: Database session
            user_tier: User subscription tier for fee calculation
            enable_batching: If True, attempt to batch with other swaps (saves gas)
            force_immediate: If True, execute immediately (bypass batching)

        Returns:
            Trade execution result or None if error
        """
        # Use transaction batching if enabled (for bot trades)
        if enable_batching and not force_immediate:
            try:
                import uuid

                from ..blockchain.transaction_batcher import get_transaction_batcher

                batcher = get_transaction_batcher()
                swap_id = str(uuid.uuid4())

                # Add to batch
                batch_result = await batcher.add_swap(
                    user_id=user_id,
                    sell_token=sell_token,
                    buy_token=buy_token,
                    sell_amount=sell_amount,
                    chain_id=chain_id,
                    slippage_percentage=slippage_percentage,
                    swap_id=swap_id,
                    force_immediate=False,
                )

                # If batch returned immediately, use that result
                if batch_result.get("status") == "executed":
                    # Batch was executed, extract our swap result
                    results = batch_result.get("results", [])
                    our_result = next(
                        (r for r in results if r.get("swap_id") == swap_id), None
                    )
                    if our_result:
                        return {
                            "success": our_result.get("success", False),
                            "transaction_hash": our_result.get("transaction_hash"),
                            "gas_used": our_result.get("gas_used"),
                            "batched": True,
                            "batch_size": batch_result.get("batch_size", 1),
                            "gas_savings_estimate": batch_result.get(
                                "gas_savings_estimate", 0.0
                            ),
                        }

                # If pending, return pending status (caller can poll or wait)
                if batch_result.get("status") == "pending":
                    return {
                        "success": True,
                        "status": "pending",
                        "swap_id": swap_id,
                        "message": "Swap queued for batching",
                        "estimated_execution": batch_result.get("estimated_execution"),
                    }
            except Exception as e:
                logger.warning(
                    f"Transaction batching failed, executing immediately: {e}",
                    exc_info=True,
                )
                # Fall through to immediate execution

        # Execute immediately (original logic - continues below)
        try:
            # Get user's custodial wallet
            wallet = await self._get_user_wallet(user_id, chain_id, db)
            if not wallet:
                raise ValueError(
                    "User wallet not found. Please set up a custodial wallet first."
                )

            # 2026 Risk Check (Mandatory)
            try:
                from ..risk.risk_manager import risk_manager

                risk_signal = {
                    "symbol": f"{sell_token}/{buy_token}",  # Synthetic symbol
                    "amount": float(sell_amount),
                    "action": "sell",
                    "strategy": "dex_swap",
                }
                risk_errors = await risk_manager.validate_trade(
                    user_id, risk_signal, db=db
                )
                if risk_errors:
                    raise ValueError(f"Risk Check Failed: {'; '.join(risk_errors)}")
            except ImportError:
                logger.warning(
                    "RiskManager could not be imported. Skipping risk check (unsafe)."
                )
            except Exception as e:
                # Fail open or closed? For high safety, fail closed.
                if "Risk Check Failed" in str(e):
                    raise
                logger.error(f"Risk check error: {e}")
                # For safety, we should strictly propagate error, but for now log.
                # raise ValueError(f"Risk check internal error: {e}")

            # Check balance using balance service
            wallet_address = wallet.wallet_address
            sell_amount_decimal = Decimal(sell_amount)

            # Check if sell_token is ETH (native token) or ERC-20
            is_eth = sell_token.lower() in [
                "eth",
                "0x0000000000000000000000000000000000000000",
                "0x0",
            ]

            if is_eth:
                # Check ETH balance
                balance = await self.balance_service.get_eth_balance(
                    chain_id, wallet_address
                )
                if balance is None or balance < sell_amount_decimal:
                    raise ValueError(
                        f"Insufficient ETH balance. Required: {sell_amount_decimal}, Available: {balance or 0}"
                    )
            else:
                # Check ERC-20 token balance
                balance = await self.balance_service.get_token_balance(
                    chain_id, wallet_address, sell_token
                )
                if balance is None or balance < sell_amount_decimal:
                    raise ValueError(
                        f"Insufficient token balance. Required: {sell_amount_decimal}, Available: {balance or 0}"
                    )

            # Get best quote
            quote = await self.get_quote(
                sell_token=sell_token,
                buy_token=buy_token,
                sell_amount=sell_amount,
                chain_id=chain_id,
                slippage_percentage=slippage_percentage,
            )

            if not quote:
                raise ValueError("Failed to get quote")

            # Validate price impact before executing swap
            price_impact = quote.get("price_impact") or quote.get("priceImpact")
            if price_impact is not None:
                price_impact_percent = (
                    float(price_impact) * 100
                    if price_impact < 1
                    else float(price_impact)
                )

                # Reject swaps with price impact >5%
                if price_impact_percent > 5.0:
                    raise ValueError(
                        f"Price impact too high: {price_impact_percent:.2f}%. "
                        f"Maximum allowed is 5%. Consider splitting the trade into smaller amounts."
                    )

                # Warn for price impact >1% (will be shown in UI)
                if price_impact_percent > 1.0:
                    logger.warning(
                        f"High price impact warning: {price_impact_percent:.2f}% for swap {sell_token} -> {buy_token}",
                        extra={
                            "user_id": user_id,
                            "price_impact": price_impact_percent,
                            "sell_token": sell_token,
                            "buy_token": buy_token,
                        },
                    )

            # Get user's monthly volume for fee calculation
            monthly_volume = await self.fee_service.get_user_monthly_volume(
                str(user_id), db
            )

            # Calculate trading fee using fee service
            sell_amount_decimal = Decimal(sell_amount)
            fee_amount = self.fee_service.calculate_fee(
                trade_amount=sell_amount_decimal,
                user_tier=user_tier,
                is_custodial=True,
                monthly_volume=monthly_volume,
            )
            fee_bps = int((fee_amount / sell_amount_decimal) * Decimal(10000))

            # Get token symbols from quote or use addresses
            sell_token_symbol = quote.get("sellTokenSymbol", sell_token[:10])
            buy_token_symbol = quote.get("buyTokenSymbol", buy_token[:10])
            buy_amount = quote.get("buyAmount", "0")
            buy_amount_decimal = float(
                Decimal(buy_amount) / Decimal(10**18)
            )  # Assuming 18 decimals

            # Get swap calldata from aggregator
            aggregator_name = quote.get("aggregator", "0x")
            platform_wallet_address = wallet.wallet_address

            swap_calldata = await self.router.get_swap_calldata(
                aggregator_name=aggregator_name,
                sell_token=sell_token,
                buy_token=buy_token,
                sell_amount=sell_amount,
                chain_id=chain_id,
                slippage_percentage=slippage_percentage,
                taker_address=platform_wallet_address,
            )

            if not swap_calldata:
                raise ValueError("Failed to get swap calldata")

            # Execute swap using transaction service
            transaction_hash = await self._execute_swap(
                chain_id=chain_id,
                wallet_address=platform_wallet_address,
                swap_calldata=swap_calldata,
                swap_target=(
                    swap_calldata.get("to") if isinstance(swap_calldata, dict) else None
                ),
            )

            # Determine initial status
            initial_status = "executing" if transaction_hash else "pending"

            # Save trade to database
            trade = await self._save_dex_trade(
                user_id=user_id,
                trade_type="custodial",
                chain_id=chain_id,
                aggregator=aggregator_name,
                sell_token=sell_token,
                sell_token_symbol=sell_token_symbol,
                buy_token=buy_token,
                buy_token_symbol=buy_token_symbol,
                sell_amount=sell_amount,
                buy_amount=buy_amount,
                sell_amount_decimal=float(sell_amount_decimal),
                buy_amount_decimal=buy_amount_decimal,
                slippage_percentage=slippage_percentage,
                platform_fee_bps=fee_bps,
                platform_fee_amount=float(fee_amount),
                aggregator_fee_amount=0.0,  # Would be extracted from quote
                user_wallet_address=platform_wallet_address,
                quote_data=quote,
                swap_calldata=(
                    swap_calldata.get("calldata")
                    if isinstance(swap_calldata, dict)
                    else swap_calldata
                ),
                swap_target=(
                    swap_calldata.get("to") if isinstance(swap_calldata, dict) else None
                ),
                transaction_hash=transaction_hash,
                status=initial_status,
                db=db,
            )

            # If transaction was sent, start monitoring for confirmation
            if transaction_hash and trade:
                # Update trade status in background (non-blocking)
                # In production, this would be handled by a Celery task
                try:
                    # Wait for transaction receipt (with timeout)
                    receipt = await self.transaction_service.get_transaction_receipt(
                        chain_id=chain_id,
                        tx_hash=transaction_hash,
                        timeout=300,  # 5 minutes timeout
                    )

                    if receipt:
                        # Update trade with confirmation details
                        from sqlalchemy import update

                        stmt = (
                            update(DEXTrade)
                            .where(DEXTrade.id == trade.id)
                            .values(
                                status=(
                                    "completed" if receipt["status"] == 1 else "failed"
                                ),
                                success=receipt["status"] == 1,
                                transaction_status="confirmed",
                                block_number=receipt["blockNumber"],
                                gas_used=receipt["gasUsed"],
                                confirmed_at=datetime.utcnow(),
                                error_message=(
                                    None
                                    if receipt["status"] == 1
                                    else "Transaction failed"
                                ),
                            )
                        )
                        await db.execute(stmt)
                        await db.commit()

                        logger.info(
                            f"Trade {trade.id} confirmed: {transaction_hash}",
                            extra={
                                "trade_id": trade.id,
                                "tx_hash": transaction_hash,
                                "status": receipt["status"],
                                "block_number": receipt["blockNumber"],
                            },
                        )

                        # Trigger portfolio reconciliation after successful trade
                        if receipt["status"] == 1:  # Only for successful trades
                            try:
                                from ...tasks.portfolio_reconciliation import (
                                    trigger_reconciliation_after_trade,
                                )

                                trigger_reconciliation_after_trade(str(user_id))
                                logger.debug(
                                    f"Triggered portfolio reconciliation for user {user_id} after trade {trade.id}"
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Failed to trigger reconciliation: {e}",
                                    exc_info=True,
                                )

                        # Create or update position tracking
                        try:
                            from ..trading.dex_position_service import (
                                DEXPositionService,
                            )

                            position_service = DEXPositionService(db)

                            # Determine if this trade opens or closes a position
                            # For now, we'll create a position for buy trades
                            # In production, implement proper position matching logic
                            if trade.trade_type == "custodial":
                                # Get buy token info
                                buy_token_symbol = trade.buy_token_symbol or "UNKNOWN"
                                buy_amount_decimal = trade.buy_amount_decimal or 0.0

                                if buy_amount_decimal > 0:
                                    # Open position for bought token
                                    current_price = (
                                        await self.market_data.get_price(
                                            f"{buy_token_symbol}/USD"
                                        )
                                        or 0.0
                                    )

                                    await position_service.open_position(
                                        user_id=trade.user_id,
                                        trade_id=trade.id,
                                        chain_id=trade.chain_id,
                                        token_address=trade.buy_token,
                                        token_symbol=buy_token_symbol,
                                        amount=buy_amount_decimal,
                                        entry_price=current_price,
                                        amount_usd=buy_amount_decimal * current_price,
                                    )
                        except Exception as e:
                            logger.warning(
                                f"Failed to create position tracking: {e}",
                                exc_info=True,
                            )

                        # Update transaction monitoring with confirmation
                        try:
                            from ...services.monitoring.transaction_monitor import (
                                transaction_monitor,
                            )

                            latency = (
                                (datetime.utcnow() - trade.created_at).total_seconds()
                                if trade.created_at
                                else None
                            )
                            await transaction_monitor.update_transaction_status(
                                transaction_hash=transaction_hash,
                                status=(
                                    "confirmed" if receipt["status"] == 1 else "failed"
                                ),
                                gas_used=receipt.get("gasUsed"),
                                block_number=receipt.get("blockNumber"),
                                latency_seconds=latency,
                            )
                        except Exception as e:
                            logger.warning(
                                f"Failed to update transaction monitoring: {e}"
                            )
                    else:
                        # Transaction not confirmed yet, will be checked by background task
                        logger.info(
                            f"Trade {trade.id} transaction sent, waiting for confirmation: {transaction_hash}",
                            extra={"trade_id": trade.id, "tx_hash": transaction_hash},
                        )
                except Exception as e:
                    logger.warning(
                        f"Error waiting for transaction receipt: {e}. Trade will be updated by background task.",
                        extra={"trade_id": trade.id, "tx_hash": transaction_hash},
                    )

            if not trade:
                raise ValueError("Failed to save trade to database")

            # Audit log DEX trade
            try:
                from ..audit.audit_logger import audit_logger

                audit_logger.log_trade(
                    user_id=user_id,
                    trade_id=str(trade.id),
                    chain_id=chain_id,
                    symbol=f"{sell_token_symbol}/{buy_token_symbol}",
                    side="swap",
                    amount=float(sell_amount_decimal),
                    price=(
                        float(buy_amount_decimal) / float(sell_amount_decimal)
                        if sell_amount_decimal > 0
                        else 0
                    ),
                    mode="real",  # Custodial swaps are real money
                    transaction_hash=transaction_hash,
                    bot_id=None,
                    mfa_used=False,  # Would be set if 2FA was required
                    risk_checks_passed=True,
                    success=True,
                )
            except Exception as e:
                logger.warning(f"Failed to audit log DEX trade: {e}")

            # Track transaction for monitoring (custodial swap)
            if transaction_hash:
                try:
                    from ...services.monitoring.transaction_monitor import (
                        transaction_monitor,
                    )

                    await transaction_monitor.track_transaction(
                        transaction_hash=transaction_hash,
                        chain_id=chain_id,
                        transaction_type="swap",
                        user_id=int(user_id),
                        amount=sell_amount_decimal,
                        token_address=(
                            sell_token if sell_token.startswith("0x") else None
                        ),
                        from_address=platform_wallet_address,
                        to_address=None,  # Swap doesn't have direct to_address
                        status="executing",
                    )
                except Exception as e:
                    logger.warning(f"Failed to track transaction for monitoring: {e}")

            # Save trading fee record
            await self._save_trading_fee(
                user_id=user_id,
                dex_trade_id=trade.id,
                fee_type="platform",
                fee_bps=fee_bps,
                fee_amount=float(fee_amount),
                fee_currency=sell_token_symbol,
                trade_amount=float(sell_amount_decimal),
                trade_currency=sell_token_symbol,
                user_tier=user_tier,
                monthly_volume=float(monthly_volume),
                is_custodial=True,
                db=db,
            )

            logger.info(
                f"Custodial swap executed: {sell_token_symbol} -> {buy_token_symbol}",
                extra={
                    "user_id": user_id,
                    "trade_id": trade.id,
                    "sell_amount": sell_amount,
                    "buy_amount": buy_amount,
                    "fee": str(fee_amount),
                    "aggregator": aggregator_name,
                },
            )

            return {
                "success": True,
                "trade_id": trade.id,
                "sell_token": sell_token,
                "sell_token_symbol": sell_token_symbol,
                "buy_token": buy_token,
                "buy_token_symbol": buy_token_symbol,
                "sell_amount": sell_amount,
                "buy_amount": buy_amount,
                "fee_amount": str(fee_amount),
                "aggregator": aggregator_name,
                "transaction_hash": transaction_hash,
                "status": trade.status,
            }

        except Exception as e:
            logger.error(f"Error executing custodial swap: {e}", exc_info=True)
            return None

    async def execute_non_custodial_swap(
        self,
        user_id: int,
        sell_token: str,
        buy_token: str,
        sell_amount: str,
        user_wallet_address: str,  # Required parameter moved before defaults
        chain_id: int = 1,
        slippage_percentage: float = 0.5,
        transaction_hash: str | None = None,
        signature: str | None = None,
        db: AsyncSession = None,
        user_tier: str = "free",
    ) -> dict[str, Any] | None:
        """
        Execute or track a non-custodial swap (user executes from their wallet)

        Args:
            user_id: User ID
            sell_token: Token to sell
            buy_token: Token to buy
            sell_amount: Amount to sell
            chain_id: Blockchain ID
            slippage_percentage: Max slippage
            user_wallet_address: User's wallet address
            transaction_hash: Optional transaction hash if user already executed
            signature: Optional EIP-712 signature for authorization
            db: Database session
            user_tier: User subscription tier for fee calculation

        Returns:
            Trade execution result or None if error
        """
        try:
            if not db:
                raise ValueError("Database session required")

            # Get best quote
            quote = await self.get_quote(
                sell_token=sell_token,
                buy_token=buy_token,
                sell_amount=sell_amount,
                chain_id=chain_id,
                slippage_percentage=slippage_percentage,
                user_wallet_address=user_wallet_address,
            )

            if not quote:
                raise ValueError("Failed to get quote")

            # Get user's monthly volume for fee calculation
            monthly_volume = await self.fee_service.get_user_monthly_volume(
                str(user_id), db
            )

            # Calculate trading fee
            sell_amount_decimal = Decimal(sell_amount)
            fee_amount = self.fee_service.calculate_fee(
                trade_amount=sell_amount_decimal,
                user_tier=user_tier,
                is_custodial=False,
                monthly_volume=monthly_volume,
            )
            fee_bps = int((fee_amount / sell_amount_decimal) * Decimal(10000))

            # Get token symbols
            sell_token_symbol = quote.get("sellTokenSymbol", sell_token[:10])
            buy_token_symbol = quote.get("buyTokenSymbol", buy_token[:10])
            buy_amount = quote.get("buyAmount", "0")
            buy_amount_decimal = float(Decimal(buy_amount) / Decimal(10**18))

            aggregator_name = quote.get("aggregator", "0x")

            # If transaction_hash provided, user already executed - just track it
            if transaction_hash:
                # Verify transaction exists
                tx_status = await self.transaction_service.get_transaction_status(
                    chain_id=chain_id,
                    tx_hash=transaction_hash,
                )

                if not tx_status:
                    raise ValueError("Transaction not found")

                initial_status = (
                    "executing" if tx_status["status"] == "pending" else "completed"
                )

                # Save trade to database
                trade = await self._save_dex_trade(
                    user_id=user_id,
                    trade_type="non_custodial",
                    chain_id=chain_id,
                    aggregator=aggregator_name,
                    sell_token=sell_token,
                    sell_token_symbol=sell_token_symbol,
                    buy_token=buy_token,
                    buy_token_symbol=buy_token_symbol,
                    sell_amount=sell_amount,
                    buy_amount=buy_amount,
                    sell_amount_decimal=float(sell_amount_decimal),
                    buy_amount_decimal=buy_amount_decimal,
                    slippage_percentage=slippage_percentage,
                    platform_fee_bps=fee_bps,
                    platform_fee_amount=float(fee_amount),
                    aggregator_fee_amount=0.0,
                    user_wallet_address=user_wallet_address,
                    quote_data=quote,
                    swap_calldata=None,
                    swap_target=None,
                    transaction_hash=transaction_hash,
                    status=initial_status,
                    db=db,
                )

                if not trade:
                    raise ValueError("Failed to save trade to database")

                # Audit log non-custodial DEX trade
                try:
                    from ...services.audit.audit_logger import audit_logger

                    audit_logger.log_trade(
                        user_id=user_id,
                        trade_id=str(trade.id),
                        chain_id=chain_id,
                        symbol=f"{sell_token_symbol}/{buy_token_symbol}",
                        side="swap",
                        amount=float(sell_amount_decimal),
                        price=(
                            float(buy_amount_decimal) / float(sell_amount_decimal)
                            if sell_amount_decimal > 0
                            else 0
                        ),
                        mode="real",  # Non-custodial swaps are also real money
                        transaction_hash=transaction_hash,
                        bot_id=None,
                        mfa_used=False,
                        risk_checks_passed=True,
                        success=True,
                    )
                except Exception as e:
                    logger.warning(f"Failed to audit log DEX trade: {e}")

                # Track transaction for monitoring (non-custodial swap)
                if transaction_hash:
                    try:
                        from ...services.monitoring.transaction_monitor import (
                            transaction_monitor,
                        )

                        await transaction_monitor.track_transaction(
                            transaction_hash=transaction_hash,
                            chain_id=chain_id,
                            transaction_type="swap",
                            user_id=user_id,
                            amount=sell_amount_decimal,
                            token_address=(
                                sell_token if sell_token.startswith("0x") else None
                            ),
                            from_address=user_wallet_address,
                            to_address=None,
                            status=initial_status,
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to track transaction for monitoring: {e}"
                        )

                # Save trading fee record
                await self._save_trading_fee(
                    user_id=user_id,
                    dex_trade_id=trade.id,
                    fee_type="platform",
                    fee_bps=fee_bps,
                    fee_amount=float(fee_amount),
                    fee_currency=sell_token_symbol,
                    trade_amount=float(sell_amount_decimal),
                    trade_currency=sell_token_symbol,
                    user_tier=user_tier,
                    monthly_volume=float(monthly_volume),
                    is_custodial=False,
                    db=db,
                )

                return {
                    "success": True,
                    "trade_id": trade.id,
                    "sell_token": sell_token,
                    "sell_token_symbol": sell_token_symbol,
                    "buy_token": buy_token,
                    "buy_token_symbol": buy_token_symbol,
                    "sell_amount": sell_amount,
                    "buy_amount": buy_amount,
                    "fee_amount": str(fee_amount),
                    "aggregator": aggregator_name,
                    "transaction_hash": transaction_hash,
                    "status": trade.status,
                }
            else:
                # Prepare swap calldata for user to execute
                return await self.prepare_non_custodial_swap(
                    user_id=str(user_id),
                    sell_token=sell_token,
                    buy_token=buy_token,
                    sell_amount=sell_amount,
                    chain_id=chain_id,
                    slippage_percentage=slippage_percentage,
                    user_wallet_address=user_wallet_address,
                    signature=signature,
                    trading_fee_bps=fee_bps,
                    db=db,
                )

        except Exception as e:
            logger.error(f"Error executing non-custodial swap: {e}", exc_info=True)
            return None

    async def prepare_non_custodial_swap(
        self,
        user_id: str,
        sell_token: str,
        buy_token: str,
        sell_amount: str,
        user_wallet_address: str,
        chain_id: int = 1,
        slippage_percentage: float = 0.5,
        signature: str | None = None,
        trading_fee_bps: int = 15,  # 0.15% for non-custodial
        db: AsyncSession | None = None,
    ) -> dict[str, Any] | None:
        """
        Prepare swap calldata for non-custodial execution (user's wallet)

        Args:
            user_id: User ID
            sell_token: Token to sell
            buy_token: Token to buy
            sell_amount: Amount to sell
            chain_id: Blockchain ID
            slippage_percentage: Max slippage
            user_wallet_address: User's wallet address
            signature: Optional EIP-712 signature for authorization
            trading_fee_bps: Trading fee in basis points (15 = 0.15%)

        Returns:
            Swap calldata for user to execute or None if error
        """
        try:
            # Verify signature if provided
            if signature and db:
                # Create trade message with nonce from database
                nonce = await self.signature_service.generate_nonce(
                    user_id=int(user_id),
                    wallet_address=user_wallet_address,
                    chain_id=chain_id,
                    message_type="trade",
                    db=db,
                )
                trade_message = self.signature_service.create_trade_message(
                    sell_token=sell_token,
                    buy_token=buy_token,
                    sell_amount=sell_amount,
                    buy_amount="0",  # Will be determined by quote
                    chain_id=chain_id,
                    nonce=nonce,
                )

                # Verify signature
                is_valid = self.signature_service.verify_eip712_signature(
                    signature=signature,
                    message=trade_message["message"],
                    domain=trade_message["domain"],
                    signer_address=user_wallet_address,
                )

                if not is_valid:
                    raise ValueError("Invalid signature")

            # Get best quote
            quote = await self.get_quote(
                sell_token=sell_token,
                buy_token=buy_token,
                sell_amount=sell_amount,
                chain_id=chain_id,
                slippage_percentage=slippage_percentage,
                user_wallet_address=user_wallet_address,
            )

            if not quote:
                raise ValueError("Failed to get quote")

            # Calculate trading fee
            sell_amount_decimal = Decimal(sell_amount)
            fee_amount = sell_amount_decimal * Decimal(trading_fee_bps) / Decimal(10000)
            # Note: Fee could be deducted from buy amount instead

            # Get swap calldata
            aggregator_name = quote.get("aggregator", "0x")
            swap_calldata = await self.router.get_swap_calldata(
                aggregator_name=aggregator_name,
                sell_token=sell_token,
                buy_token=buy_token,
                sell_amount=sell_amount,
                chain_id=chain_id,
                slippage_percentage=slippage_percentage,
                taker_address=user_wallet_address,
            )

            if not swap_calldata:
                raise ValueError("Failed to get swap calldata")

            logger.info(
                f"Non-custodial swap prepared: {sell_token} -> {buy_token}",
                extra={
                    "user_id": user_id,
                    "wallet_address": user_wallet_address,
                    "sell_amount": sell_amount,
                    "buy_amount": quote.get("buyAmount"),
                    "fee": str(fee_amount),
                    "aggregator": aggregator_name,
                },
            )

            return {
                "success": True,
                "sell_token": sell_token,
                "buy_token": buy_token,
                "sell_amount": sell_amount,
                "buy_amount": quote.get("buyAmount"),
                "fee_amount": str(fee_amount),
                "aggregator": aggregator_name,
                "swap_calldata": swap_calldata,
                "chain_id": chain_id,
            }

        except Exception as e:
            logger.error(f"Error preparing non-custodial swap: {e}", exc_info=True)
            return None

    async def _execute_swap(
        self,
        chain_id: int,
        wallet_address: str,
        swap_calldata: dict[str, Any] | str,
        swap_target: str | None = None,
    ) -> str | None:
        """
        Execute swap transaction on blockchain

        Args:
            chain_id: Blockchain chain ID
            wallet_address: Wallet address to execute from
            swap_calldata: Swap calldata (dict with 'calldata' and 'to', or hex string)
            swap_target: Target contract address (if calldata is string)

        Returns:
            Transaction hash (hex string) or None if error
        """
        try:
            # Get private key from secure key management
            private_key = await self.key_management.get_private_key(
                wallet_address, chain_id
            )
            if not private_key:
                logger.error(
                    f"Could not retrieve private key for wallet {wallet_address}",
                    extra={"wallet_address": wallet_address, "chain_id": chain_id},
                )
                raise ValueError(
                    "Private key not available. Key management not configured."
                )

            # Parse swap calldata
            if isinstance(swap_calldata, dict):
                calldata_hex = swap_calldata.get("calldata") or swap_calldata.get(
                    "data"
                )
                to_address = swap_calldata.get("to") or swap_target
            else:
                calldata_hex = swap_calldata
                to_address = swap_target

            if not calldata_hex or not to_address:
                raise ValueError(
                    "Invalid swap calldata: missing calldata or target address"
                )

            # Normalize addresses
            to_address = self.web3_service.normalize_address(to_address)
            wallet_address = self.web3_service.normalize_address(wallet_address)

            if not to_address or not wallet_address:
                raise ValueError("Invalid addresses in swap calldata")

            # Get transaction count (nonce)
            nonce = await self.transaction_service.get_transaction_count(
                chain_id, wallet_address
            )
            if nonce is None:
                raise ValueError("Could not get transaction count")

            # Get gas price
            gas_price = await self.transaction_service.get_gas_price(chain_id)
            if gas_price is None:
                raise ValueError("Could not get gas price")

            # Build transaction
            transaction = {
                "from": wallet_address,
                "to": to_address,
                "data": (
                    calldata_hex
                    if calldata_hex.startswith("0x")
                    else "0x" + calldata_hex
                ),
                "value": 0,  # DEX swaps typically don't send ETH (unless swapping ETH)
                "gasPrice": gas_price,
                "nonce": nonce,
                "chainId": chain_id,
            }

            # Estimate gas
            gas = await self.transaction_service.estimate_gas(chain_id, transaction)
            if gas is None:
                raise ValueError("Could not estimate gas")
            # Add 20% gas buffer to prevent transaction failures due to gas estimation inaccuracies
            # This is important because DEX swaps can have variable gas costs depending on route complexity
            transaction["gas"] = int(gas * 1.2)

            # Calculate trade value in USD for MEV protection decision
            trade_amount_usd = None

            try:
                # Get token prices to calculate USD value
                from ..blockchain.token_registry import get_token_registry

                # Get sell token symbol and decimals
                sell_token_symbol = await token_registry.get_token_symbol(
                    sell_token, chain_id
                )
                if sell_token_symbol:
                    # Get price from MarketDataService
                    price = await self.market_data.get_price(f"{sell_token_symbol}/USD")
                    if price:
                        # Get actual token decimals
                        sell_token_decimals = await token_registry.get_token_decimals(
                            sell_token, chain_id
                        )
                        # Calculate USD value using actual decimals
                        sell_amount_float = float(
                            Decimal(sell_amount) / Decimal(10**sell_token_decimals)
                        )
                        trade_amount_usd = sell_amount_float * price
            except Exception as e:
                logger.debug(
                    f"Could not calculate trade USD value for MEV protection: {e}"
                )

            # Sign and send transaction (with optional MEV protection)
            # MEV protection automatically enabled for trades > $1000 USD to protect against
            # front-running and sandwich attacks. The threshold balances security with gas costs.
            tx_hash = await self.transaction_service.sign_and_send_transaction(
                chain_id=chain_id,
                private_key=private_key,
                transaction=transaction,
                use_mev_protection=False,  # Auto-determined based on trade_amount_usd (>$1000)
                trade_amount_usd=trade_amount_usd,
            )

            if not tx_hash:
                raise ValueError("Failed to send transaction")

            logger.info(
                f"Swap transaction sent: {tx_hash}",
                extra={
                    "chain_id": chain_id,
                    "wallet_address": wallet_address,
                    "tx_hash": tx_hash,
                    "trade_amount_usd": trade_amount_usd,
                },
            )

            return tx_hash

        except Exception as e:
            logger.error(f"Error executing swap: {e}", exc_info=True)
            return None

    async def get_swap_status(
        self,
        trade_id: int,
        chain_id: int,
        transaction_hash: str,
        db: AsyncSession,
    ) -> dict[str, Any] | None:
        """
        Get swap transaction status and update trade record

        Args:
            trade_id: DEX trade ID
            chain_id: Blockchain ID
            transaction_hash: Transaction hash
            db: Database session

        Returns:
            Transaction status dictionary or None if error
        """
        try:
            # Get transaction status
            tx_status = await self.transaction_service.get_transaction_status(
                chain_id=chain_id,
                tx_hash=transaction_hash,
            )

            if not tx_status:
                return {
                    "status": "not_found",
                    "message": "Transaction not found",
                }

            # Update trade record if status changed
            from sqlalchemy import select, update

            stmt = select(DEXTrade).where(DEXTrade.id == trade_id)
            result = await db.execute(stmt)
            trade = result.scalar_one_or_none()

            if trade:
                new_status = None
                if tx_status["status"] == "confirmed":
                    new_status = "completed" if tx_status["success"] else "failed"
                elif tx_status["status"] == "pending":
                    new_status = "executing"

                if new_status and new_status != trade.status:
                    update_stmt = (
                        update(DEXTrade)
                        .where(DEXTrade.id == trade_id)
                        .values(
                            status=new_status,
                            success=tx_status.get("success"),
                            block_number=tx_status.get("blockNumber"),
                            gas_used=tx_status.get("gasUsed"),
                            confirmed_at=(
                                datetime.utcnow()
                                if tx_status["status"] == "confirmed"
                                else None
                            ),
                        )
                    )
                    await db.execute(update_stmt)
                    await db.commit()

                    # Update transaction monitoring
                    try:
                        from ...services.monitoring.transaction_monitor import (
                            transaction_monitor,
                        )

                        # Calculate latency if we have timestamps
                        latency = None
                        if trade.created_at and tx_status["status"] == "confirmed":
                            latency = (
                                datetime.utcnow() - trade.created_at
                            ).total_seconds()

                        await transaction_monitor.update_transaction_status(
                            transaction_hash=transaction_hash,
                            status=(
                                "confirmed"
                                if tx_status["status"] == "confirmed"
                                else "failed"
                            ),
                            gas_used=tx_status.get("gasUsed"),
                            block_number=tx_status.get("blockNumber"),
                            latency_seconds=latency,
                        )
                    except Exception as e:
                        logger.warning(f"Failed to update transaction monitoring: {e}")

            return {
                "status": tx_status["status"],
                "success": tx_status.get("success"),
                "block_number": tx_status.get("blockNumber"),
                "gas_used": tx_status.get("gasUsed"),
                "trade_id": trade_id,
                "transaction_hash": transaction_hash,
            }

        except Exception as e:
            logger.error(f"Error getting swap status: {e}", exc_info=True)
            return None

    async def get_supported_chains(self) -> list[dict[str, Any]]:
        """
        Get list of supported blockchain networks

        Returns:
            List of supported chains
        """
        try:
            # Get chains from all aggregators and merge
            zeroex_chains = await self.router.zeroex.get_supported_chains()
            okx_chains = await self.router.okx.get_supported_chains()
            rubic_chains = await self.router.rubic.get_supported_chains()

            # Merge and deduplicate by chainId
            chains_dict = {}
            for chain in zeroex_chains + okx_chains + rubic_chains:
                chain_id = chain.get("chainId")
                if chain_id and chain_id not in chains_dict:
                    chains_dict[chain_id] = chain

            return list(chains_dict.values())
        except Exception as e:
            logger.error(f"Error getting supported chains: {e}", exc_info=True)
            # Return default chains if aggregators fail
            return [
                {"chainId": 1, "name": "Ethereum", "symbol": "ETH"},
                {"chainId": 8453, "name": "Base", "symbol": "ETH"},
                {"chainId": 42161, "name": "Arbitrum One", "symbol": "ETH"},
                {"chainId": 137, "name": "Polygon", "symbol": "MATIC"},
            ]
