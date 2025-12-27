"""
Real Money Safety Service
Comprehensive safety checks and validations for all real money operations
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from decimal import Decimal

from ..models.base import User
from ..models.trade import Trade
from ..models.wallet import Wallet, WalletTransaction
from ..database import get_db_context

logger = logging.getLogger(__name__)


class RealMoneySafetyService:
    """Comprehensive safety service for real money operations"""

    def __init__(self):
        self.min_trade_amount = Decimal("0.01")  # Minimum trade amount
        self.max_trade_amount = Decimal("1000000")  # Maximum trade amount per trade
        self.max_daily_volume = Decimal("10000000")  # Maximum daily volume per user
        self.max_hourly_trades = 100  # Maximum trades per hour
        self.cooldown_after_failed_trade = timedelta(
            minutes=5
        )  # Cooldown after failed trade

    async def validate_real_money_trade(
        self,
        user_id: int,
        exchange: str,
        symbol: str,
        side: str,
        amount: Decimal,
        price: Optional[Decimal] = None,
        db: Optional[AsyncSession] = None,
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Comprehensive validation for real money trades

        Returns:
            (is_valid, errors, metadata)
        """
        errors = []
        metadata = {}

        try:
            # Use provided session or create new one
            if db is None:
                async with get_db_context() as session:
                    return await self._validate_trade_internal(
                        user_id,
                        exchange,
                        symbol,
                        side,
                        amount,
                        price,
                        session,
                        errors,
                        metadata,
                    )
            else:
                return await self._validate_trade_internal(
                    user_id, exchange, symbol, side, amount, price, db, errors, metadata
                )
        except Exception as e:
            logger.error(f"Error validating real money trade: {e}", exc_info=True)
            errors.append(f"Validation error: {str(e)}")
            return False, errors, metadata

    async def _validate_trade_internal(
        self,
        user_id: int,
        exchange: str,
        symbol: str,
        side: str,
        amount: Decimal,
        price: Optional[Decimal],
        db: AsyncSession,
        errors: List[str],
        metadata: Dict[str, Any],
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Internal validation logic"""

        # 1. Validate user exists and is active
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        if not user:
            errors.append("User not found")
            return False, errors, metadata

        if not user.is_active:
            errors.append("User account is not active")
            return False, errors, metadata

        metadata["user_verified"] = True

        # 2. Validate amount
        if amount < self.min_trade_amount:
            errors.append(
                f"Trade amount {amount} is below minimum {self.min_trade_amount}"
            )

        if amount > self.max_trade_amount:
            errors.append(
                f"Trade amount {amount} exceeds maximum {self.max_trade_amount}"
            )

        # 3. Validate price (if provided)
        if price is not None:
            if price <= 0:
                errors.append("Price must be positive")
            elif price > Decimal("1000000000"):  # $1B max price
                errors.append("Price exceeds maximum allowed")

        # 4. Validate symbol format
        if not symbol or len(symbol) > 50:
            errors.append("Invalid symbol format")

        # 5. Validate side
        if side not in ["buy", "sell"]:
            errors.append(f"Invalid side: {side}. Must be 'buy' or 'sell'")

        # 6. Check daily volume limit
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        volume_result = await db.execute(
            select(func.sum(Trade.cost)).where(
                Trade.user_id == user_id,
                Trade.mode == "real",
                Trade.executed_at >= today_start,
                Trade.success == True,
            )
        )
        daily_volume = volume_result.scalar() or Decimal("0")

        trade_value = amount * (price or Decimal("0"))
        if daily_volume + trade_value > self.max_daily_volume:
            errors.append(
                f"Daily volume limit exceeded: {daily_volume + trade_value} > {self.max_daily_volume}"
            )

        metadata["daily_volume"] = float(daily_volume)
        metadata["trade_value"] = float(trade_value)

        # 7. Check hourly trade count
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        count_result = await db.execute(
            select(func.count(Trade.id)).where(
                Trade.user_id == user_id,
                Trade.mode == "real",
                Trade.executed_at >= one_hour_ago,
            )
        )
        hourly_trades = count_result.scalar() or 0

        if hourly_trades >= self.max_hourly_trades:
            errors.append(
                f"Hourly trade limit exceeded: {hourly_trades} >= {self.max_hourly_trades}"
            )

        metadata["hourly_trades"] = hourly_trades

        # 8. Check for recent failed trades (cooldown)
        cooldown_start = datetime.utcnow() - self.cooldown_after_failed_trade
        failed_result = await db.execute(
            select(func.count(Trade.id)).where(
                Trade.user_id == user_id,
                Trade.mode == "real",
                Trade.success == False,
                Trade.executed_at >= cooldown_start,
            )
        )
        recent_failures = failed_result.scalar() or 0

        if recent_failures >= 3:  # 3 failed trades in cooldown period
            errors.append(
                "Too many recent failed trades. Please wait before trading again."
            )

        metadata["recent_failures"] = recent_failures

        # 9. Check wallet balance for buy orders
        if side == "buy":
            wallet_result = await db.execute(
                select(Wallet).where(
                    Wallet.user_id == user_id,
                    Wallet.currency == "USD",
                    Wallet.is_active == True,
                )
            )
            wallet = wallet_result.scalar_one_or_none()

            if wallet:
                required_balance = trade_value * Decimal(
                    "1.01"
                )  # Add 1% buffer for fees
                if wallet.available_balance < required_balance:
                    errors.append(
                        f"Insufficient balance: {wallet.available_balance} < {required_balance}"
                    )
                metadata["wallet_balance"] = float(wallet.available_balance)
                metadata["required_balance"] = float(required_balance)
            else:
                errors.append("No active USD wallet found")

        # 10. Check for suspicious activity patterns
        # (This would integrate with fraud detection in production)
        metadata["suspicious_score"] = 0.0  # Placeholder

        is_valid = len(errors) == 0
        return is_valid, errors, metadata

    async def validate_real_money_withdrawal(
        self,
        user_id: int,
        amount: Decimal,
        currency: str,
        destination: str,
        db: Optional[AsyncSession] = None,
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate real money withdrawal"""
        errors = []
        metadata = {}

        try:
            if db is None:
                async with get_db_context() as session:
                    return await self._validate_withdrawal_internal(
                        user_id,
                        amount,
                        currency,
                        destination,
                        session,
                        errors,
                        metadata,
                    )
            else:
                return await self._validate_withdrawal_internal(
                    user_id, amount, currency, destination, db, errors, metadata
                )
        except Exception as e:
            logger.error(f"Error validating withdrawal: {e}", exc_info=True)
            errors.append(f"Validation error: {str(e)}")
            return False, errors, metadata

    async def _validate_withdrawal_internal(
        self,
        user_id: int,
        amount: Decimal,
        currency: str,
        destination: str,
        db: AsyncSession,
        errors: List[str],
        metadata: Dict[str, Any],
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Internal withdrawal validation"""

        # 1. Validate user
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        if not user or not user.is_active:
            errors.append("User not found or inactive")
            return False, errors, metadata

        # 2. Validate amount
        if amount < Decimal("10"):  # Minimum withdrawal
            errors.append(f"Withdrawal amount {amount} is below minimum $10")

        if amount > Decimal("100000"):  # Maximum withdrawal per transaction
            errors.append(f"Withdrawal amount {amount} exceeds maximum $100,000")

        # 3. Check wallet balance
        wallet_result = await db.execute(
            select(Wallet).where(
                Wallet.user_id == user_id,
                Wallet.currency == currency,
                Wallet.is_active == True,
            )
        )
        wallet = wallet_result.scalar_one_or_none()

        if not wallet:
            errors.append(f"No active {currency} wallet found")
            return False, errors, metadata

        if wallet.available_balance < amount:
            errors.append(
                f"Insufficient balance: {wallet.available_balance} < {amount}"
            )

        metadata["wallet_balance"] = float(wallet.available_balance)

        # 4. Check daily withdrawal limit
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        withdrawal_result = await db.execute(
            select(func.sum(WalletTransaction.amount)).where(
                WalletTransaction.user_id == user_id,
                WalletTransaction.transaction_type == "withdrawal",
                WalletTransaction.status == "completed",
                WalletTransaction.created_at >= today_start,
            )
        )
        daily_withdrawals = withdrawal_result.scalar() or Decimal("0")
        max_daily_withdrawal = Decimal("500000")  # $500K per day

        if daily_withdrawals + amount > max_daily_withdrawal:
            errors.append(
                f"Daily withdrawal limit exceeded: {daily_withdrawals + amount} > {max_daily_withdrawal}"
            )

        metadata["daily_withdrawals"] = float(daily_withdrawals)

        # 5. Validate destination (basic check)
        if not destination or len(destination) < 10:
            errors.append("Invalid withdrawal destination")

        is_valid = len(errors) == 0
        return is_valid, errors, metadata

    async def log_real_money_operation(
        self,
        operation_type: str,
        user_id: int,
        details: Dict[str, Any],
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Log real money operation for audit"""
        try:
            from ..services.audit.audit_logger import audit_logger

            log_entry = {
                "operation_type": operation_type,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "success": success,
                "error": error,
                **details,
            }

            # Log to audit logger
            if operation_type == "trade":
                audit_logger.log_trade(
                    user_id=user_id,
                    trade_id=details.get("trade_id", "unknown"),
                    exchange=details.get("exchange", "unknown"),
                    symbol=details.get("symbol", "unknown"),
                    side=details.get("side", "unknown"),
                    amount=float(details.get("amount", 0)),
                    price=float(details.get("price", 0)),
                    mode="real",
                    success=success,
                    error=error,
                    **{
                        k: v
                        for k, v in details.items()
                        if k
                        not in [
                            "trade_id",
                            "exchange",
                            "symbol",
                            "side",
                            "amount",
                            "price",
                        ]
                    },
                )
            else:
                # Log other operations
                logger.warning(f"REAL MONEY {operation_type.upper()}: {log_entry}")

        except Exception as e:
            logger.error(f"Failed to log real money operation: {e}", exc_info=True)


# Global instance
real_money_safety_service = RealMoneySafetyService()
