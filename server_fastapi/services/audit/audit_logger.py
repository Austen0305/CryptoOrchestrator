"""
Audit Logger Service
Logs all sensitive operations, especially real-money trades
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Audit log directory
AUDIT_LOG_DIR = Path("logs")
AUDIT_LOG_DIR.mkdir(exist_ok=True)

AUDIT_LOG_FILE = AUDIT_LOG_DIR / "audit.log"


class AuditLogger:
    """Service for logging audit events, especially real-money trades"""
    
    def __init__(self):
        # Set up audit file handler
        self.audit_handler = logging.FileHandler(AUDIT_LOG_FILE)
        self.audit_handler.setLevel(logging.INFO)
        self.audit_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
        
        # Create audit logger
        self.audit_logger = logging.getLogger('audit')
        self.audit_logger.addHandler(self.audit_handler)
        self.audit_logger.setLevel(logging.INFO)
        self.audit_logger.propagate = False
    
    def log_trade(
        self,
        user_id: int,
        trade_id: str,
        exchange: str,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        mode: str,
        order_id: Optional[str] = None,
        bot_id: Optional[str] = None,
        mfa_used: bool = False,
        risk_checks_passed: bool = True,
        success: bool = True,
        error: Optional[str] = None,
        **kwargs
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
            "exchange": exchange,
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
                "exchange": exchange,
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "price": price,
                "mode": mode,
                "order_id": order_id,
                "bot_id": bot_id,
            },
            **kwargs
        }
        
        # Log to audit log file
        self.audit_logger.info(json.dumps(audit_event))
        
        # Also log to main logger for real-money trades
        if mode == "real":
            logger.warning(
                f"REAL MONEY TRADE: user={user_id}, exchange={exchange}, "
                f"symbol={symbol}, side={side}, amount={amount}, price={price}, "
                f"order_id={order_id}, success={success}"
            )
    
    def log_api_key_operation(
        self,
        user_id: int,
        operation: str,  # 'create', 'update', 'delete', 'validate'
        exchange: str,
        success: bool = True,
        error: Optional[str] = None,
        **kwargs
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
            "details": {
                "operation": operation,
                "exchange": exchange,
                **kwargs
            },
            **kwargs
        }
        
        self.audit_logger.info(json.dumps(audit_event))
        
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
        **kwargs
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
                **kwargs
            },
            **kwargs
        }
        
        self.audit_logger.info(json.dumps(audit_event))
        
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
        **kwargs
    ):
        """Log risk management events"""
        audit_event = {
            "event_type": "risk_event",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "risk_event_type": event_type,
            "details": details,
            **kwargs
        }
        
        self.audit_logger.warning(json.dumps(audit_event))
        logger.warning(f"RISK EVENT: user={user_id}, type={event_type}, details={details}")
    
    def log_security_event(
        self,
        user_id: int,
        event_type: str,  # 'failed_login', 'unauthorized_access', 'suspicious_activity'
        details: Dict[str, Any],
        **kwargs
    ):
        """Log security-related events"""
        audit_event = {
            "event_type": "security_event",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "security_event_type": event_type,
            "details": details,
            **kwargs
        }
        
        self.audit_logger.warning(json.dumps(audit_event))
        logger.warning(f"SECURITY EVENT: user={user_id}, type={event_type}, details={details}")
    
    def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve audit logs with filtering"""
        logs = []
        
        try:
            if not AUDIT_LOG_FILE.exists():
                return logs
            
            with open(AUDIT_LOG_FILE, 'r') as f:
                for line in f:
                    try:
                        # Parse log line (format: timestamp - logger - level - message)
                        parts = line.split(' - ', 3)
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
                            log_timestamp = datetime.fromisoformat(log_entry.get("timestamp", ""))
                            if log_timestamp < start_date:
                                continue
                        if end_date:
                            log_timestamp = datetime.fromisoformat(log_entry.get("timestamp", ""))
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


# Global audit logger instance
audit_logger = AuditLogger()

