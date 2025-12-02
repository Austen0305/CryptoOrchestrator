"""
Audit logging middleware for security and compliance.
Logs all sensitive operations for audit trails.
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import os

logger = logging.getLogger(__name__)

# Configure audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Create audit log file handler
if not audit_logger.handlers:
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    audit_handler = logging.FileHandler(
        os.path.join(log_dir, "audit.log"),
        encoding="utf-8"
    )
    audit_handler.setLevel(logging.INFO)
    
    # Format: timestamp | level | user_id | action | details
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    audit_handler.setFormatter(formatter)
    audit_logger.addHandler(audit_handler)


class AuditLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log security-sensitive operations for audit trails.
    """
    
    # Endpoints that require audit logging
    AUDIT_ENDPOINTS = {
        "POST": ["/api/auth/login", "/api/auth/register", "/api/auth/logout"],
        "PUT": ["/api/bots/", "/api/trades/"],
        "DELETE": ["/api/bots/", "/api/trades/"],
        "PATCH": ["/api/bots/", "/api/preferences/"],
    }
    
    # Sensitive data fields to mask in logs
    SENSITIVE_FIELDS = {
        "password", "passwordHash", "secret", "api_key", "api_secret",
        "token", "access_token", "refresh_token", "authorization"
    }
    
    def _should_audit(self, method: str, path: str) -> bool:
        """Check if endpoint requires audit logging."""
        if method in self.AUDIT_ENDPOINTS:
            for pattern in self.AUDIT_ENDPOINTS[method]:
                if pattern in path:
                    return True
        return False
    
    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive fields in log data."""
        if not isinstance(data, dict):
            return data
        
        masked = {}
        for key, value in data.items():
            if key.lower() in self.SENSITIVE_FIELDS:
                masked[key] = "***MASKED***"
            elif isinstance(value, dict):
                masked[key] = self._mask_sensitive_data(value)
            elif isinstance(value, list):
                masked[key] = [
                    self._mask_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked[key] = value
        
        return masked
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request."""
        # Try to get user from JWT token
        auth_header = request.headers.get("authorization")
        if auth_header:
            try:
                import jwt
                token = auth_header.replace("Bearer ", "")
                # Decode without verification (we just need user ID for logging)
                payload = jwt.decode(token, options={"verify_signature": False})
                return str(payload.get("id") or payload.get("user_id") or "unknown")
            except Exception:
                pass
        
        # Try to get from request state (if set by auth middleware)
        if hasattr(request.state, "user"):
            user = request.state.user
            return str(user.get("id") or user.get("user_id", "unknown"))
        
        return "anonymous"
    
    async def dispatch(self, request: Request, call_next):
        """Process request and log audit events."""
        start_time = datetime.now()
        method = request.method
        path = request.url.path
        
        # Check if we should audit this request
        should_audit = self._should_audit(method, path)
        
        user_id = self._get_user_id(request)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log request details if audit required
        if should_audit:
            try:
                body = await request.body()
                request._body = body  # Restore body for endpoint processing
                
                # Parse request body (if JSON)
                body_data = {}
                if body:
                    try:
                        body_data = json.loads(body.decode())
                        body_data = self._mask_sensitive_data(body_data)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        body_data = {"raw": "***NON_JSON_DATA***"}
                
                audit_logger.info(
                    json.dumps({
                        "event": "request_started",
                        "user_id": user_id,
                        "method": method,
                        "path": path,
                        "ip": client_ip,
                        "user_agent": user_agent,
                        "body": body_data,
                        "timestamp": start_time.isoformat()
                    })
                )
            except Exception as e:
                logger.error(f"Error logging audit request: {e}")
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error
            if should_audit:
                audit_logger.error(
                    json.dumps({
                        "event": "request_failed",
                        "user_id": user_id,
                        "method": method,
                        "path": path,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                )
            raise
        
        # Log response if audit required
        if should_audit:
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            audit_logger.info(
                json.dumps({
                    "event": "request_completed",
                    "user_id": user_id,
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "timestamp": end_time.isoformat()
                })
            )
        
        return response


def log_audit_event(
    event_type: str,
    user_id: Optional[str],
    action: str,
    details: Dict[str, Any],
    severity: str = "info"
):
    """
    Log a custom audit event.
    
    Args:
        event_type: Type of event (e.g., "auth", "trading", "admin")
        user_id: User ID performing the action
        action: Description of the action
        details: Additional details about the event
        severity: Log level (info, warning, error, critical)
    """
    log_level = getattr(logging, severity.upper(), logging.INFO)
    
    audit_logger.log(
        log_level,
        json.dumps({
            "event_type": event_type,
            "user_id": user_id or "system",
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    )

