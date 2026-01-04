"""
Transaction Service
Execute blockchain transactions with signing and monitoring
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

# Defensive imports to prevent route loading failures if web3 is not installed
try:
    from web3 import AsyncWeb3
    from web3.exceptions import Web3Exception, TransactionNotFound
    from eth_account import Account
    from eth_account.signers.local import LocalAccount
    from hexbytes import HexBytes
    WEB3_AVAILABLE = True
except ImportError as e:
    WEB3_AVAILABLE = False
    AsyncWeb3 = None
    Web3Exception = Exception
    TransactionNotFound = Exception
    Account = None
    LocalAccount = None
    HexBytes = None
    logger = logging.getLogger(__name__)
    logger.warning(f"Web3 not available: {e}. Transaction service will be limited.")

from .web3_service import get_web3_service
from ...config.settings import get_settings

if 'logger' not in locals():
    logger = logging.getLogger(__name__)


class TransactionService:
    """Service for executing blockchain transactions"""

    def __init__(self):
        self.settings = get_settings()
        if not WEB3_AVAILABLE:
            logger.warning("Web3 not available - TransactionService will have limited functionality")
        try:
            self.web3_service = get_web3_service()
        except Exception as e:
            logger.warning(f"Failed to initialize web3 service: {e}")
            self.web3_service = None

    async def estimate_gas(
        self,
        chain_id: int,
        transaction: Dict[str, Any],
    ) -> Optional[int]:
        """
        Estimate gas for a transaction

        Args:
            chain_id: Blockchain chain ID
            transaction: Transaction dictionary

        Returns:
            Estimated gas or None if error
        """
        try:
            w3 = await self.web3_service.get_connection(chain_id)
            if not w3:
                return None

            gas = await w3.eth.estimate_gas(transaction)
            return gas

        except Web3Exception as e:
            logger.error(f"Error estimating gas: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error estimating gas: {e}", exc_info=True)
            return None

    async def get_gas_price(
        self, chain_id: int, priority: str = "standard"
    ) -> Optional[Dict[str, Any]]:
        """
        Get current gas price with EIP-1559 support and priority levels

        Args:
            chain_id: Blockchain chain ID
            priority: Priority level ("slow", "standard", "fast")

        Returns:
            Dictionary with gas price information or None if error
            Format: {
                "gas_price": int (for legacy chains),
                "max_fee_per_gas": int (for EIP-1559),
                "max_priority_fee_per_gas": int (for EIP-1559),
                "priority": str
            }
        """
        try:
            w3 = await self.web3_service.get_connection(chain_id)
            if not w3:
                return None

            # Try to get EIP-1559 fee structure (for Ethereum mainnet and most L2s)
            try:
                # Get latest block to check if EIP-1559 is supported
                latest_block = await w3.eth.get_block("latest")

                if "baseFeePerGas" in latest_block:
                    # EIP-1559 is supported
                    base_fee = latest_block["baseFeePerGas"]

                    # Get fee history for better estimation
                    try:
                        fee_history = await w3.eth.fee_history(1, "latest")
                        if fee_history and fee_history.get("baseFeePerGas"):
                            base_fee = fee_history["baseFeePerGas"][0]
                    except Exception:
                        pass  # Fallback to block base fee

                    # Calculate priority fees based on priority level
                    priority_multipliers = {
                        "slow": 0.1,
                        "standard": 0.2,
                        "fast": 0.5,
                    }
                    multiplier = priority_multipliers.get(priority, 0.2)
                    max_priority_fee = int(base_fee * multiplier)
                    max_fee_per_gas = base_fee + max_priority_fee

                    return {
                        "gas_price": None,  # Not used for EIP-1559
                        "max_fee_per_gas": max_fee_per_gas,
                        "max_priority_fee_per_gas": max_priority_fee,
                        "priority": priority,
                        "base_fee": base_fee,
                    }
            except Exception:
                # Fallback to legacy gas price
                pass

            # Legacy gas price (for chains without EIP-1559)
            gas_price = await w3.eth.gas_price

            # Apply priority multiplier for legacy chains
            priority_multipliers = {
                "slow": 0.9,
                "standard": 1.0,
                "fast": 1.2,
            }
            multiplier = priority_multipliers.get(priority, 1.0)
            adjusted_gas_price = int(gas_price * multiplier)

            return {
                "gas_price": adjusted_gas_price,
                "max_fee_per_gas": None,
                "max_priority_fee_per_gas": None,
                "priority": priority,
            }

        except Web3Exception as e:
            logger.error(f"Error getting gas price: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting gas price: {e}", exc_info=True)
            return None

    async def get_transaction_count(self, chain_id: int, address: str) -> Optional[int]:
        """
        Get transaction count (nonce) for an address

        Args:
            chain_id: Blockchain chain ID
            address: Ethereum address

        Returns:
            Transaction count (nonce) or None if error
        """
        try:
            w3 = await self.web3_service.get_connection(chain_id)
            if not w3:
                return None

            address = self.web3_service.normalize_address(address)
            if not address:
                return None

            nonce = await w3.eth.get_transaction_count(address)
            return nonce

        except Web3Exception as e:
            logger.error(f"Error getting transaction count: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error getting transaction count: {e}", exc_info=True
            )
            return None

    async def sign_and_send_transaction(
        self,
        chain_id: int,
        private_key: str,
        transaction: Dict[str, Any],
        use_mev_protection: bool = False,
        trade_amount_usd: Optional[float] = None,
    ) -> Optional[str]:
        """
        Sign and send a transaction with optional MEV protection

        Args:
            chain_id: Blockchain chain ID
            private_key: Private key (hex string, 0x-prefixed)
            transaction: Transaction dictionary (to, value, data, gas, gasPrice, nonce)
            use_mev_protection: If True, send through MEV-protected RPC
            trade_amount_usd: Trade amount in USD (for auto-determining MEV protection)

        Returns:
            Transaction hash (hex string) or None if error

        Note: In production, private keys should be retrieved from secure key management
        (AWS KMS, HashiCorp Vault) rather than passed as parameters.
        """
        try:
            # Determine if MEV protection should be used
            if trade_amount_usd is not None and not use_mev_protection:
                from .mev_protection import get_mev_protection_service

                mev_service = get_mev_protection_service()
                use_mev_protection = await mev_service.should_use_mev_protection(
                    trade_amount_usd=trade_amount_usd, chain_id=chain_id
                )

            # Get Web3 connection (with MEV protection if enabled)
            if use_mev_protection:
                from .mev_protection import (
                    get_mev_protection_service,
                    MEVProtectionProvider,
                )
                from web3 import AsyncWeb3
                from web3.providers.async_rpc import AsyncHTTPProvider

                mev_service = get_mev_protection_service()
                protected_rpc = await mev_service.get_protected_rpc_url(
                    chain_id, MEVProtectionProvider.MEV_BLOCKER
                )

                if protected_rpc:
                    # Create temporary Web3 connection with protected RPC
                    protected_provider = AsyncHTTPProvider(protected_rpc)
                    w3 = AsyncWeb3(protected_provider)
                    logger.info(
                        f"Using MEV-protected RPC for transaction on chain {chain_id}",
                        extra={
                            "chain_id": chain_id,
                            "protected_rpc": protected_rpc,
                            "trade_amount_usd": trade_amount_usd,
                        },
                    )
                else:
                    # Fallback to regular connection
                    w3 = await self.web3_service.get_connection(chain_id)
                    logger.warning(
                        f"MEV protection requested but not available for chain {chain_id}, "
                        f"using regular RPC"
                    )
            else:
                w3 = await self.web3_service.get_connection(chain_id)

            if not w3:
                logger.error(f"No Web3 connection for chain {chain_id}")
                return None

            # Create account from private key
            account: LocalAccount = Account.from_key(private_key)

            # Ensure transaction has required fields
            if "chainId" not in transaction:
                transaction["chainId"] = chain_id

            if "from" not in transaction:
                transaction["from"] = account.address

            if "nonce" not in transaction:
                nonce = await self.get_transaction_count(chain_id, account.address)
                if nonce is None:
                    logger.error("Could not get transaction count")
                    return None
                transaction["nonce"] = nonce

            if "gasPrice" not in transaction:
                gas_price = await self.get_gas_price(chain_id)
                if gas_price is None:
                    logger.error("Could not get gas price")
                    return None
                transaction["gasPrice"] = gas_price

            if "gas" not in transaction:
                # Estimate gas
                gas = await self.estimate_gas(chain_id, transaction)
                if gas is None:
                    logger.error("Could not estimate gas")
                    return None
                # Add 20% buffer
                transaction["gas"] = int(gas * 1.2)

            # Sign transaction
            signed_txn = account.sign_transaction(transaction)

            # Send transaction
            tx_hash = await w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            logger.info(
                f"Transaction sent: {tx_hash.hex()}",
                extra={
                    "chain_id": chain_id,
                    "from": account.address,
                    "to": transaction.get("to"),
                    "tx_hash": tx_hash.hex(),
                    "mev_protection": use_mev_protection,
                    "trade_amount_usd": trade_amount_usd,
                },
            )

            return tx_hash.hex()

        except Web3Exception as e:
            logger.error(f"Web3 error sending transaction: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error sending transaction: {e}", exc_info=True)
            return None

    async def get_transaction_receipt(
        self, chain_id: int, tx_hash: str, timeout: int = 300
    ) -> Optional[Dict[str, Any]]:
        """
        Get transaction receipt, waiting for confirmation

        Args:
            chain_id: Blockchain chain ID
            tx_hash: Transaction hash (hex string)
            timeout: Maximum time to wait in seconds

        Returns:
            Transaction receipt dictionary or None if error/timeout
        """
        try:
            w3 = await self.web3_service.get_connection(chain_id)
            if not w3:
                return None

            # Convert hex string to bytes if needed
            if isinstance(tx_hash, str):
                if tx_hash.startswith("0x"):
                    tx_hash_bytes = HexBytes(tx_hash)
                else:
                    tx_hash_bytes = HexBytes("0x" + tx_hash)
            else:
                tx_hash_bytes = tx_hash

            # Wait for transaction receipt
            receipt = await w3.eth.wait_for_transaction_receipt(
                tx_hash_bytes, timeout=timeout
            )

            # Convert to dict for easier handling
            receipt_dict = {
                "transactionHash": receipt["transactionHash"].hex(),
                "blockNumber": receipt["blockNumber"],
                "blockHash": receipt["blockHash"].hex(),
                "status": receipt["status"],  # 1 = success, 0 = failure
                "gasUsed": receipt["gasUsed"],
                "effectiveGasPrice": receipt.get(
                    "effectiveGasPrice", receipt.get("gasPrice", 0)
                ),
                "from": receipt["from"],
                "to": receipt.get("to"),
                "logs": [log.hex() for log in receipt.get("logs", [])],
            }

            logger.info(
                f"Transaction receipt received: {tx_hash}",
                extra={
                    "chain_id": chain_id,
                    "tx_hash": tx_hash,
                    "status": receipt_dict["status"],
                    "block_number": receipt_dict["blockNumber"],
                },
            )

            return receipt_dict

        except TransactionNotFound:
            logger.warning(f"Transaction not found: {tx_hash}")
            return None
        except Web3Exception as e:
            logger.error(f"Web3 error getting transaction receipt: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error getting transaction receipt: {e}", exc_info=True)
            return None

    async def monitor_transaction(
        self,
        chain_id: int,
        tx_hash: str,
        timeout: int = 300,
        poll_interval: int = 2,
    ) -> Optional[Dict[str, Any]]:
        """
        Monitor transaction until confirmed or timeout with exponential backoff

        Args:
            chain_id: Blockchain chain ID
            tx_hash: Transaction hash
            timeout: Maximum time to wait in seconds (default: 5 minutes)
            poll_interval: Initial polling interval in seconds (default: 2 seconds)

        Returns:
            Transaction receipt dictionary or None if error/timeout
        """
        import asyncio
        from datetime import datetime

        start_time = datetime.now()
        current_interval = poll_interval
        max_interval = 30  # Cap polling interval at 30 seconds

        while True:
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout:
                logger.warning(
                    f"Transaction monitoring timeout after {timeout}s: {tx_hash}",
                    extra={"chain_id": chain_id, "tx_hash": tx_hash},
                )
                return None

            # Check transaction status
            status = await self.get_transaction_status(chain_id, tx_hash)

            if status:
                if status.get("status") == "confirmed":
                    # Get full receipt
                    receipt = await self.get_transaction_receipt(
                        chain_id, tx_hash, timeout=10
                    )
                    return receipt
                elif status.get("status") == "failed":
                    logger.error(
                        f"Transaction failed: {tx_hash}",
                        extra={"chain_id": chain_id, "tx_hash": tx_hash},
                    )
                    return {
                        "status": "failed",
                        "tx_hash": tx_hash,
                        "chain_id": chain_id,
                    }

            # Wait before next poll with exponential backoff
            await asyncio.sleep(current_interval)
            current_interval = min(
                current_interval * 1.5, max_interval
            )  # Exponential backoff, capped

    async def get_transaction_status(
        self, chain_id: int, tx_hash: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get transaction status without waiting

        Args:
            chain_id: Blockchain chain ID
            tx_hash: Transaction hash

        Returns:
            Transaction status dictionary with status: "pending", "confirmed", or "failed"
        """
        try:
            w3 = await self.web3_service.get_connection(chain_id)
            if not w3:
                return None

            # Convert hex string to bytes if needed
            if isinstance(tx_hash, str):
                if tx_hash.startswith("0x"):
                    tx_hash_bytes = HexBytes(tx_hash)
                else:
                    tx_hash_bytes = HexBytes("0x" + tx_hash)
            else:
                tx_hash_bytes = tx_hash

            # Try to get receipt (transaction may not be mined yet)
            try:
                receipt = await w3.eth.get_transaction_receipt(tx_hash_bytes)
                return {
                    "status": "confirmed",
                    "success": receipt["status"] == 1,
                    "blockNumber": receipt["blockNumber"],
                    "gasUsed": receipt["gasUsed"],
                    "tx_hash": tx_hash,
                }
            except TransactionNotFound:
                # Transaction not yet mined, check if it exists in mempool
                try:
                    tx = await w3.eth.get_transaction(tx_hash_bytes)
                    return {
                        "status": "pending",
                        "success": None,
                        "blockNumber": None,
                        "gasUsed": None,
                    }
                except TransactionNotFound:
                    return {
                        "status": "not_found",
                        "success": None,
                        "blockNumber": None,
                        "gasUsed": None,
                    }

        except Web3Exception as e:
            logger.error(f"Web3 error getting transaction status: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error getting transaction status: {e}", exc_info=True)
            return None


# Singleton instance
_transaction_service: Optional[TransactionService] = None


def get_transaction_service() -> TransactionService:
    """Get singleton TransactionService instance"""
    global _transaction_service
    if _transaction_service is None:
        _transaction_service = TransactionService()
    return _transaction_service
