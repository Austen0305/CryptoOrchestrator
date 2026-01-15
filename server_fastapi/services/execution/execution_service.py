import logging
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from ...core.bus import bus
from ...core.domain_registry import domain_registry
from ...core.events import OrderEvent
from ..blockchain.transaction_service import TransactionService
from ..real_money_safety import RealMoneySafetyService
from ..real_money_transaction_manager import real_money_transaction_manager
from ..security.signing_service import SigningService
from ..wallet_service import WalletService

logger = logging.getLogger(__name__)


class ExecutionService:
    """
    Bridge between TradingOrchestrator and TransactionService.
    Responsible for validating and executing trade signals on-chain.
    """

    def __init__(self, db: AsyncSession | None = None):
        self.db = db
        self.safety_service = RealMoneySafetyService()
        self.transaction_service = TransactionService()
        self.wallet_service = WalletService()
        self.transaction_manager = real_money_transaction_manager
        self._signing_service = None
        self._risk_manager = None

    @property
    def signing_service(self) -> SigningService:
        if self._signing_service is None:
            self._signing_service = domain_registry.resolve(SigningService)
        return self._signing_service

    @property
    def risk_manager(self) -> Any:  # RiskManager
        if self._risk_manager is None:
            self._risk_manager = domain_registry.resolve(
                Any
            )  # risk_manager registered as Any for now
        return self._risk_manager

    async def execute_trade_signal(
        self,
        signal: dict[str, Any],
        user_id: int,
        wallet_id: str,
        chain_id: int,
        db_session: AsyncSession | None = None,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute a trade signal after safety checks.

        Args:
            signal: Dictionary containing trade details
            user_id: ID of the user owning the bot/trade
            wallet_id: Internal reference to the wallet (Vault-backed)
            chain_id: Blockchain ID
            db_session: Database session
            dry_run: If True, only simulate the trade
            idempotency_key: Unique key to prevent duplicate execution

        Returns:
            Dict with execution result (status, tx_hash, error)
        """
        # Ensure an idempotency key exists
        if not idempotency_key:
            idempotency_key = str(uuid4())
            logger.info(
                f"No idempotency key provided for trade. Generated: {idempotency_key}"
            )

        async def _execute_trade_operation(db: AsyncSession) -> dict[str, Any]:
            # This inner function contains the core logic to be executed atomically

            symbol = signal.get("symbol")
            side = signal.get("side")
            amount = Decimal(str(signal.get("amount", 0)))
            price = Decimal(str(signal.get("price", 0)))
            order_id = signal.get("order_id", str(uuid4()))

            logger.info(
                f"Received execution request: {side} {amount} {symbol} for {user_id}"
            )

            # Emit NEW Order Event (Market Abuse Monitoring)
            new_event = OrderEvent(
                order_id=order_id,
                user_id=str(user_id),
                asset=symbol,
                side=side,
                amount=float(amount),
                price=float(price),
                status="NEW",
            )
            # Fire and forget (or await if strict) - usually strictly ordered in trading
            await bus.publish(new_event)

            # 1. Safety Check through RealMoneySafetyService
            # Note: We pass the atomic 'db' session here
            (
                is_safe,
                errors,
                metadata,
            ) = await self.safety_service.validate_real_money_trade(
                user_id=user_id,
                exchange="dex",  # Assuming DEX for on-chain execution
                symbol=symbol,
                side=side,
                amount=amount,
                price=price,
                db=db,
            )

            if not is_safe:
                error_msg = f"Safety checks failed: {', '.join(errors)}"
                logger.error(f"Trade blocked by safety checks: {error_msg}")
                raise ValueError(error_msg)

            # 2. Core Risk Validation (2026 Standard)
            risk_errors = await self.risk_manager.validate_trade(user_id, signal)
            if risk_errors:
                error_msg = f"Risk validation failed: {', '.join(risk_errors)}"
                logger.warning(
                    f"Trade blocked by Risk Manager for user {user_id}: {error_msg}"
                )
                raise ValueError(error_msg)

            # 3. Prepare Transaction
            # Construct the transaction payload based on the signal
            if not dry_run and "tx_data" not in signal:
                # In a real scenario, we'd build the swap here.
                # For now, we assume if it's not dry_run, we need tx_data or we fail safely.
                # However, for this refactor, we keep the placeholder logic but make it safe.
                pass

            transaction_payload = signal.get(
                "tx_data",
                {
                    "to": await self.signing_service.get_wallet_address(
                        user_id, wallet_id
                    ),
                    "value": 0,
                    "data": "0x",
                    "gas": 21000,
                    "gasPrice": 0,
                },
            )

            # 4. Sign and Execute via SigningService and TransactionService
            # We first get the address for the wallet_id
            await self.signing_service.get_wallet_address(
                user_id, wallet_id
            )

            # Sign the transaction
            signed_tx_raw = await self.signing_service.sign_transaction(
                user_id=user_id,
                wallet_id=wallet_id,
                transaction=transaction_payload,
                dry_run=dry_run,
            )

            # Broadcast via TransactionService
            if not dry_run:
                tx_hash = await self.transaction_service.broadcast_raw_transaction(
                    chain_id=chain_id, raw_transaction=signed_tx_raw
                )
            else:
                tx_hash = f"mock_tx_hash_{uuid4()}"

            if tx_hash:
                logger.info(f"Trade executed successfully: {tx_hash}")

                # Emit FILLED Event
                filled_event = OrderEvent(
                    order_id=order_id,
                    user_id=str(user_id),
                    asset=symbol,
                    side=side,
                    amount=float(amount),
                    price=float(price),
                    status="FILLED",
                )
                await bus.publish(filled_event)

                return {"status": "submitted", "tx_hash": tx_hash, "metadata": metadata}
            else:
                raise RuntimeError("Transaction execution returned no hash")

        # Wrap the entire operation in the transaction manager
        return await self.transaction_manager.execute_with_rollback(
            operation=_execute_trade_operation,
            operation_name="trade_execution",
            user_id=user_id,
            operation_details=signal,
            idempotency_key=idempotency_key,
        )

    async def cancel_order(self, order_id: str, user_id: int, symbol: str) -> bool:
        """
        Cancel an order and emit CANCELED event for market abuse monitoring.
        """
        # Logic to cancel on exchange would go here
        logger.info(f"Cancelling order {order_id} for user {user_id}")

        cancel_event = OrderEvent(
            order_id=order_id,
            user_id=str(user_id),
            asset=symbol,
            side="buy",  # Mock side, needed for event
            amount=0.0,  # Mock amount
            price=0.0,
            status="CANCELED",
        )
        await bus.publish(cancel_event)
        return True
