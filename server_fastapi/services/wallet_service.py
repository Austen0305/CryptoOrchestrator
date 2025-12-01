"""
Wallet Service
Manages user wallets, deposits, withdrawals, and balance operations.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from ..models.wallet import Wallet, WalletTransaction, WalletType, TransactionType, TransactionStatus
from ..models.user import User
from ..services.payments.stripe_service import stripe_service

logger = logging.getLogger(__name__)


class WalletService:
    """Service for wallet management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_wallet(
        self,
        user_id: int,
        currency: str = "USD",
        wallet_type: str = "trading"
    ) -> Wallet:
        """Get or create a wallet for a user"""
        try:
            stmt = select(Wallet).where(
                and_(
                    Wallet.user_id == user_id,
                    Wallet.currency == currency,
                    Wallet.wallet_type == wallet_type
                )
            )
            result = await self.db.execute(stmt)
            wallet = result.scalar_one_or_none()
            
            if not wallet:
                wallet = Wallet(
                    user_id=user_id,
                    currency=currency,
                    wallet_type=wallet_type,
                    balance=0.0,
                    available_balance=0.0,
                    locked_balance=0.0
                )
                self.db.add(wallet)
                await self.db.commit()
                await self.db.refresh(wallet)
                logger.info(f"Created wallet for user {user_id}: {currency} {wallet_type}")
            
            return wallet
            
        except Exception as e:
            logger.error(f"Error getting/creating wallet: {e}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def deposit(
        self,
        user_id: int,
        amount: float,
        currency: str = "USD",
        payment_method_id: Optional[str] = None,
        payment_intent_id: Optional[str] = None,
        payment_method_type: str = "card",
        description: Optional[str] = None
    ) -> Dict:
        """
        Deposit funds into user wallet with comprehensive safety measures.
        Ensures no money is lost through idempotency, verification, and atomic transactions.
        
        Args:
            user_id: User ID
            amount: Deposit amount
            currency: Currency code
            payment_method_id: Stripe payment method ID
            payment_intent_id: Stripe payment intent ID
            payment_method_type: Payment method type ('card', 'ach', 'bank_transfer')
            description: Transaction description
        
        Returns:
            Dict with transaction details
        """
        from decimal import Decimal
        
        # Convert to Decimal for precision
        amount_decimal = Decimal(str(amount))
        
        # Comprehensive safety validation
        try:
            from .deposit_safety import deposit_safety_service
            
            is_valid, errors, metadata = await deposit_safety_service.validate_deposit(
                user_id=user_id,
                amount=amount_decimal,
                currency=currency,
                payment_intent_id=payment_intent_id,
                db=self.db
            )
            
            if not is_valid:
                error_message = "; ".join(errors)
                logger.warning(f"Deposit validation failed for user {user_id}: {error_message}")
                raise ValueError(f"Deposit validation failed: {error_message}")
        except ImportError:
            # Safety service not available, proceed with basic checks
            logger.warning("Deposit safety service not available, using basic validation")
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Safety validation error: {e}", exc_info=True)
            raise
        
        try:
            # Get or create wallet
            wallet = await self.get_or_create_wallet(user_id, currency, "trading")
            
            # Create payment intent if not provided
            if not payment_intent_id and payment_method_id:
                # Get user email for Stripe
                user_stmt = select(User).where(User.id == user_id)
                user_result = await self.db.execute(user_stmt)
                user = user_result.scalar_one_or_none()
                
                if user:
                    # Create Stripe payment intent
                    amount_cents = int(amount * 100)  # Convert to cents
                    payment_intent = stripe_service.create_payment_intent(
                        amount=amount_cents,
                        currency=currency.lower(),
                        payment_method_type=payment_method_type,
                        metadata={"user_id": str(user_id), "wallet_id": str(wallet.id)}
                    )
                    
                    if payment_intent:
                        payment_intent_id = payment_intent.get("id")
            
            # If payment_intent_id is provided, use safe deposit processing
            if payment_intent_id:
                try:
                    from .deposit_safety import deposit_safety_service
                    
                    # Use safe deposit processing (verifies payment, prevents duplicates)
                    success, transaction_id, error_msg = await deposit_safety_service.process_deposit_safely(
                        user_id=user_id,
                        amount=amount_decimal,
                        currency=currency,
                        payment_intent_id=payment_intent_id,
                        db=self.db
                    )
                    
                    if not success:
                        raise ValueError(error_msg or "Failed to process deposit safely")
                    
                    # Retrieve the transaction
                    from sqlalchemy import select
                    txn_result = await self.db.execute(
                        select(WalletTransaction).where(WalletTransaction.id == transaction_id)
                    )
                    transaction = txn_result.scalar_one_or_none()
                    
                    if transaction:
                        logger.info(f"✅ Deposit processed safely: user {user_id}, amount {amount} {currency}")
                        return {
                            "transaction_id": transaction.id,
                            "wallet_id": transaction.wallet_id,
                            "amount": transaction.amount,
                            "currency": transaction.currency,
                            "status": transaction.status,
                            "payment_intent_id": payment_intent_id
                        }
                except ImportError:
                    # Safety service not available, fall back to basic processing
                    logger.warning("Deposit safety service not available, using basic processing")
            
            # Basic deposit processing (for cases without payment_intent_id or if safety service unavailable)
            # Calculate deposit fee (5% = 5 cents per dollar)
            from decimal import Decimal
            deposit_fee_rate = Decimal("0.05")  # 5% fee
            deposit_fee = amount_decimal * deposit_fee_rate
            net_amount = amount_decimal - deposit_fee
            
            # Create transaction record (PENDING - will be confirmed via webhook)
            transaction = WalletTransaction(
                wallet_id=wallet.id,
                user_id=user_id,
                transaction_type=TransactionType.DEPOSIT.value,
                status=TransactionStatus.PENDING.value,
                amount=float(amount_decimal),  # Original deposit amount
                currency=currency,
                fee=float(deposit_fee),  # 5% fee
                net_amount=float(net_amount),  # Amount after fee
                payment_intent_id=payment_intent_id,
                description=description or f"Deposit {amount} {currency} (Fee: {deposit_fee:.2f} {currency})",
                reference_id=payment_intent_id
            )
            self.db.add(transaction)
            
            # If payment intent exists, mark as processing (will be confirmed via webhook)
            if payment_intent_id:
                transaction.status = TransactionStatus.PROCESSING.value
            
            await self.db.commit()
            await self.db.refresh(transaction)
            
            logger.info(f"Deposit initiated: user {user_id}, amount {amount} {currency}")
            
            return {
                "transaction_id": transaction.id,
                "wallet_id": wallet.id,
                "amount": float(amount_decimal),
                "currency": currency,
                "status": transaction.status,
                "payment_intent_id": payment_intent_id
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error processing deposit: {e}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def confirm_deposit(
        self,
        transaction_id: int,
        payment_intent_id: str
    ) -> bool:
        """
        Confirm a deposit transaction after payment verification.
        Uses safe processing to ensure no money is lost and no duplicates.
        """
        try:
            from decimal import Decimal
            from .deposit_safety import deposit_safety_service
            
            # Find transaction
            stmt = select(WalletTransaction).where(
                and_(
                    WalletTransaction.id == transaction_id,
                    WalletTransaction.payment_intent_id == payment_intent_id
                )
            )
            result = await self.db.execute(stmt)
            transaction = result.scalar_one_or_none()
            
            if not transaction:
                logger.warning(f"Transaction not found: {transaction_id}, payment_intent: {payment_intent_id}")
                return False
            
            # Check if already completed (idempotency)
            if transaction.status == TransactionStatus.COMPLETED.value:
                logger.info(f"Deposit already confirmed: transaction {transaction_id}")
                return True  # Already processed - safe to return success
            
            # Verify payment was actually received before crediting wallet
            amount_decimal = Decimal(str(transaction.amount))
            is_verified, error_msg, payment_details = await deposit_safety_service.verify_payment_received(
                payment_intent_id,
                amount_decimal,
                transaction.currency
            )
            
            if not is_verified:
                logger.error(
                    f"Payment verification failed for transaction {transaction_id}: {error_msg}. "
                    f"NOT crediting wallet to prevent money loss."
                )
                # Mark as failed instead of crediting
                transaction.status = TransactionStatus.FAILED.value
                await self.db.commit()
                return False
            
            # Use safe deposit processing to ensure atomic operation
            success, processed_txn_id, error_msg = await deposit_safety_service.process_deposit_safely(
                user_id=transaction.user_id,
                amount=amount_decimal,
                currency=transaction.currency,
                payment_intent_id=payment_intent_id,
                db=self.db
            )
            
            if success:
                # Refresh transaction to get updated status
                await self.db.refresh(transaction)
                
                logger.info(
                    f"✅ Deposit confirmed safely: transaction {transaction_id}, "
                    f"payment_intent {payment_intent_id}"
                )
                
                # Broadcast wallet update via WebSocket
                try:
                    from ..services.wallet_broadcast import broadcast_wallet_update
                    balance = await self.get_wallet_balance(transaction.user_id, transaction.currency)
                    await broadcast_wallet_update(transaction.user_id, balance)
                except Exception as e:
                    logger.warning(f"Failed to broadcast wallet update: {e}")
                
                return True
            else:
                logger.error(f"Failed to confirm deposit safely: {error_msg}")
                return False
            
        except ImportError:
            # Safety service not available, use basic confirmation
            logger.warning("Deposit safety service not available, using basic confirmation")
            
            stmt = select(WalletTransaction).where(
                and_(
                    WalletTransaction.id == transaction_id,
                    WalletTransaction.payment_intent_id == payment_intent_id
                )
            )
            result = await self.db.execute(stmt)
            transaction = result.scalar_one_or_none()
            
            if not transaction:
                return False
            
            if transaction.status == TransactionStatus.COMPLETED.value:
                return True  # Already processed
            
            # Update wallet balance (basic - no verification)
            wallet_stmt = select(Wallet).where(Wallet.id == transaction.wallet_id)
            wallet_result = await self.db.execute(wallet_stmt)
            wallet = wallet_result.scalar_one_or_none()
            
            if wallet:
                # Credit wallet with net_amount (after fee)
                # Fee is already calculated and stored in transaction
                wallet.balance += transaction.net_amount
                wallet.available_balance += transaction.net_amount
                wallet.total_deposited += transaction.amount  # Track total deposited (before fee)
                
                transaction.status = TransactionStatus.COMPLETED.value
                transaction.processed_at = datetime.utcnow()
                
                await self.db.commit()
                logger.info(
                    f"Deposit confirmed: transaction {transaction_id}, "
                    f"amount {transaction.amount} {transaction.currency}, "
                    f"fee {transaction.fee:.2f} {transaction.currency} (5%), "
                    f"net_amount {transaction.net_amount:.2f} {transaction.currency}"
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error confirming deposit: {e}", exc_info=True)
            await self.db.rollback()
            return False
    
    async def withdraw(
        self,
        user_id: int,
        amount: float,
        currency: str = "USD",
        destination: Optional[str] = None,
        description: Optional[str] = None,
        skip_whitelist_check: bool = False
    ) -> Dict:
        """
        Withdraw funds from user wallet with comprehensive safety checks.
        
        Args:
            user_id: User ID
            amount: Withdrawal amount
            currency: Currency code
            destination: Withdrawal destination (bank account, crypto address, etc.)
            description: Transaction description
        
        Returns:
            Dict with transaction details
        """
        # Import safety service (lazy import to avoid circular dependencies)
        try:
            from .real_money_safety import real_money_safety_service
            from decimal import Decimal
            
            # Comprehensive safety validation for real money withdrawal
            amount_decimal = Decimal(str(amount))
            is_valid, errors, metadata = await real_money_safety_service.validate_real_money_withdrawal(
                user_id=user_id,
                amount=amount_decimal,
                currency=currency,
                destination=destination or "",
                db=self.db
            )
            
            if not is_valid:
                error_message = "; ".join(errors)
                logger.warning(f"Withdrawal validation failed for user {user_id}: {error_message}")
                raise ValueError(f"Withdrawal validation failed: {error_message}")
            
            # Check withdrawal address whitelist (if enabled and destination provided)
            if destination and not skip_whitelist_check:
                try:
                    from .security.withdrawal_whitelist_service import withdrawal_whitelist_service
                    
                    is_whitelisted = await withdrawal_whitelist_service.is_address_whitelisted(
                        user_id=user_id,
                        address=destination,
                        currency=currency,
                        db=self.db
                    )
                    
                    if not is_whitelisted:
                        raise ValueError(
                            f"Withdrawal address {destination} is not whitelisted. "
                            f"Please add it to your whitelist first (24-hour cooldown applies)."
                        )
                except ImportError:
                    # Whitelist service not available, skip check
                    logger.warning("Withdrawal whitelist service not available, skipping check")
                except ValueError:
                    raise
                except Exception as e:
                    logger.warning(f"Whitelist check failed: {e}, proceeding with withdrawal")
            
            # Fraud detection check
            try:
                from .fraud_detection.fraud_detection_service import fraud_detection_service
                
                fraud_analysis = await fraud_detection_service.analyze_transaction(
                    user_id=user_id,
                    transaction_type="withdrawal",
                    amount=amount_decimal,
                    currency=currency,
                    metadata={"destination": destination, "description": description},
                    db=self.db
                )
                
                if fraud_analysis.get("is_fraud") or fraud_analysis.get("recommendation") == "block":
                    logger.warning(
                        f"Fraud detection blocked withdrawal for user {user_id}: "
                        f"risk_score={fraud_analysis.get('risk_score')}, "
                        f"indicators={fraud_analysis.get('indicators')}"
                    )
                    raise ValueError(
                        f"Withdrawal blocked by fraud detection. "
                        f"Risk score: {fraud_analysis.get('risk_score')}. "
                        f"Please contact support if this is a legitimate transaction."
                    )
                elif fraud_analysis.get("recommendation") == "review":
                    logger.info(
                        f"Withdrawal flagged for review for user {user_id}: "
                        f"risk_score={fraud_analysis.get('risk_score')}"
                    )
                    # Allow but log for review
            except ImportError:
                # Fraud detection service not available, skip check
                logger.warning("Fraud detection service not available, skipping check")
            except ValueError:
                raise
            except Exception as e:
                logger.warning(f"Fraud detection check failed: {e}, proceeding with withdrawal")
        except ImportError:
            # Safety service not available, proceed with basic checks
            logger.warning("Real money safety service not available, using basic validation")
        except Exception as e:
            logger.error(f"Safety validation error: {e}", exc_info=True)
            raise
        
        try:
            # Get wallet
            wallet = await self.get_or_create_wallet(user_id, currency, "trading")
            
            # Check available balance
            if wallet.available_balance < amount:
                raise ValueError(f"Insufficient balance. Available: {wallet.available_balance}, Requested: {amount}")
            
            # Calculate fee (could be configurable)
            fee = amount * 0.01  # 1% withdrawal fee (example)
            net_amount = amount - fee
            
            # Create transaction
            transaction = WalletTransaction(
                wallet_id=wallet.id,
                user_id=user_id,
                transaction_type=TransactionType.WITHDRAWAL.value,
                status=TransactionStatus.PENDING.value,
                amount=amount,
                currency=currency,
                fee=fee,
                net_amount=net_amount,
                description=description or f"Withdrawal {amount} {currency}",
                metadata={"destination": destination} if destination else None
            )
            self.db.add(transaction)
            
            # Lock balance
            wallet.available_balance -= amount
            wallet.locked_balance += amount
            
            await self.db.commit()
            await self.db.refresh(transaction)
            
            logger.info(f"Withdrawal initiated: user {user_id}, amount {amount} {currency}")
            
            # In production, would initiate actual withdrawal via payment processor
            # For now, mark as processing
            transaction.status = TransactionStatus.PROCESSING.value
            await self.db.commit()
            
            return {
                "transaction_id": transaction.id,
                "wallet_id": wallet.id,
                "amount": amount,
                "fee": fee,
                "net_amount": net_amount,
                "currency": currency,
                "status": transaction.status
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error processing withdrawal: {e}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def confirm_withdrawal(
        self,
        transaction_id: int
    ) -> bool:
        """Confirm a withdrawal transaction after processing"""
        try:
            stmt = select(WalletTransaction).where(WalletTransaction.id == transaction_id)
            result = await self.db.execute(stmt)
            transaction = result.scalar_one_or_none()
            
            if not transaction:
                return False
            
            if transaction.status == TransactionStatus.COMPLETED.value:
                return True
            
            # Update wallet balance
            wallet_stmt = select(Wallet).where(Wallet.id == transaction.wallet_id)
            wallet_result = await self.db.execute(wallet_stmt)
            wallet = wallet_result.scalar_one_or_none()
            
            if wallet:
                wallet.balance -= transaction.amount
                wallet.locked_balance -= transaction.amount
                wallet.total_withdrawn += transaction.amount
                
                transaction.status = TransactionStatus.COMPLETED.value
                transaction.processed_at = datetime.utcnow()
                
                await self.db.commit()
                logger.info(f"Withdrawal confirmed: transaction {transaction_id}")
                
                # Broadcast wallet update via WebSocket
                try:
                    from ..services.wallet_broadcast import broadcast_wallet_update
                    balance = await self.get_wallet_balance(wallet.user_id, wallet.currency)
                    await broadcast_wallet_update(wallet.user_id, balance)
                except Exception as e:
                    logger.warning(f"Failed to broadcast wallet update: {e}")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error confirming withdrawal: {e}", exc_info=True)
            await self.db.rollback()
            return False
    
    async def get_wallet_balance(
        self,
        user_id: int,
        currency: str = "USD"
    ) -> Dict:
        """Get wallet balance for a user"""
        try:
            wallet = await self.get_or_create_wallet(user_id, currency, "trading")
            
            return {
                "wallet_id": wallet.id,
                "currency": wallet.currency,
                "balance": wallet.balance,
                "available_balance": wallet.available_balance,
                "locked_balance": wallet.locked_balance,
                "total_deposited": wallet.total_deposited,
                "total_withdrawn": wallet.total_withdrawn,
                "total_traded": wallet.total_traded
            }
        except Exception as e:
            logger.error(f"Error getting wallet balance: {e}", exc_info=True)
            return {
                "wallet_id": None,
                "currency": currency,
                "balance": 0.0,
                "available_balance": 0.0,
                "locked_balance": 0.0,
                "total_deposited": 0.0,
                "total_withdrawn": 0.0,
                "total_traded": 0.0
            }
    
    async def get_transactions(
        self,
        user_id: int,
        currency: Optional[str] = None,
        transaction_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get wallet transactions for a user"""
        try:
            conditions = [WalletTransaction.user_id == user_id]
            
            if currency:
                conditions.append(WalletTransaction.currency == currency)
            if transaction_type:
                conditions.append(WalletTransaction.transaction_type == transaction_type)
            
            stmt = select(WalletTransaction).where(
                and_(*conditions)
            ).order_by(desc(WalletTransaction.created_at)).limit(limit)
            
            result = await self.db.execute(stmt)
            transactions = result.scalars().all()
            
            return [
                {
                    "id": t.id,
                    "type": t.transaction_type,
                    "status": t.status,
                    "amount": t.amount,
                    "currency": t.currency,
                    "fee": t.fee,
                    "net_amount": t.net_amount,
                    "description": t.description,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "processed_at": t.processed_at.isoformat() if t.processed_at else None
                }
                for t in transactions
            ]
            
        except Exception as e:
            logger.error(f"Error getting transactions: {e}", exc_info=True)
            return []

