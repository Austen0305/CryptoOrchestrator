"""
Transaction Monitoring Service
Tracks all wallet transactions, success rates, latency, and suspicious patterns
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
from decimal import Decimal

logger = logging.getLogger(__name__)


class TransactionMonitor:
    """Service for monitoring blockchain transactions"""

    def __init__(self):
        # In-memory storage (would use Redis/database in production)
        self._transactions: Dict[str, Dict[str, Any]] = {}
        self._transaction_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "pending": 0,
                "total_amount": Decimal("0"),
                "total_gas": Decimal("0"),
                "avg_latency": 0.0,
                "latencies": [],
            }
        )
        self._suspicious_patterns: List[Dict[str, Any]] = []

    async def track_transaction(
        self,
        transaction_hash: str,
        chain_id: int,
        transaction_type: str,  # 'deposit', 'withdrawal', 'swap'
        user_id: int,
        amount: Optional[Decimal] = None,
        token_address: Optional[str] = None,
        from_address: Optional[str] = None,
        to_address: Optional[str] = None,
        status: str = "pending",  # 'pending', 'confirmed', 'failed'
        gas_used: Optional[int] = None,
        block_number: Optional[int] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Track a transaction for monitoring

        Args:
            transaction_hash: Transaction hash
            chain_id: Blockchain ID
            transaction_type: Type of transaction
            user_id: User ID
            amount: Transaction amount
            token_address: Token address (if ERC-20)
            from_address: Source address
            to_address: Destination address
            status: Transaction status
            gas_used: Gas used
            block_number: Block number
            timestamp: Transaction timestamp
        """
        try:
            transaction = {
                "transaction_hash": transaction_hash,
                "chain_id": chain_id,
                "transaction_type": transaction_type,
                "user_id": user_id,
                "amount": str(amount) if amount else None,
                "token_address": token_address,
                "from_address": from_address,
                "to_address": to_address,
                "status": status,
                "gas_used": gas_used,
                "block_number": block_number,
                "timestamp": timestamp or datetime.utcnow(),
                "created_at": datetime.utcnow(),
            }

            self._transactions[transaction_hash] = transaction

            # Update statistics
            chain_key = f"chain_{chain_id}"
            type_key = f"{transaction_type}_{chain_id}"

            stats = self._transaction_stats[chain_key]
            type_stats = self._transaction_stats[type_key]

            stats["total"] += 1
            type_stats["total"] += 1

            if status == "confirmed":
                stats["successful"] += 1
                type_stats["successful"] += 1
            elif status == "failed":
                stats["failed"] += 1
                type_stats["failed"] += 1
            else:
                stats["pending"] += 1
                type_stats["pending"] += 1

            if amount:
                stats["total_amount"] += amount
                type_stats["total_amount"] += amount

            if gas_used:
                stats["total_gas"] += Decimal(str(gas_used))
                type_stats["total_gas"] += Decimal(str(gas_used))

            logger.debug(
                f"Tracked transaction: {transaction_hash[:10]}... ({transaction_type}, {status})",
                extra={
                    "transaction_hash": transaction_hash,
                    "chain_id": chain_id,
                    "type": transaction_type,
                    "user_id": user_id,
                },
            )

        except Exception as e:
            logger.error(f"Error tracking transaction: {e}", exc_info=True)

    async def update_transaction_status(
        self,
        transaction_hash: str,
        status: str,
        gas_used: Optional[int] = None,
        block_number: Optional[int] = None,
        latency_seconds: Optional[float] = None,
    ) -> None:
        """
        Update transaction status and calculate latency

        Args:
            transaction_hash: Transaction hash
            status: New status ('confirmed', 'failed')
            gas_used: Gas used
            block_number: Block number
            latency_seconds: Time taken for transaction (seconds)
        """
        try:
            if transaction_hash not in self._transactions:
                logger.warning(
                    f"Transaction not found for update: {transaction_hash[:10]}..."
                )
                return

            transaction = self._transactions[transaction_hash]
            old_status = transaction["status"]
            chain_id = transaction["chain_id"]
            transaction_type = transaction["transaction_type"]

            # Update transaction
            transaction["status"] = status
            if gas_used:
                transaction["gas_used"] = gas_used
            if block_number:
                transaction["block_number"] = block_number
            transaction["updated_at"] = datetime.utcnow()

            # Calculate latency if provided
            if latency_seconds is not None:
                transaction["latency_seconds"] = latency_seconds

                # Update average latency
                chain_key = f"chain_{chain_id}"
                type_key = f"{transaction_type}_{chain_id}"

                for stats_key in [chain_key, type_key]:
                    stats = self._transaction_stats[stats_key]
                    stats["latencies"].append(latency_seconds)
                    # Keep only last 100 latencies for rolling average
                    if len(stats["latencies"]) > 100:
                        stats["latencies"] = stats["latencies"][-100:]
                    stats["avg_latency"] = (
                        sum(stats["latencies"]) / len(stats["latencies"])
                        if stats["latencies"]
                        else 0.0
                    )

            # Update statistics
            if old_status == "pending":
                chain_key = f"chain_{chain_id}"
                type_key = f"{transaction_type}_{chain_id}"

                for stats_key in [chain_key, type_key]:
                    stats = self._transaction_stats[stats_key]
                    stats["pending"] -= 1

                    if status == "confirmed":
                        stats["successful"] += 1
                    elif status == "failed":
                        stats["failed"] += 1

            logger.debug(
                f"Updated transaction status: {transaction_hash[:10]}... -> {status}",
                extra={
                    "transaction_hash": transaction_hash,
                    "old_status": old_status,
                    "new_status": status,
                },
            )

        except Exception as e:
            logger.error(f"Error updating transaction status: {e}", exc_info=True)

    async def get_transaction_stats(
        self,
        chain_id: Optional[int] = None,
        transaction_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get transaction statistics

        Args:
            chain_id: Filter by chain ID
            transaction_type: Filter by transaction type
            start_date: Start date filter
            end_date: End date filter

        Returns:
            Statistics dictionary
        """
        try:
            # Filter transactions
            filtered = list(self._transactions.values())

            if chain_id:
                filtered = [t for t in filtered if t["chain_id"] == chain_id]

            if transaction_type:
                filtered = [
                    t for t in filtered if t["transaction_type"] == transaction_type
                ]

            if start_date:
                filtered = [t for t in filtered if t["timestamp"] >= start_date]

            if end_date:
                filtered = [t for t in filtered if t["timestamp"] <= end_date]

            # Calculate stats
            total = len(filtered)
            successful = len([t for t in filtered if t["status"] == "confirmed"])
            failed = len([t for t in filtered if t["status"] == "failed"])
            pending = len([t for t in filtered if t["status"] == "pending"])

            total_amount = sum(
                Decimal(t["amount"])
                for t in filtered
                if t["amount"] and t["status"] == "confirmed"
            )

            total_gas = sum(
                Decimal(str(t["gas_used"]))
                for t in filtered
                if t["gas_used"] and t["status"] == "confirmed"
            )

            latencies = [
                t.get("latency_seconds")
                for t in filtered
                if t.get("latency_seconds") is not None
            ]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

            success_rate = (successful / total * 100) if total > 0 else 0.0

            return {
                "total": total,
                "successful": successful,
                "failed": failed,
                "pending": pending,
                "success_rate": round(success_rate, 2),
                "total_amount": str(total_amount),
                "total_gas": str(total_gas),
                "avg_latency_seconds": round(avg_latency, 2),
                "chain_id": chain_id,
                "transaction_type": transaction_type,
                "period": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None,
                },
            }

        except Exception as e:
            logger.error(f"Error getting transaction stats: {e}", exc_info=True)
            return {}

    async def detect_suspicious_patterns(
        self,
        user_id: Optional[int] = None,
        chain_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect suspicious transaction patterns

        Args:
            user_id: Filter by user ID
            chain_id: Filter by chain ID

        Returns:
            List of suspicious patterns detected
        """
        try:
            suspicious = []

            # Filter transactions
            filtered = list(self._transactions.values())
            if user_id:
                filtered = [t for t in filtered if t["user_id"] == user_id]
            if chain_id:
                filtered = [t for t in filtered if t["chain_id"] == chain_id]

            # Pattern 1: Unusual frequency (many transactions in short time)
            user_tx_counts: Dict[int, int] = defaultdict(int)
            for tx in filtered:
                if tx["timestamp"] > datetime.utcnow() - timedelta(hours=1):
                    user_tx_counts[tx["user_id"]] += 1

            for user_id_check, count in user_tx_counts.items():
                if count > 20:  # Threshold
                    suspicious.append(
                        {
                            "pattern": "high_frequency",
                            "user_id": user_id_check,
                            "count": count,
                            "period": "1 hour",
                            "severity": "medium",
                            "description": f"User {user_id_check} made {count} transactions in the last hour",
                        }
                    )

            # Pattern 2: Unusual amounts (very large or very small)
            for tx in filtered:
                if tx["amount"]:
                    amount = Decimal(tx["amount"])
                    # Very large amount (> 1000 ETH equivalent)
                    if amount > Decimal("1000"):
                        suspicious.append(
                            {
                                "pattern": "large_amount",
                                "transaction_hash": tx["transaction_hash"],
                                "user_id": tx["user_id"],
                                "amount": str(amount),
                                "severity": "high",
                                "description": f"Large transaction detected: {amount}",
                            }
                        )
                    # Very small amount (< 0.0001)
                    elif (
                        amount < Decimal("0.0001")
                        and tx["transaction_type"] == "withdrawal"
                    ):
                        suspicious.append(
                            {
                                "pattern": "dust_withdrawal",
                                "transaction_hash": tx["transaction_hash"],
                                "user_id": tx["user_id"],
                                "amount": str(amount),
                                "severity": "low",
                                "description": f"Very small withdrawal: {amount}",
                            }
                        )

            # Pattern 3: Failed transactions pattern
            user_failures: Dict[int, int] = defaultdict(int)
            for tx in filtered:
                if tx["status"] == "failed" and tx[
                    "timestamp"
                ] > datetime.utcnow() - timedelta(hours=24):
                    user_failures[tx["user_id"]] += 1

            for user_id_check, failure_count in user_failures.items():
                if failure_count > 5:  # Threshold
                    suspicious.append(
                        {
                            "pattern": "high_failure_rate",
                            "user_id": user_id_check,
                            "failure_count": failure_count,
                            "period": "24 hours",
                            "severity": "medium",
                            "description": f"User {user_id_check} has {failure_count} failed transactions in 24 hours",
                        }
                    )

            self._suspicious_patterns.extend(suspicious)

            return suspicious

        except Exception as e:
            logger.error(f"Error detecting suspicious patterns: {e}", exc_info=True)
            return []

    async def generate_report(
        self,
        start_date: datetime,
        end_date: datetime,
        chain_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate transaction monitoring report

        Args:
            start_date: Report start date
            end_date: Report end date
            chain_id: Filter by chain ID

        Returns:
            Report dictionary
        """
        try:
            stats = await self.get_transaction_stats(
                chain_id=chain_id,
                start_date=start_date,
                end_date=end_date,
            )

            suspicious = await self.detect_suspicious_patterns(chain_id=chain_id)

            # Per-chain breakdown
            chain_breakdown = {}
            for tx in self._transactions.values():
                if start_date <= tx["timestamp"] <= end_date:
                    if chain_id and tx["chain_id"] != chain_id:
                        continue

                    chain_key = str(tx["chain_id"])
                    if chain_key not in chain_breakdown:
                        chain_breakdown[chain_key] = {
                            "total": 0,
                            "successful": 0,
                            "failed": 0,
                            "pending": 0,
                        }

                    chain_breakdown[chain_key]["total"] += 1
                    if tx["status"] == "confirmed":
                        chain_breakdown[chain_key]["successful"] += 1
                    elif tx["status"] == "failed":
                        chain_breakdown[chain_key]["failed"] += 1
                    else:
                        chain_breakdown[chain_key]["pending"] += 1

            return {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "summary": stats,
                "chain_breakdown": chain_breakdown,
                "suspicious_patterns": suspicious,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating transaction report: {e}", exc_info=True)
            return {}


# Global transaction monitor instance
transaction_monitor = TransactionMonitor()
