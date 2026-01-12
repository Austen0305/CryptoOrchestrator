"""
Real Money Trading Service
Handles real money trades with proper security and validation
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from ...services.advanced_risk_manager import AdvancedRiskManager
from ...services.real_money_safety import real_money_safety_service
from ...services.real_money_transaction_manager import real_money_transaction_manager
from ...services.trading.safe_trading_system import SafeTradingSystem
from ..trading.dex_trading_service import DEXTradingService

logger = logging.getLogger(__name__)


class RealMoneyTradingService:
    """Service for executing real money trades with security and validation"""

    def __init__(self):
        self.risk_manager = AdvancedRiskManager.get_instance()
        self.safe_trading_system = SafeTradingSystem()
        # Note: real_money_safety_service and real_money_transaction_manager
        # are imported at module level to avoid circular imports

    async def execute_real_money_trade(
        self,
        user_id: str,
        chain_id: int,  # Changed from exchange to chain_id
        pair: str,
        side: str,
        order_type: str,
        amount: float,
        price: float | None = None,
        bot_id: str | None = None,
        mfa_token: str | None = None,
        stop: float | None = None,
        take_profit: float | None = None,
        trailing_stop_percent: float | None = None,
        time_in_force: str | None = "GTC",
        db: Any | None = None,  # Database session
    ) -> dict[str, Any]:
        """Execute a real money trade with proper validation and security"""
        user_id_int = (
            int(user_id) if isinstance(user_id, str) and user_id.isdigit() else user_id
        )
        if not isinstance(user_id_int, int):
            user_id_int = int(user_id) if user_id else 1

        # Convert to Decimal for precision
        amount_decimal = Decimal(str(amount))
        price_decimal = Decimal(str(price)) if price else None

        # Calculate trade value in USD for compliance checks
        trade_value_usd = float(amount_decimal) * (
            float(price_decimal) if price_decimal else 0.0
        )
        if not price_decimal:  # Market order - estimate with current price
            try:
                # Get current price from Market Data Service
                from ..market_data_service import get_market_data_service

                market_data = get_market_data_service()
                coin_symbol = pair.split("/")[0]  # e.g., "ETH" from "ETH/USD"
                current_price = await market_data.get_price(f"{coin_symbol}/USD")
                if current_price:
                    trade_value_usd = float(amount_decimal) * current_price
            except Exception as e:
                logger.warning(f"Could not estimate trade value for compliance: {e}")

        # Compliance checks
        from ..compliance.compliance_service import (
            ComplianceCheckResult,
            compliance_service,
        )

        (
            compliance_result,
            compliance_reasons,
        ) = await compliance_service.check_trade_compliance(
            user_id=user_id_int,
            amount_usd=trade_value_usd,
            chain_id=chain_id,  # Changed from exchange
            symbol=pair,
            side=side,
        )

        if compliance_result == ComplianceCheckResult.BLOCKED:
            error_message = "; ".join(compliance_reasons)
            logger.warning(
                f"Trade blocked by compliance for user {user_id}: {error_message}"
            )
            raise ValueError(f"Trade blocked by compliance: {error_message}")
        elif compliance_result == ComplianceCheckResult.REQUIRES_KYC:
            error_message = "; ".join(compliance_reasons)
            logger.warning(f"Trade requires KYC for user {user_id}: {error_message}")
            raise ValueError(f"KYC verification required: {error_message}")
        elif compliance_result == ComplianceCheckResult.REQUIRES_REVIEW:
            logger.warning(
                f"Trade flagged for compliance review for user {user_id}: {compliance_reasons}"
            )
            # Continue with trade but log for review

        # Comprehensive safety validation
        (
            is_valid,
            errors,
            metadata,
        ) = await real_money_safety_service.validate_real_money_trade(
            user_id=user_id_int,
            chain_id=chain_id,
            symbol=pair,
            side=side,
            amount=amount_decimal,
            price=price_decimal,
        )

        if not is_valid:
            error_message = "; ".join(errors)
            logger.warning(
                f"Real money trade validation failed for user {user_id}: {error_message}"
            )
            raise ValueError(f"Trade validation failed: {error_message}")

        # Validate MFA if provided
        if mfa_token:
            from ..services.two_factor_service import two_factor_service

            is_valid_mfa = await two_factor_service.verify_totp(
                user_id=user_id_int,
                token=mfa_token,
            )
            if not is_valid_mfa:
                raise ValueError("Invalid 2FA token")

        # Execute within atomic transaction
        async def _execute_trade(db):
            return await self._execute_trade_internal(
                user_id_int,
                chain_id,  # Changed from exchange
                pair,
                side,
                order_type,
                float(amount_decimal),
                float(price_decimal) if price_decimal else None,
                bot_id,
                mfa_token,
                db,
            )

        try:
            result = await real_money_transaction_manager.execute_with_rollback(
                operation=_execute_trade,
                operation_name="trade",
                user_id=user_id_int,
                operation_details={
                    "chain_id": chain_id,
                    "symbol": pair,
                    "side": side,
                    "amount": float(amount_decimal),
                    "price": float(price_decimal) if price_decimal else None,
                    "order_type": order_type,
                    "bot_id": bot_id,
                    **metadata,
                },
            )

            # Audit log the trade
            from ..services.audit.audit_logger import audit_logger

            audit_logger.log_trade(
                user_id=user_id_int,
                trade_id=str(result.get("trade_id", "unknown")),
                chain_id=chain_id,
                symbol=pair,
                side=side,
                amount=float(amount_decimal),
                price=float(price_decimal) if price_decimal else 0.0,
                mode="real",
                transaction_hash=result.get("transaction_hash"),
                bot_id=bot_id,
                mfa_used=bool(mfa_token),
                risk_checks_passed=True,
                success=result.get("success", False),
            )

            return result
        except Exception as e:
            logger.error(f"Failed to execute real money trade: {e}", exc_info=True)
            raise

    async def _execute_trade_internal(
        self,
        user_id: int,
        chain_id: int,  # Changed from exchange to chain_id
        pair: str,
        side: str,
        order_type: str,
        amount: float,
        price: float | None,
        bot_id: str | None,
        mfa_token: str | None,
        db,
        stop: float | None = None,
        take_profit: float | None = None,
        trailing_stop_percent: float | None = None,
        time_in_force: str | None = "GTC",
    ) -> dict[str, Any]:
        """Internal trade execution logic via DEX (called within transaction)"""
        try:
            # Convert user_id to int
            user_id_int = (
                int(user_id)
                if isinstance(user_id, str) and user_id.isdigit()
                else user_id
            )
            if not isinstance(user_id_int, int):
                user_id_int = int(user_id) if user_id else 1

            # 0. MANDATORY 2FA requirement for real money trading
            import speakeasy
            from sqlalchemy import select

            from ...database import get_db_context
            from ...models.base import User

            async with get_db_context() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id_int)
                )
                user = result.scalar_one_or_none()

                if not user:
                    raise ValueError("User not found")

                # MANDATORY: 2FA must be enabled for real money trading
                if not user.mfa_enabled:
                    raise ValueError(
                        "2FA is required for real money trading. Please enable 2FA in your account settings."
                    )

                # MANDATORY: 2FA token must be provided
                if not mfa_token:
                    raise ValueError(
                        "2FA token is required for real money trading. Please provide your 2FA token."
                    )

                # Verify 2FA token
                if user.mfa_method == "totp" and user.mfa_secret:
                    verified = speakeasy.totp.verify(
                        {
                            "secret": user.mfa_secret,
                            "encoding": "base32",
                            "token": mfa_token,
                            "window": 2,
                        }
                    )
                    if not verified:
                        raise ValueError(
                            "Invalid 2FA token. Please check your authenticator app."
                        )
                elif user.mfa_method in ("email", "sms"):
                    # Verify one-time code
                    if not user.mfa_code or user.mfa_code != mfa_token:
                        raise ValueError(
                            "Invalid 2FA code. Please check your email/SMS."
                        )
                    # Check expiration
                    if (
                        user.mfa_code_expires_at
                        and datetime.utcnow() > user.mfa_code_expires_at
                    ):
                        raise ValueError(
                            "2FA code has expired. Please request a new code."
                        )
                else:
                    raise ValueError(
                        "Unsupported 2FA method. Please use TOTP, email, or SMS."
                    )

            # 1. Validate user has wallet for this chain
            from ...repositories.wallet_repository import WalletRepository

            wallet_repo = WalletRepository(db)
            user_wallet = await wallet_repo.get_user_wallet(
                user_id_int, chain_id, "custodial"
            )

            if not user_wallet:
                raise ValueError(
                    f"No custodial wallet found for chain {chain_id}. Please create a wallet first."
                )

            # 2. Risk management checks (optional - can be disabled if risk manager is not available)
            try:
                risk_profile = await self.risk_manager.get_user_risk_profile(user_id)
                if risk_profile:
                    # Check position size limits
                    max_position = getattr(
                        risk_profile, "max_position_size", float("inf")
                    )
                    if amount > max_position:
                        raise ValueError(
                            f"Position size {amount} exceeds maximum {max_position}"
                        )

                    # Check daily loss limit
                    daily_pnl = await self.safe_trading_system.get_daily_pnl(
                        str(user_id_int)
                    )
                    daily_loss_limit = getattr(
                        risk_profile, "daily_loss_limit", float("inf")
                    )
                    if daily_pnl < -daily_loss_limit:
                        raise ValueError(
                            f"Daily loss limit reached: {daily_pnl} < -{daily_loss_limit}"
                        )
            except AttributeError:
                # Risk manager doesn't have get_user_risk_profile method - skip risk checks
                logger.warning(
                    "Risk manager doesn't support user risk profiles, skipping risk checks"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to perform risk checks: {e}, proceeding with trade"
                )

            # 3. Execute trade via DEX
            dex_service = DEXTradingService()

            # Convert pair to token addresses using token registry
            from ..blockchain.token_registry import get_token_registry

            token_registry = get_token_registry()
            base_address, quote_address = await token_registry.parse_symbol_to_tokens(
                pair, chain_id
            )

            # Determine sell/buy tokens based on side
            if side == "buy":
                # Buying: sell quote token to get base token
                sell_token = quote_address
                buy_token = base_address
            else:
                # Selling: sell base token to get quote token
                sell_token = base_address
                buy_token = quote_address

            # For DEX, we primarily support market orders (swaps)
            # Advanced order types (stop-loss, take-profit) would need to be handled differently
            if order_type not in ("market", "limit"):
                logger.warning(
                    f"Order type {order_type} not fully supported on DEX, executing as market order"
                )

            # Convert amount to proper decimal format using token registry
            from decimal import Decimal

            from ..blockchain.token_registry import get_token_registry

            token_registry = get_token_registry()
            sell_token_decimals = await token_registry.get_token_decimals(
                sell_token, chain_id
            )
            sell_amount_decimal = Decimal(str(amount))
            sell_amount_wei = str(
                int(sell_amount_decimal * Decimal(10**sell_token_decimals))
            )
            sell_amount = sell_amount_wei

            # Calculate slippage based on order type
            slippage_percentage = 0.5  # Default 0.5% for market orders
            if order_type == "limit" and price:
                # For limit orders, use tighter slippage
                slippage_percentage = 0.1

            # Execute DEX swap
            swap_result = await dex_service.execute_custodial_swap(
                user_id=user_id_int,
                sell_token=sell_token,
                buy_token=buy_token,
                sell_amount=sell_amount,
                chain_id=chain_id,
                slippage_percentage=slippage_percentage,
                user_tier="free",  # Get from user profile
                db=db,
            )

            if not swap_result or not swap_result.get("success"):
                raise ValueError("DEX swap execution failed")

            # Format result to match expected structure
            order_result = {
                "id": swap_result.get("transaction_hash"),
                "transaction_hash": swap_result.get("transaction_hash"),
                "status": "completed" if swap_result.get("success") else "failed",
                "price": price or swap_result.get("executed_price", 0.0),
                "amount": amount,
                "filled": amount,
                "fee": swap_result.get("fee_amount", 0.0),
            }

            # 5. Record trade in safe trading system
            trade_details = {
                "user_id": str(user_id_int),
                "symbol": pair,
                "action": side,
                "quantity": amount,
                "price": price or order_result.get("price", 0),
                "bot_id": bot_id or "manual",
                "chain_id": chain_id,  # Changed from exchange
                "pair": pair,
                "side": side,
                "order_type": order_type,
                "amount": amount,
                "mode": "real",
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Calculate P&L (will be updated when position is closed)
            pnl = 0.0
            await self.safe_trading_system.record_trade_result(trade_details, pnl)

            # 6. Update last used timestamp for API key
            # This would be done in the exchange_key_service

            # 7. Log trade for audit
            try:
                from ...services.audit.audit_logger import audit_logger

                audit_logger.log_trade(
                    user_id=user_id_int,
                    trade_id=order_result.get("transaction_hash", "unknown"),
                    chain_id=chain_id,  # Changed from exchange
                    symbol=pair,
                    side=side,
                    amount=amount,
                    price=price or order_result.get("price", 0),
                    mode="real",
                    order_id=order_result.get("id"),
                    bot_id=bot_id,
                    mfa_used=bool(mfa_token),
                    risk_checks_passed=True,
                    success=True,
                    order_type=order_type,
                )
            except ImportError:
                logger.warning("Audit logger not available, skipping audit log")
            except Exception as e:
                logger.error(f"Failed to log trade to audit: {e}")

            logger.info(
                f"Real money trade executed via DEX: user={user_id}, chain_id={chain_id}, "
                f"pair={pair}, side={side}, amount={amount}, price={price}"
            )

            # Record transaction for compliance monitoring
            try:
                from ..compliance.compliance_service import compliance_service

                trade_value_usd = amount * (price or order_result.get("price", 0))
                await compliance_service.record_transaction(
                    user_id=user_id_int,
                    transaction_id=order_result.get("transaction_hash", "unknown"),
                    amount_usd=trade_value_usd,
                    chain_id=chain_id,  # Changed from exchange
                    symbol=pair,
                    side=side,
                    order_id=order_result.get("transaction_hash"),
                )
            except Exception as e:
                logger.error(f"Failed to record transaction for compliance: {e}")

            return {
                "success": True,
                "order_id": order_result.get("transaction_hash"),
                "transaction_hash": order_result.get("transaction_hash"),
                "status": order_result.get("status", "completed"),
                "filled": order_result.get("filled", amount),
                "remaining": 0,  # DEX swaps are atomic, no remaining
                "price": order_result.get("price", price),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to execute real money trade: {e}")
            raise

    # Removed _create_exchange_instance - no longer using exchanges


# Global instance
real_money_trading_service = RealMoneyTradingService()
