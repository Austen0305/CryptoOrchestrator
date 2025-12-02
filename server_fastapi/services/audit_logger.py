"""
Comprehensive Audit Logging System
Tracks all critical user actions and system events for compliance
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    # User actions
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_REGISTER = "user.register"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    
    # Trading actions
    ORDER_CREATE = "order.create"
    ORDER_CANCEL = "order.cancel"
    ORDER_EXECUTE = "order.execute"
    
    # Bot actions
    BOT_CREATE = "bot.create"
    BOT_START = "bot.start"
    BOT_STOP = "bot.stop"
    BOT_UPDATE = "bot.update"
    BOT_DELETE = "bot.delete"
    
    # Security actions
    API_KEY_CREATE = "apikey.create"
    API_KEY_REVOKE = "apikey.revoke"
    PASSWORD_CHANGE = "password.change"
    TWOFACTOR_ENABLE = "2fa.enable"
    TWOFACTOR_DISABLE = "2fa.disable"
    
    # Admin actions
    SETTINGS_CHANGE = "settings.change"
    PERMISSION_GRANT = "permission.grant"
    PERMISSION_REVOKE = "permission.revoke"
    
    # System events
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    RATE_LIMIT_EXCEEDED = "system.rate_limit"


class AuditEntry(BaseModel):
    timestamp: datetime
    action: AuditAction
    user_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    status: str  # "success", "failure"
    error_message: Optional[str]


class AuditLogger:
    """
    Centralized audit logging system for compliance and security
    """
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Create audit log handler
        handler = logging.FileHandler("logs/audit.log")
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(message)s')
        )
        self.logger.addHandler(handler)
    
    async def log(
        self,
        action: AuditAction,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ):
        """Log an audit entry"""
        entry = AuditEntry(
            timestamp=datetime.now(),
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            status=status,
            error_message=error_message
        )
        
        # Log to file
        self.logger.info(json.dumps(entry.dict(), default=str))
        
        # Also log to database for querying
        await self._save_to_database(entry)
    
    async def _save_to_database(self, entry: AuditEntry):
        """Save audit entry to database"""
        try:
            from database.connection_pool import db_pool
            
            if db_pool:
                async with db_pool.get_session() as session:
                    # Create audit log table entry
                    await session.execute(
                        """
                        INSERT INTO audit_logs 
                        (timestamp, action, user_id, ip_address, user_agent, 
                         resource_type, resource_id, details, status, error_message)
                        VALUES (:timestamp, :action, :user_id, :ip_address, :user_agent,
                                :resource_type, :resource_id, :details, :status, :error_message)
                        """,
                        {
                            "timestamp": entry.timestamp,
                            "action": entry.action.value,
                            "user_id": entry.user_id,
                            "ip_address": entry.ip_address,
                            "user_agent": entry.user_agent,
                            "resource_type": entry.resource_type,
                            "resource_id": entry.resource_id,
                            "details": json.dumps(entry.details) if entry.details else None,
                            "status": entry.status,
                            "error_message": entry.error_message
                        }
                    )
                    await session.commit()
        except Exception as e:
            logger.error(f"Failed to save audit log to database: {e}")


# Global audit logger instance
audit_logger = AuditLogger()


# Helper functions for common audit actions
async def audit_user_login(user_id: str, ip_address: str, user_agent: str, success: bool = True):
    """Audit user login attempt"""
    await audit_logger.log(
        action=AuditAction.USER_LOGIN,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        status="success" if success else "failure"
    )


async def audit_order_create(user_id: str, order_id: str, details: Dict, ip_address: str):
    """Audit order creation"""
    await audit_logger.log(
        action=AuditAction.ORDER_CREATE,
        user_id=user_id,
        resource_type="order",
        resource_id=order_id,
        details=details,
        ip_address=ip_address,
        status="success"
    )


async def audit_bot_action(action: AuditAction, user_id: str, bot_id: str, ip_address: str):
    """Audit bot-related actions"""
    await audit_logger.log(
        action=action,
        user_id=user_id,
        resource_type="bot",
        resource_id=bot_id,
        ip_address=ip_address,
        status="success"
    )


async def audit_security_event(action: AuditAction, user_id: str, details: Dict, ip_address: str):
    """Audit security-related events"""
    await audit_logger.log(
        action=action,
        user_id=user_id,
        details=details,
        ip_address=ip_address,
        status="success"
    )
