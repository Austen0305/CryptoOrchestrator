"""
Audit Logger Service
Logs all sensitive operations, especially real-money trades
Includes hash chaining for tamper prevention
"""

import logging
import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Audit log directory
AUDIT_LOG_DIR = Path("logs")
AUDIT_LOG_DIR.mkdir(exist_ok=True)

AUDIT_LOG_FILE = AUDIT_LOG_DIR / "audit.log"
AUDIT_HASH_FILE = AUDIT_LOG_DIR / "audit.hash"  # Stores hash chain


class AuditLogger:
    """
    Service for logging audit events, especially real-money trades.
    Implements hash chaining for tamper prevention.
    """

    def __init__(self):
        # Set up audit file handler (append-only mode)
        self.audit_handler = logging.FileHandler(AUDIT_LOG_FILE, mode="a")
        self.audit_handler.setLevel(logging.INFO)
        self.audit_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        # Create audit logger
        self.audit_logger = logging.getLogger("audit")
        self.audit_logger.addHandler(self.audit_handler)
        self.audit_logger.setLevel(logging.INFO)
        self.audit_logger.propagate = False

        # Initialize hash chain
        self.previous_hash = self._load_previous_hash()

    def _load_previous_hash(self) -> str:
        """Load previous hash from hash chain file"""
        if AUDIT_HASH_FILE.exists():
            try:
                with open(AUDIT_HASH_FILE, "r") as f:
                    return f.read().strip()
            except Exception as e:
                logger.warning(f"Failed to load previous hash: {e}")
                return ""
        return ""

    def _calculate_hash(self, data: str, previous_hash: str = "") -> str:
        """Calculate hash for audit log entry with chaining"""
        # Combine previous hash with current entry for chaining
        combined = f"{previous_hash}{data}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def _append_to_hash_chain(self, entry_hash: str) -> None:
        """Append hash to hash chain file (append-only)"""
        try:
            with open(AUDIT_HASH_FILE, "a") as f:
                f.write(f"{entry_hash}\n")
        except Exception as e:
            logger.error(f"Failed to append to hash chain: {e}")

    def _verify_hash_chain(self) -> bool:
        """Verify integrity of audit log hash chain"""
        if not AUDIT_HASH_FILE.exists():
            return True  # No hash chain yet

        try:
            with open(AUDIT_HASH_FILE, "r") as f:
                hashes = [line.strip() for line in f.readlines() if line.strip()]

            # Recalculate hashes from audit log
            if not AUDIT_LOG_FILE.exists():
                return True

            calculated_hash = ""
            log_entries = []
            with open(AUDIT_LOG_FILE, "r") as f:
                for line in f:
                    if line.strip():
                        # Parse log line to extract JSON message
                        try:
                            parts = line.split(" - ", 3)
                            if len(parts) >= 4:
                                message = parts[3].strip()
                                log_entries.append(message)
                                calculated_hash = self._calculate_hash(
                                    message, calculated_hash
                                )
                        except Exception:
                            # Skip malformed lines but still calculate hash
                            calculated_hash = self._calculate_hash(
                                line.strip(), calculated_hash
                            )

            # Verify hash chain integrity
            if not hashes:
                return True  # No hashes stored yet

            # Verify each hash in chain
            chain_hash = ""
            for i, log_entry in enumerate(log_entries):
                chain_hash = self._calculate_hash(log_entry, chain_hash)
                if i < len(hashes):
                    if hashes[i] != chain_hash:
                        logger.critical(
                            f"Audit log hash chain mismatch at entry {i} - possible tampering!"
                        )
                        return False

            # Verify last hash matches
            if hashes and hashes[-1] == calculated_hash:
                return True
            else:
                logger.critical(
                    "Audit log hash chain verification failed - possible tampering!"
                )
                return False

        except Exception as e:
            logger.error(f"Hash chain verification error: {e}")
            return False

    async def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify audit log integrity and return detailed results

        Returns:
            Dict with verification results
        """
        is_valid = self._verify_hash_chain()

        # Get log statistics
        log_size = AUDIT_LOG_FILE.stat().st_size if AUDIT_LOG_FILE.exists() else 0
        hash_count = 0
        if AUDIT_HASH_FILE.exists():
            with open(AUDIT_HASH_FILE, "r") as f:
                hash_count = len([line for line in f if line.strip()])

        return {
            "integrity_verified": is_valid,
            "log_file_size": log_size,
            "hash_chain_length": hash_count,
            "last_verified": datetime.utcnow().isoformat(),
            "tampering_detected": not is_valid,
        }

    def log_trade(
        self,
        user_id: int,
        trade_id: str,
        chain_id: int,  # Changed from exchange to chain_id
        symbol: str,
        side: str,
        amount: float,
        price: float,
        mode: str,
        order_id: Optional[str] = None,
        transaction_hash: Optional[str] = None,  # Blockchain transaction hash
        bot_id: Optional[str] = None,
        mfa_used: bool = False,
        risk_checks_passed: bool = True,
        success: bool = True,
        error: Optional[str] = None,
        **kwargs,
    ):
        """Log a trade execution for audit purposes"""
        audit_event = {
            "event_type": "trade_execution",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": f"execute_trade_{side}",
            "resource_type": "trade",
            "resource_id": trade_id,
            "trade_id": trade_id,
            "chain_id": chain_id,  # Changed from exchange
            "transaction_hash": transaction_hash,
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "price": price,
            "cost": amount * price,
            "mode": mode,
            "order_id": order_id,
            "bot_id": bot_id,
            "mfa_used": mfa_used,
            "risk_checks_passed": risk_checks_passed,
            "status": "success" if success else "failure",
            "success": success,
            "error": error,
            "details": {
                "chain_id": chain_id,  # Changed from exchange
                "transaction_hash": transaction_hash,
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "price": price,
                "mode": mode,
                "order_id": order_id,
                "bot_id": bot_id,
            },
            **kwargs,
        }

        # Log to audit log file with hash chaining
        log_entry = json.dumps(audit_event)
        self.audit_logger.info(log_entry)

        # Calculate and store hash for tamper prevention
        entry_hash = self._calculate_hash(log_entry, self.previous_hash)
        self._append_to_hash_chain(entry_hash)
        self.previous_hash = entry_hash

        # Also log to main logger for real-money trades
        if mode == "real":
            logger.warning(
                f"REAL MONEY TRADE: user={user_id}, chain_id={chain_id}, "
                f"symbol={symbol}, side={side}, amount={amount}, price={price}, "
                f"transaction_hash={transaction_hash}, order_id={order_id}, success={success}"
            )

    def log_api_key_operation(
        self,
        user_id: int,
        operation: str,  # 'create', 'update', 'delete', 'validate'
        exchange: str,
        success: bool = True,
        error: Optional[str] = None,
        **kwargs,
    ):
        """Log API key operations for audit"""
        audit_event = {
            "event_type": "api_key_operation",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": f"{operation}_api_key",
            "resource_type": "exchange_api_key",
            "resource_id": exchange,
            "operation": operation,
            "exchange": exchange,
            "status": "success" if success else "failure",
            "success": success,
            "error_message": error,
            "details": {"operation": operation, "exchange": exchange, **kwargs},
            **kwargs,
        }

        # Log with hash chaining
        log_entry = json.dumps(audit_event)
        self.audit_logger.info(log_entry)
        entry_hash = self._calculate_hash(log_entry, self.previous_hash)
        self._append_to_hash_chain(entry_hash)
        self.previous_hash = entry_hash

        # Warn for sensitive operations
        if operation in ("delete", "create"):
            logger.warning(
                f"API KEY OPERATION: user={user_id}, operation={operation}, "
                f"exchange={exchange}, success={success}"
            )

    def log_mode_switch(
        self,
        user_id: int,
        from_mode: str,
        to_mode: str,
        requirements_met: bool = True,
        **kwargs,
    ):
        """Log trading mode switches"""
        audit_event = {
            "event_type": "mode_switch",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": "switch_trading_mode",
            "resource_type": "trading_mode",
            "resource_id": to_mode,
            "from_mode": from_mode,
            "to_mode": to_mode,
            "requirements_met": requirements_met,
            "status": "success" if requirements_met else "failure",
            "details": {
                "from_mode": from_mode,
                "to_mode": to_mode,
                "requirements_met": requirements_met,
                **kwargs,
            },
            **kwargs,
        }

        # Log with hash chaining
        log_entry = json.dumps(audit_event)
        self.audit_logger.info(log_entry)
        entry_hash = self._calculate_hash(log_entry, self.previous_hash)
        self._append_to_hash_chain(entry_hash)
        self.previous_hash = entry_hash

        # Warn if switching to real money
        if to_mode == "real":
            logger.warning(
                f"USER SWITCHED TO REAL MONEY: user={user_id}, "
                f"requirements_met={requirements_met}"
            )

    def log_risk_event(
        self,
        user_id: int,
        event_type: str,  # 'limit_exceeded', 'emergency_stop', 'risk_check_failed'
        details: Dict[str, Any],
        **kwargs,
    ):
        """Log risk management events"""
        audit_event = {
            "event_type": "risk_event",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "risk_event_type": event_type,
            "details": details,
            **kwargs,
        }

        self.audit_logger.warning(json.dumps(audit_event))
        logger.warning(
            f"RISK EVENT: user={user_id}, type={event_type}, details={details}"
        )

    def log_security_event(
        self,
        user_id: int,
        event_type: str,  # 'failed_login', 'unauthorized_access', 'suspicious_activity'
        details: Dict[str, Any],
        **kwargs,
    ):
        """Log security-related events"""
        audit_event = {
            "event_type": "security_event",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "security_event_type": event_type,
            "details": details,
            **kwargs,
        }

        self.audit_logger.warning(json.dumps(audit_event))
        logger.warning(
            f"SECURITY EVENT: user={user_id}, type={event_type}, details={details}"
        )

    def log_wallet_operation(
        self,
        user_id: int,
        operation: str,  # 'create', 'deposit', 'withdraw', 'balance_refresh', 'register_external'
        wallet_id: Optional[int] = None,
        wallet_type: Optional[str] = None,
        chain_id: Optional[int] = None,
        amount: Optional[float] = None,
        token_address: Optional[str] = None,
        transaction_hash: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None,
        **kwargs,
    ):
        """Log wallet operations for audit"""
        audit_event = {
            "event_type": "wallet_operation",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": f"{operation}_wallet",
            "resource_type": "wallet",
            "resource_id": wallet_id,
            "operation": operation,
            "wallet_id": wallet_id,
            "wallet_type": wallet_type,
            "chain_id": chain_id,
            "amount": amount,
            "token_address": token_address,
            "transaction_hash": transaction_hash,
            "status": "success" if success else "failure",
            "success": success,
            "error": error,
            "details": {
                "operation": operation,
                "wallet_id": wallet_id,
                "wallet_type": wallet_type,
                "chain_id": chain_id,
                "amount": amount,
                "token_address": token_address,
                "transaction_hash": transaction_hash,
                **kwargs,
            },
            **kwargs,
        }

        # Log with hash chaining
        log_entry = json.dumps(audit_event)
        self.audit_logger.info(log_entry)
        entry_hash = self._calculate_hash(log_entry, self.previous_hash)
        self._append_to_hash_chain(entry_hash)
        self.previous_hash = entry_hash

        # Warn for sensitive operations
        if operation in ("withdraw", "deposit") and success:
            logger.warning(
                f"WALLET OPERATION: user={user_id}, operation={operation}, "
                f"wallet_id={wallet_id}, chain_id={chain_id}, amount={amount}, "
                f"transaction_hash={transaction_hash}, success={success}"
            )

    def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve audit logs with filtering"""
        logs = []

        try:
            if not AUDIT_LOG_FILE.exists():
                return logs

            with open(AUDIT_LOG_FILE, "r") as f:
                for line in f:
                    try:
                        # Parse log line (format: timestamp - logger - level - message)
                        parts = line.split(" - ", 3)
                        if len(parts) < 4:
                            continue

                        timestamp_str = parts[0]
                        message = parts[3].strip()

                        # Parse JSON message
                        log_entry = json.loads(message)

                        # Apply filters
                        if user_id and log_entry.get("user_id") != user_id:
                            continue
                        if event_type and log_entry.get("event_type") != event_type:
                            continue
                        if start_date:
                            log_timestamp = datetime.fromisoformat(
                                log_entry.get("timestamp", "")
                            )
                            if log_timestamp < start_date:
                                continue
                        if end_date:
                            log_timestamp = datetime.fromisoformat(
                                log_entry.get("timestamp", "")
                            )
                            if log_timestamp > end_date:
                                continue

                        logs.append(log_entry)

                        if len(logs) >= limit:
                            break
                    except (json.JSONDecodeError, ValueError) as e:
                        # Skip invalid log lines
                        continue

            # Sort by timestamp (newest first)
            logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        except Exception as e:
            logger.error(f"Failed to read audit logs: {e}")

        return logs

    def export_audit_logs(
        self,
        user_id: Optional[int] = None,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "json",  # 'json' or 'csv'
    ) -> str:
        """
        Export audit logs to JSON or CSV format

        Returns:
            File path to exported logs
        """
        try:
            logs = self.get_audit_logs(
                user_id=user_id,
                event_type=event_type,
                start_date=start_date,
                end_date=end_date,
                limit=10000,  # Large limit for export
            )

            export_dir = AUDIT_LOG_DIR / "exports"
            export_dir.mkdir(exist_ok=True)

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"audit_logs_{timestamp}.{format}"
            filepath = export_dir / filename

            if format == "json":
                import json

                with open(filepath, "w") as f:
                    json.dump(logs, f, indent=2)
            elif format == "csv":
                import csv

                if logs:
                    fieldnames = set()
                    for log in logs:
                        fieldnames.update(log.keys())

                    with open(filepath, "w", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                        writer.writeheader()
                        writer.writerows(logs)

            logger.info(f"Exported {len(logs)} audit logs to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error exporting audit logs: {e}", exc_info=True)
            raise

    def cleanup_old_logs(self, retention_days: int = 90):
        """
        Clean up audit logs older than retention period

        Args:
            retention_days: Number of days to retain logs (default: 90)
        """
        try:
            if not AUDIT_LOG_FILE.exists():
                return

            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            cutoff_timestamp = cutoff_date.isoformat()

            # Read all logs
            with open(AUDIT_LOG_FILE, "r") as f:
                lines = f.readlines()

            # Filter logs to keep
            kept_lines = []
            removed_count = 0

            for line in lines:
                try:
                    parts = line.split(" - ", 3)
                    if len(parts) < 4:
                        kept_lines.append(line)
                        continue

                    message = parts[3].strip()
                    log_entry = json.loads(message)
                    log_timestamp = log_entry.get("timestamp", "")

                    if log_timestamp >= cutoff_timestamp:
                        kept_lines.append(line)
                    else:
                        removed_count += 1
                except Exception:
                    # Keep lines that can't be parsed
                    kept_lines.append(line)

            # Write back kept logs
            with open(AUDIT_LOG_FILE, "w") as f:
                f.writelines(kept_lines)

            logger.info(
                f"Cleaned up {removed_count} old audit log entries (retention: {retention_days} days)"
            )

        except Exception as e:
            logger.error(f"Error cleaning up audit logs: {e}", exc_info=True)


# Global audit logger instance
audit_logger = AuditLogger()
