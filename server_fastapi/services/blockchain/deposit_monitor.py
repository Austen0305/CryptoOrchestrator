"""
Deposit Monitoring Service
Monitors blockchain for deposits to user wallets
Runs as background task to detect incoming transactions
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from .web3_service import get_web3_service
from .balance_service import get_balance_service
from ...models.user_wallet import UserWallet
from ...models.dex_trade import DEXTrade
from ...repositories.wallet_repository import WalletRepository

logger = logging.getLogger(__name__)


class DepositMonitor:
    """Service for monitoring blockchain deposits"""

    def __init__(self):
        self.web3_service = get_web3_service()
        self.balance_service = get_balance_service()
        self._last_checked_block: Dict[int, int] = {}  # {chain_id: block_number}

    async def check_deposits(
        self, chain_id: int, db: AsyncSession, lookback_blocks: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Check for new deposits on a specific chain

        Args:
            chain_id: Blockchain chain ID
            db: Database session
            lookback_blocks: Number of blocks to look back

        Returns:
            List of deposit events found
        """
        deposits_found = []

        try:
            # Get Web3 connection
            w3 = await self.web3_service.get_connection(chain_id)
            if not w3:
                logger.warning(f"No Web3 connection for chain {chain_id}")
                return deposits_found

            # Get current block number
            current_block = await w3.eth.block_number
            if current_block is None:
                logger.warning(f"Could not get current block for chain {chain_id}")
                return deposits_found

            # Determine starting block
            last_checked = self._last_checked_block.get(chain_id)
            if last_checked:
                start_block = max(last_checked + 1, current_block - lookback_blocks)
            else:
                # First time checking, look back a reasonable amount
                start_block = max(1, current_block - lookback_blocks)

            if start_block > current_block:
                # No new blocks
                return deposits_found

            logger.debug(
                f"Checking deposits on chain {chain_id} from block {start_block} to {current_block}",
                extra={
                    "chain_id": chain_id,
                    "start_block": start_block,
                    "current_block": current_block,
                },
            )

            # Get all active custodial wallets for this chain
            repository = WalletRepository(db)
            wallets = await repository.get_user_wallets(None)  # Get all wallets
            chain_wallets = [
                w
                for w in wallets
                if w.chain_id == chain_id
                and w.wallet_type == "custodial"
                and w.is_active
            ]

            if not chain_wallets:
                logger.debug(f"No active custodial wallets found for chain {chain_id}")
                self._last_checked_block[chain_id] = current_block
                return deposits_found

            # Check each block for transactions to our wallets
            wallet_addresses = {w.wallet_address.lower() for w in chain_wallets}

            for block_num in range(start_block, current_block + 1):
                try:
                    block = await w3.eth.get_block(block_num, full_transactions=True)

                    # Check each transaction in the block
                    for tx in block.get("transactions", []):
                        if not isinstance(tx, dict):
                            continue

                        to_address = tx.get("to")
                        if not to_address:
                            continue

                        to_address_lower = (
                            to_address.lower()
                            if isinstance(to_address, str)
                            else to_address.hex().lower()
                        )

                        # Check if transaction is to one of our wallets
                        if to_address_lower in wallet_addresses:
                            value = tx.get("value", 0)
                            if (
                                value > 0
                            ):  # Only count transactions with value (ETH deposits)
                                # Find the wallet
                                wallet = next(
                                    (
                                        w
                                        for w in chain_wallets
                                        if w.wallet_address.lower() == to_address_lower
                                    ),
                                    None,
                                )

                                if wallet:
                                    tx_hash = tx.get("hash")
                                    tx_hash_hex = (
                                        tx_hash.hex()
                                        if hasattr(tx_hash, "hex")
                                        else str(tx_hash)
                                    )

                                    # Check if we've already recorded this deposit
                                    existing_trade = await db.execute(
                                        select(DEXTrade).where(
                                            and_(
                                                DEXTrade.transaction_hash
                                                == tx_hash_hex,
                                                DEXTrade.chain_id == chain_id,
                                            )
                                        )
                                    )
                                    if existing_trade.scalar_one_or_none():
                                        continue  # Already recorded

                                    deposit_amount = Decimal(value) / Decimal(
                                        10**18
                                    )  # Convert from wei

                                    deposits_found.append(
                                        {
                                            "wallet_id": wallet.id,
                                            "user_id": wallet.user_id,
                                            "wallet_address": wallet.wallet_address,
                                            "chain_id": chain_id,
                                            "transaction_hash": tx_hash_hex,
                                            "block_number": block_num,
                                            "amount": float(deposit_amount),
                                            "currency": "ETH",
                                            "from_address": tx.get("from"),
                                            "timestamp": datetime.fromtimestamp(
                                                block.get("timestamp", 0)
                                            ),
                                        }
                                    )

                                    logger.info(
                                        f"Deposit detected: {deposit_amount} ETH to {wallet.wallet_address[:10]}...",
                                        extra={
                                            "wallet_id": wallet.id,
                                            "user_id": wallet.user_id,
                                            "chain_id": chain_id,
                                            "tx_hash": tx_hash_hex,
                                            "amount": str(deposit_amount),
                                        },
                                    )

                except Exception as e:
                    logger.warning(
                        f"Error checking block {block_num} on chain {chain_id}: {e}",
                        extra={"chain_id": chain_id, "block_number": block_num},
                    )
                    continue

            # Update last checked block
            self._last_checked_block[chain_id] = current_block

            logger.info(
                f"Deposit check complete for chain {chain_id}: found {len(deposits_found)} deposits",
                extra={"chain_id": chain_id, "deposits_found": len(deposits_found)},
            )

        except Exception as e:
            logger.error(
                f"Error checking deposits for chain {chain_id}: {e}",
                exc_info=True,
                extra={"chain_id": chain_id},
            )

        return deposits_found

    async def process_deposits(
        self, deposits: List[Dict[str, Any]], db: AsyncSession
    ) -> int:
        """
        Process detected deposits (update balances, notify users)

        Args:
            deposits: List of deposit events
            db: Database session

        Returns:
            Number of deposits processed
        """
        processed = 0

        for deposit in deposits:
            try:
                wallet_id = deposit["wallet_id"]
                chain_id = deposit["chain_id"]
                wallet_address = deposit["wallet_address"]
                amount = deposit["amount"]

                # Update wallet balance
                repository = WalletRepository(db)
                wallet = await db.get(UserWallet, wallet_id)

                # Get wallet from database
                stmt = select(UserWallet).where(UserWallet.id == wallet_id)
                result = await db.execute(stmt)
                wallet = result.scalar_one_or_none()

                if wallet:
                    # Get current balance
                    current_balance = await self.balance_service.get_eth_balance(
                        chain_id, wallet_address, use_cache=False
                    )

                    if current_balance is not None:
                        # Update cached balance in database
                        balance_dict = wallet.balance or {}
                        balance_dict["ETH"] = str(current_balance)
                        await repository.update_wallet_balance(wallet_id, balance_dict)

                        logger.info(
                            f"Updated balance for wallet {wallet_id}: {current_balance} ETH",
                            extra={
                                "wallet_id": wallet_id,
                                "chain_id": chain_id,
                                "balance": str(current_balance),
                            },
                        )

                processed += 1

            except Exception as e:
                logger.error(
                    f"Error processing deposit: {e}",
                    exc_info=True,
                    extra={"deposit": deposit},
                )

        return processed

    async def monitor_all_chains(
        self, db: AsyncSession, supported_chains: List[int] = None
    ) -> Dict[int, int]:
        """
        Monitor deposits on all supported chains

        Args:
            db: Database session
            supported_chains: List of chain IDs to monitor (default: all supported)

        Returns:
            Dictionary mapping chain_id to number of deposits found
        """
        if supported_chains is None:
            supported_chains = [1, 8453, 42161, 137, 10, 43114, 56]  # Default chains

        results = {}

        for chain_id in supported_chains:
            try:
                deposits = await self.check_deposits(chain_id, db)
                if deposits:
                    processed = await self.process_deposits(deposits, db)
                    results[chain_id] = processed
                else:
                    results[chain_id] = 0
            except Exception as e:
                logger.error(
                    f"Error monitoring chain {chain_id}: {e}",
                    exc_info=True,
                    extra={"chain_id": chain_id},
                )
                results[chain_id] = 0

        return results


# Singleton instance
_deposit_monitor: Optional[DepositMonitor] = None


def get_deposit_monitor() -> DepositMonitor:
    """Get singleton DepositMonitor instance"""
    global _deposit_monitor
    if _deposit_monitor is None:
        _deposit_monitor = DepositMonitor()
    return _deposit_monitor
