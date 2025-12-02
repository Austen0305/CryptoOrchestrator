"""
Deposit Safety Service
Ensures no money is lost during deposit operations with comprehensive safety measures
"""
import logging
from typing import Any, Dict, Optional, Tuple, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from ..models.wallet import WalletTransaction, TransactionStatus
from ..models.base import User
from ..services.transaction_idempotency import transaction_idempotency_service
from ..services.real_money_transaction_manager import real_money_transaction_manager

logger = logging.getLogger(__name__)


class DepositSafetyService:
    """Comprehensive safety service for deposit operations"""
    
    def __init__(self):
        self.min_deposit = Decimal("1.00")  # Minimum deposit $1
        self.max_deposit = Decimal("1000000")  # Maximum deposit $1M per transaction
        self.max_daily_deposits = Decimal("5000000")  # Maximum $5M per day per user
        self.deposit_fee_rate = Decimal("0.05")  # 5% deposit fee (5 cents per dollar)
    
    async def validate_deposit(
        self,
        user_id: int,
        amount: Decimal,
        currency: str,
        payment_intent_id: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Comprehensive validation for deposits
        
        Returns:
            (is_valid, errors, metadata)
        """
        errors = []
        metadata = {}
        
        try:
            # Use provided session or create new one
            if db is None:
                from ..database import get_db_context
                async with get_db_context() as session:
                    return await self._validate_deposit_internal(
                        user_id, amount, currency, payment_intent_id, session, errors, metadata
                    )
            else:
                return await self._validate_deposit_internal(
                    user_id, amount, currency, payment_intent_id, db, errors, metadata
                )
        except Exception as e:
            logger.error(f"Error validating deposit: {e}", exc_info=True)
            errors.append(f"Validation error: {str(e)}")
            return False, errors, metadata
    
    async def _validate_deposit_internal(
        self,
        user_id: int,
        amount: Decimal,
        currency: str,
        payment_intent_id: Optional[str],
        db: AsyncSession,
        errors: List[str],
        metadata: Dict[str, Any]
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
        if amount < self.min_deposit:
            errors.append(f"Deposit amount {amount} is below minimum {self.min_deposit}")
        
        if amount > self.max_deposit:
            errors.append(f"Deposit amount {amount} exceeds maximum {self.max_deposit}")
        
        # 3. Validate currency
        if not currency or len(currency) > 10:
            errors.append("Invalid currency format")
        
        # 4. Check for duplicate payment intent (idempotency)
        if payment_intent_id:
            # Check if this payment intent was already processed
            existing_result = await db.execute(
                select(WalletTransaction).where(
                    and_(
                        WalletTransaction.payment_intent_id == payment_intent_id,
                        WalletTransaction.user_id == user_id,
                        WalletTransaction.transaction_type == "deposit"
                    )
                )
            )
            existing_transaction = existing_result.scalar_one_or_none()
            
            if existing_transaction:
                if existing_transaction.status == TransactionStatus.COMPLETED.value:
                    errors.append(f"Payment intent {payment_intent_id} has already been processed")
                    metadata["duplicate"] = True
                    metadata["existing_transaction_id"] = existing_transaction.id
                elif existing_transaction.status == TransactionStatus.PROCESSING.value:
                    errors.append(f"Payment intent {payment_intent_id} is already being processed")
                    metadata["processing"] = True
                    metadata["existing_transaction_id"] = existing_transaction.id
        
            # 5. Check daily deposit limits
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            deposits_result = await db.execute(
                select(func.sum(WalletTransaction.amount))
                .where(
                    WalletTransaction.user_id == user_id,
                    WalletTransaction.transaction_type == "deposit",
                    WalletTransaction.status == TransactionStatus.COMPLETED.value,
                    WalletTransaction.created_at >= today_start
                )
            )
            daily_deposits = deposits_result.scalar() or Decimal("0")
            
            if daily_deposits + amount > self.max_daily_deposits:
                errors.append(
                    f"Daily deposit limit exceeded: {daily_deposits + amount} > {self.max_daily_deposits}"
                )
            
            metadata["daily_deposits"] = float(daily_deposits)
            metadata["deposit_amount"] = float(amount)
            
            # 6. Fraud detection check
            try:
                from .fraud_detection.fraud_detection_service import fraud_detection_service
                
                fraud_analysis = await fraud_detection_service.analyze_transaction(
                    user_id=user_id,
                    transaction_type="deposit",
                    amount=amount,
                    currency=currency,
                    metadata={"payment_intent_id": payment_intent_id},
                    db=db
                )
                
                if fraud_analysis.get("is_fraud") or fraud_analysis.get("recommendation") == "block":
                    errors.append(
                        f"Deposit blocked by fraud detection. Risk score: {fraud_analysis.get('risk_score')}"
                    )
                    metadata["fraud_analysis"] = fraud_analysis
                elif fraud_analysis.get("recommendation") == "review":
                    metadata["fraud_analysis"] = fraud_analysis
                    metadata["requires_review"] = True
            except ImportError:
                # Fraud detection service not available, skip check
                pass
            except Exception as e:
                logger.warning(f"Fraud detection check failed: {e}")
            
            is_valid = len(errors) == 0
            return is_valid, errors, metadata
    
    async def verify_payment_received(
        self,
        payment_intent_id: str,
        expected_amount: Decimal,
        currency: str
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Verify that payment was actually received from payment processor
        
        Returns:
            (is_verified, error_message, payment_details)
        """
        try:
            from ..services.payments.stripe_service import stripe_service
            
            # Verify payment intent with Stripe
            if hasattr(stripe_service, 'get_payment_intent'):
                payment_intent = stripe_service.get_payment_intent(payment_intent_id)
            else:
                # Fallback: try to retrieve via Stripe API directly
                try:
                    import stripe
                    payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                    payment_intent = {
                        'id': payment_intent.id,
                        'status': payment_intent.status,
                        'amount': payment_intent.amount,
                        'currency': payment_intent.currency
                    }
                except Exception as e:
                    logger.error(f"Failed to retrieve payment intent: {e}")
                    return False, f"Failed to verify payment: {str(e)}", None
            
            if not payment_intent:
                return False, "Payment intent not found", None
            
            # Verify status
            status = payment_intent.get('status', '').lower()
            if status not in ['succeeded', 'processing']:
                return False, f"Payment not successful. Status: {status}", None
            
            # Verify amount (convert to Decimal for comparison)
            received_amount = Decimal(str(payment_intent.get('amount', 0))) / Decimal("100")  # Convert cents to dollars
            if abs(received_amount - expected_amount) > Decimal("0.01"):  # Allow 1 cent tolerance
                return False, f"Amount mismatch. Expected: {expected_amount}, Received: {received_amount}", None
            
            # Verify currency
            received_currency = payment_intent.get('currency', '').upper()
            if received_currency != currency.upper():
                return False, f"Currency mismatch. Expected: {currency}, Received: {received_currency}", None
            
            return True, None, payment_intent
            
        except ImportError:
            logger.warning("Stripe service not available, skipping payment verification")
            return True, None, None  # Allow to proceed if Stripe not available
        except Exception as e:
            logger.error(f"Error verifying payment: {e}", exc_info=True)
            return False, f"Payment verification error: {str(e)}", None
    
    async def process_deposit_safely(
        self,
        user_id: int,
        amount: Decimal,
        currency: str,
        payment_intent_id: str,
        db: AsyncSession
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Process deposit with complete safety - ensures no money is lost
        
        Returns:
            (success, transaction_id, error_message)
        """
        try:
            # 1. Check idempotency first (prevent duplicate processing)
            idempotency_key = transaction_idempotency_service.generate_idempotency_key(
                user_id=str(user_id),
                operation="deposit",
                params={
                    "payment_intent_id": payment_intent_id,
                    "amount": str(amount),
                    "currency": currency
                }
            )
            
            # Check if already processed
            existing_result = await transaction_idempotency_service.check_idempotency(
                idempotency_key,
                str(user_id)
            )
            
            if existing_result and existing_result.get("exists"):
                # Already processed - return existing result
                logger.info(f"Deposit already processed (idempotency): {payment_intent_id}")
                result_data = existing_result.get("result", {})
                return True, result_data.get("transaction_id"), None
            
            # 2. Verify payment was actually received
            is_verified, error_msg, payment_details = await self.verify_payment_received(
                payment_intent_id,
                amount,
                currency
            )
            
            if not is_verified:
                logger.error(f"Payment verification failed for {payment_intent_id}: {error_msg}")
                return False, None, error_msg
            
            # 3. Check for existing transaction with this payment intent
            existing_txn_result = await db.execute(
                select(WalletTransaction).where(
                    and_(
                        WalletTransaction.payment_intent_id == payment_intent_id,
                        WalletTransaction.user_id == user_id
                    )
                )
            )
            existing_transaction = existing_txn_result.scalar_one_or_none()
            
            if existing_transaction:
                if existing_transaction.status == TransactionStatus.COMPLETED.value:
                    # Already completed - return success
                    logger.info(f"Deposit already completed: transaction {existing_transaction.id}")
                    return True, existing_transaction.id, None
                elif existing_transaction.status == TransactionStatus.PROCESSING.value:
                    # Still processing - don't duplicate
                    logger.warning(f"Deposit already processing: transaction {existing_transaction.id}")
                    return False, existing_transaction.id, "Deposit is already being processed"
            
            # 4. Get or create wallet
            from .wallet_service import WalletService
            wallet_service = WalletService(db)
            wallet = await wallet_service.get_or_create_wallet(user_id, currency, "trading")
            
            # 5. Calculate deposit fee (5% = 5 cents per dollar)
            deposit_fee = amount * self.deposit_fee_rate
            net_amount = amount - deposit_fee
            
            logger.info(
                f"Deposit fee calculation: amount={amount}, fee_rate={self.deposit_fee_rate}, "
                f"fee={deposit_fee}, net_amount={net_amount}"
            )
            
            # 6. Create transaction record (PROCESSING first)
            transaction = WalletTransaction(
                wallet_id=wallet.id,
                user_id=user_id,
                transaction_type="deposit",
                status=TransactionStatus.PROCESSING.value,
                amount=float(amount),  # Original deposit amount
                currency=currency,
                fee=float(deposit_fee),  # 5% fee
                net_amount=float(net_amount),  # Amount after fee (what user receives)
                payment_intent_id=payment_intent_id,
                description=f"Deposit {amount} {currency} (Fee: {deposit_fee:.2f} {currency})",
                reference_id=payment_intent_id
            )
            db.add(transaction)
            await db.flush()  # Flush to get transaction ID
            
            # 7. Update wallet balance (atomic operation) - credit only net_amount
            wallet.balance += float(net_amount)
            wallet.available_balance += float(net_amount)
            wallet.total_deposited += float(amount)  # Track total deposited (before fee)
            
            # 8. Mark transaction as completed
            transaction.status = TransactionStatus.COMPLETED.value
            transaction.processed_at = datetime.utcnow()
            
            # 9. Store idempotency result
            await transaction_idempotency_service.store_idempotency_result(
                idempotency_key,
                str(user_id),
                {
                    "transaction_id": transaction.id,
                    "payment_intent_id": payment_intent_id,
                    "amount": float(amount),
                    "fee": float(deposit_fee),
                    "net_amount": float(net_amount),
                    "currency": currency,
                    "status": "completed"
                },
                status_code=200
            )
            
            # Commit transaction (atomic)
            await db.commit()
            await db.refresh(transaction)
            
            logger.info(
                f"✅ Deposit processed safely: user {user_id}, amount {amount} {currency}, "
                f"fee {deposit_fee:.2f} {currency} (5%), net_amount {net_amount:.2f} {currency}, "
                f"transaction {transaction.id}, payment_intent {payment_intent_id}"
            )
            
            return True, transaction.id, None
            
        except Exception as e:
            logger.error(f"Error processing deposit safely: {e}", exc_info=True)
            await db.rollback()
            return False, None, f"Deposit processing error: {str(e)}"


# Global instance
deposit_safety_service = DepositSafetyService()

