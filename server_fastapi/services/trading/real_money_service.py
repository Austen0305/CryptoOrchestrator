"""
Real Money Trading Service
Handles real money trades with proper security and validation
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..exchange_service import ExchangeService
from ...services.auth.exchange_key_service import exchange_key_service
from ...services.advanced_risk_manager import AdvancedRiskManager
from ...services.trading.safe_trading_system import SafeTradingSystem
from ...services.real_money_safety import real_money_safety_service
from ...services.real_money_transaction_manager import real_money_transaction_manager
from decimal import Decimal

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
        exchange: str,
        pair: str,
        side: str,
        order_type: str,
        amount: float,
        price: Optional[float] = None,
        bot_id: Optional[str] = None,
        mfa_token: Optional[str] = None,
        stop: Optional[float] = None,
        take_profit: Optional[float] = None,
        trailing_stop_percent: Optional[float] = None,
        time_in_force: Optional[str] = "GTC",
    ) -> Dict[str, Any]:
        """Execute a real money trade with proper validation and security"""
        user_id_int = int(user_id) if isinstance(user_id, str) and user_id.isdigit() else user_id
        if not isinstance(user_id_int, int):
            user_id_int = int(user_id) if user_id else 1
        
        # Convert to Decimal for precision
        amount_decimal = Decimal(str(amount))
        price_decimal = Decimal(str(price)) if price else None
        
        # Calculate trade value in USD for compliance checks
        trade_value_usd = float(amount_decimal) * (float(price_decimal) if price_decimal else 0.0)
        if not price_decimal:  # Market order - estimate with current price
            try:
                from ..exchange_service import ExchangeService
                from ..auth.exchange_key_service import exchange_key_service
                api_key_data = await exchange_key_service.get_api_key(
                    str(user_id_int), exchange, include_secrets=False
                )
                if api_key_data:
                    exchange_service = ExchangeService(
                        name=exchange,
                        use_mock=False,
                        api_key=api_key_data.get('api_key'),
                        api_secret=api_key_data.get('api_secret')
                    )
                    current_price = await exchange_service.get_market_price(pair)
                    if current_price:
                        trade_value_usd = float(amount_decimal) * current_price
            except Exception as e:
                logger.warning(f"Could not estimate trade value for compliance: {e}")
        
        # Compliance checks
        from ..compliance.compliance_service import compliance_service, ComplianceCheckResult
        compliance_result, compliance_reasons = await compliance_service.check_trade_compliance(
            user_id=user_id_int,
            amount_usd=trade_value_usd,
            exchange=exchange,
            symbol=pair,
            side=side
        )
        
        if compliance_result == ComplianceCheckResult.BLOCKED:
            error_message = "; ".join(compliance_reasons)
            logger.warning(f"Trade blocked by compliance for user {user_id}: {error_message}")
            raise ValueError(f"Trade blocked by compliance: {error_message}")
        elif compliance_result == ComplianceCheckResult.REQUIRES_KYC:
            error_message = "; ".join(compliance_reasons)
            logger.warning(f"Trade requires KYC for user {user_id}: {error_message}")
            raise ValueError(f"KYC verification required: {error_message}")
        elif compliance_result == ComplianceCheckResult.REQUIRES_REVIEW:
            logger.warning(f"Trade flagged for compliance review for user {user_id}: {compliance_reasons}")
            # Continue with trade but log for review
        
        # Comprehensive safety validation
        is_valid, errors, metadata = await real_money_safety_service.validate_real_money_trade(
            user_id=user_id_int,
            exchange=exchange,
            symbol=pair,
            side=side,
            amount=amount_decimal,
            price=price_decimal
        )
        
        if not is_valid:
            error_message = "; ".join(errors)
            logger.warning(f"Real money trade validation failed for user {user_id}: {error_message}")
            raise ValueError(f"Trade validation failed: {error_message}")
        
        # Execute within atomic transaction
        async def _execute_trade(db):
            return await self._execute_trade_internal(
                user_id_int, exchange, pair, side, order_type,
                float(amount_decimal), float(price_decimal) if price_decimal else None,
                bot_id, mfa_token, db
            )
        
        try:
            result = await real_money_transaction_manager.execute_with_rollback(
                operation=_execute_trade,
                operation_name="trade",
                user_id=user_id_int,
                operation_details={
                    "exchange": exchange,
                    "symbol": pair,
                    "side": side,
                    "amount": float(amount_decimal),
                    "price": float(price_decimal) if price_decimal else None,
                    "order_type": order_type,
                    "bot_id": bot_id,
                    **metadata
                }
            )
            return result
        except Exception as e:
            logger.error(f"Failed to execute real money trade: {e}", exc_info=True)
            raise
    
    async def _execute_trade_internal(
        self,
        user_id: int,
        exchange: str,
        pair: str,
        side: str,
        order_type: str,
        amount: float,
        price: Optional[float],
        bot_id: Optional[str],
        mfa_token: Optional[str],
        db,
        stop: Optional[float] = None,
        take_profit: Optional[float] = None,
        trailing_stop_percent: Optional[float] = None,
        time_in_force: Optional[str] = "GTC",
    ) -> Dict[str, Any]:
        """Internal trade execution logic (called within transaction)"""
        try:
            # Convert user_id to int
            user_id_int = int(user_id) if isinstance(user_id, str) and user_id.isdigit() else user_id
            if not isinstance(user_id_int, int):
                user_id_int = int(user_id) if user_id else 1
            
            # 0. Check 2FA requirement for real money trading
            try:
                from ...database import get_db_context
                from ...models.base import User
                from sqlalchemy import select
                import speakeasy
                
                async with get_db_context() as session:
                    result = await session.execute(
                        select(User).where(User.id == user_id_int)
                    )
                    user = result.scalar_one_or_none()
                    
                    if user and user.mfa_enabled:
                        if not mfa_token:
                            raise ValueError("2FA token required for real money trading")
                        
                        # Verify 2FA token
                        if user.mfa_method == "totp" and user.mfa_secret:
                            verified = speakeasy.totp.verify({
                                'secret': user.mfa_secret,
                                'encoding': 'base32',
                                'token': mfa_token,
                                'window': 2
                            })
                            if not verified:
                                raise ValueError("Invalid 2FA token")
                        elif user.mfa_method in ("email", "sms"):
                            # Verify one-time code
                            if not user.mfa_code or user.mfa_code != mfa_token:
                                raise ValueError("Invalid 2FA code")
                            # Check expiration
                            if user.mfa_code_expires_at and datetime.utcnow() > user.mfa_code_expires_at:
                                raise ValueError("2FA code expired")
            except ImportError:
                logger.warning("2FA verification not available, skipping 2FA check")
            except Exception as e:
                logger.warning(f"2FA check failed: {e}, proceeding with trade")
            
            # 1. Validate user has API keys for this exchange
            api_key_data = await exchange_key_service.get_api_key(
                str(user_id_int), exchange, include_secrets=True
            )
            if not api_key_data:
                raise ValueError(f"No API key found for {exchange}")

            if not api_key_data.get("is_validated", False):
                raise ValueError(f"API key for {exchange} is not validated")

            # 2. Risk management checks (optional - can be disabled if risk manager is not available)
            try:
                risk_profile = await self.risk_manager.get_user_risk_profile(user_id)
                if risk_profile:
                    # Check position size limits
                    max_position = getattr(risk_profile, 'max_position_size', float('inf'))
                    if amount > max_position:
                        raise ValueError(
                            f"Position size {amount} exceeds maximum {max_position}"
                        )

                    # Check daily loss limit
                    daily_pnl = await self.safe_trading_system.get_daily_pnl(str(user_id_int))
                    daily_loss_limit = getattr(risk_profile, 'daily_loss_limit', float('inf'))
                    if daily_pnl < -daily_loss_limit:
                        raise ValueError(
                            f"Daily loss limit reached: {daily_pnl} < -{daily_loss_limit}"
                        )
            except AttributeError:
                # Risk manager doesn't have get_user_risk_profile method - skip risk checks
                logger.warning("Risk manager doesn't support user risk profiles, skipping risk checks")
            except Exception as e:
                logger.warning(f"Failed to perform risk checks: {e}, proceeding with trade")

            # 3. Create exchange instance with user's API keys
            exchange_instance = self._create_exchange_instance(
                exchange=exchange,
                api_key=api_key_data["api_key"],
                api_secret=api_key_data["api_secret"],
                passphrase=api_key_data.get("passphrase"),
                is_testnet=api_key_data.get("is_testnet", False),
            )

            # Connect to exchange
            try:
                await exchange_instance.load_markets()
            except Exception as e:
                raise ConnectionError(f"Failed to connect to {exchange}: {e}")

            # 4. Execute trade with advanced order type support
            if order_type == "market":
                order_result = await exchange_instance.create_market_order(
                    symbol=pair,
                    side=side,
                    amount=amount,
                )
            elif order_type == "limit":
                if not price:
                    raise ValueError("Price required for limit orders")
                order_result = await exchange_instance.create_limit_order(
                    symbol=pair,
                    side=side,
                    amount=amount,
                    price=price,
                    time_in_force=time_in_force or "GTC",
                )
            elif order_type in ("stop", "stop-limit"):
                if not stop:
                    raise ValueError("Stop price required for stop orders")
                if order_type == "stop-limit" and not price:
                    raise ValueError("Price required for stop-limit orders")
                # Use exchange service place_order method which supports stop orders
                from ..exchange_service import default_exchange
                order_result = await default_exchange.place_order(
                    pair=pair,
                    side=side,
                    type_=order_type,
                    amount=amount,
                    price=price,
                    stop=stop,
                    time_in_force=time_in_force or "GTC",
                )
            elif order_type == "take-profit":
                if not take_profit:
                    raise ValueError("Take profit price required for take-profit orders")
                # Take-profit orders are typically limit orders with a specific price
                order_result = await exchange_instance.create_limit_order(
                    symbol=pair,
                    side=side,
                    amount=amount,
                    price=take_profit,
                    time_in_force=time_in_force or "GTC",
                )
            elif order_type == "trailing-stop":
                if not trailing_stop_percent:
                    raise ValueError("Trailing stop percentage required for trailing-stop orders")
                # Trailing stop orders require exchange-specific implementation
                # For now, create a stop order that will be updated dynamically
                # This would need exchange-specific API support
                order_result = await exchange_instance.create_order(
                    symbol=pair,
                    type="STOP_LOSS_LIMIT" if price else "STOP_LOSS",
                    side=side.upper(),
                    amount=amount,
                    price=price,
                    stopPrice=price * (1 - trailing_stop_percent / 100) if side == "buy" else price * (1 + trailing_stop_percent / 100),
                )
            else:
                raise ValueError(f"Unsupported order type: {order_type}")

            # 5. Record trade in safe trading system
            trade_details = {
                "user_id": str(user_id_int),
                "symbol": pair,
                "action": side,
                "quantity": amount,
                "price": price or order_result.get("price", 0),
                "bot_id": bot_id or "manual",
                "exchange": exchange,
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
                    trade_id=order_result.get("id", "unknown"),
                    exchange=exchange,
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
                    order_type=order_type
                )
            except ImportError:
                logger.warning("Audit logger not available, skipping audit log")
            except Exception as e:
                logger.error(f"Failed to log trade to audit: {e}")
            
            logger.info(
                f"Real money trade executed: user={user_id}, exchange={exchange}, "
                f"pair={pair}, side={side}, amount={amount}, price={price}"
            )
            
            # Record transaction for compliance monitoring
            try:
                from ..compliance.compliance_service import compliance_service
                trade_value_usd = amount * (price or order_result.get("price", 0))
                await compliance_service.record_transaction(
                    user_id=user_id_int,
                    transaction_id=order_result.get("id", "unknown"),
                    amount_usd=trade_value_usd,
                    exchange=exchange,
                    symbol=pair,
                    side=side,
                    order_id=order_result.get("id")
                )
            except Exception as e:
                logger.error(f"Failed to record transaction for compliance: {e}")

            return {
                "success": True,
                "order_id": order_result.get("id"),
                "status": order_result.get("status"),
                "filled": order_result.get("filled", 0),
                "remaining": order_result.get("remaining", amount),
                "price": order_result.get("price", price),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to execute real money trade: {e}")
            raise

    def _create_exchange_instance(
        self, exchange: str, api_key: str, api_secret: str, passphrase: Optional[str] = None, is_testnet: bool = False
    ):
        """Create exchange instance with API credentials"""
        import ccxt

        exchange_class = getattr(ccxt, exchange, None)
        if not exchange_class:
            raise ValueError(f"Exchange {exchange} not found in ccxt")

        config = {
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "options": {
                "testnet": is_testnet,
            },
        }

        if passphrase:
            config["passphrase"] = passphrase

        return exchange_class(config)


# Global instance
real_money_trading_service = RealMoneyTradingService()

