import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..blockchain.transaction_service import TransactionService
from ..real_money_safety import RealMoneySafetyService
from ..wallet_service import WalletService

logger = logging.getLogger(__name__)


class ExecutionService:
    """
    Bridge between TradingOrchestrator and TransactionService.
    Responsible for validating and executing trade signals on-chain.
    """

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.safety_service = RealMoneySafetyService()
        self.transaction_service = (
            TransactionService()
        )  # In a real app, this might be injected
        self.wallet_service = WalletService()  # For checking balances/address info

    async def execute_trade_signal(
        self,
        signal: Dict[str, Any],
        user_id: int,
        wallet_address: str,
        chain_id: int,
        private_key: str,  # In Phase 4 this will be replaced by a secure signer reference
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Execute a trade signal after safety checks.

        Args:
            signal: Dictionary containing trade details (symbol, side, amount, price)
            user_id: ID of the user owning the bot/trade
            wallet_address: Address to execute from
            chain_id: Blockchain ID
            private_key: Private key for signing (TEMPORARY: until Phase 4 KMS)
            db_session: Database session

        Returns:
            Dict with execution result (status, tx_hash, error)
        """
        session = db_session or self.db
        if not session:
            raise ValueError("Database session required for execution")

        symbol = signal.get("symbol")
        side = signal.get("side")
        amount = Decimal(str(signal.get("amount", 0)))
        price = Decimal(str(signal.get("price", 0)))

        logger.info(
            f"Received execution request: {side} {amount} {symbol} for {user_id}"
        )

        # 1. Safety Check through RealMoneySafetyService
        is_safe, errors, metadata = await self.safety_service.validate_real_money_trade(
            user_id=user_id,
            exchange="dex",  # Assuming DEX for on-chain execution
            symbol=symbol,
            side=side,
            amount=amount,
            price=price,
            db=session,
        )

        if not is_safe:
            logger.error(f"Trade blocked by safety checks: {errors}")
            return {
                "status": "failed",
                "error": f"Safety checks failed: {', '.join(errors)}",
                "metadata": metadata,
            }

        # 2. Prepare Transaction
        # Construct the transaction payload based on the signal
        # This is simplified; in reality we'd need to swap tokens via a router contract
        # For this phase, we'll verify we CAN call the TransactionService

        # Example transaction structure (would need ABI encoding for actual swap)
        transaction_payload = {
            "to": wallet_address,  # Self-transfer as placeholder if checking connectivity
            "value": 0,
            "data": "0x",  # Placeholder for swap call data
            "gas": 21000,
            "gasPrice": 0,  # Will be filled by transaction service
        }

        # TODO: Implement actual Swap Router interaction (Uniswap/Sushi) here
        # For Phase 3, we focus on the *link* existing.
        # We will assume 'signal' might contain pre-prepared tx data or we build it.

        if "tx_data" in signal:
            transaction_payload = signal["tx_data"]

        try:
            # 3. Execute via TransactionService
            tx_hash = await self.transaction_service.sign_and_send_transaction(
                chain_id=chain_id,
                private_key=private_key,
                transaction=transaction_payload,
                use_mev_protection=True,  # Default to safe
            )

            if tx_hash:
                logger.info(f"Trade executed successfully: {tx_hash}")
                return {"status": "submitted", "tx_hash": tx_hash, "metadata": metadata}
            else:
                return {
                    "status": "failed",
                    "error": "Transaction execution returned no hash",
                    "metadata": metadata,
                }

        except Exception as e:
            logger.error(f"Transaction execution exception: {e}")
            return {"status": "error", "error": str(e), "metadata": metadata}
