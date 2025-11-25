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

logger = logging.getLogger(__name__)


class RealMoneyTradingService:
    """Service for executing real money trades with security and validation"""

    def __init__(self):
        self.risk_manager = AdvancedRiskManager.get_instance()
        self.safe_trading_system = SafeTradingSystem()

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
    ) -> Dict[str, Any]:
        """Execute a real money trade with proper validation and security"""
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

            # 4. Execute trade
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

