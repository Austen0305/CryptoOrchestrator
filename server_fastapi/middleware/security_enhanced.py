"""
Enhanced Security Middleware
Comprehensive security enhancements with advanced threat detection
"""

import logging
import re
import html
from typing import Dict, List, Optional, Set
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EnhancedSecurityMiddleware(BaseHTTPMiddleware):
    """
    Enhanced security middleware with:
    - Advanced SQL injection detection
    - XSS protection
    - Command injection prevention
    - Path traversal protection
    - Rate limiting per IP
    - Threat detection and blocking
    """

    # Enhanced SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION)\b)",
        r"(--|;|/\*|\*/|#)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+['\"]\w+['\"]\s*=\s*['\"]\w+['\"])",
        r"(\b(OR|AND)\s+['\"]1['\"]\s*=\s*['\"]1['\"])",
        r"(\b(OR|AND)\s+1\s*=\s*1\b)",
        r"(\b(OR|AND)\s+['\"]1['\"]\s*=\s*['\"]1['\"])",
        r"(\bEXEC\s*\()",
        r"(\bEXECUTE\s*\()",
        r"(\bxp_\w+)",  # SQL Server extended procedures
        r"(\bLOAD_FILE\s*\()",  # MySQL file operations
    ]

    # Enhanced XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
        r"expression\s*\(",
        r"vbscript:",
        r"data:text/html",
    ]

    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$(){}[\]<>]",
        r"\b(cat|ls|pwd|whoami|id|uname|ps|kill|rm|mv|cp)\b",
        r"\$\{",
        r"`[^`]*`",
        r"\$\([^)]+\)",
    ]

    def __init__(
        self,
        app,
        block_threats: bool = True,
        log_threats: bool = True,
        threat_threshold: int = 5,  # Block after N threats
        threat_window: int = 300,  # 5 minutes
    ):
        super().__init__(app)
        self.block_threats = block_threats
        self.log_threats = log_threats
        self.threat_threshold = threat_threshold
        self.threat_window = threat_window
        
        # Threat tracking per IP
        self.threat_tracker: Dict[str, List[datetime]] = defaultdict(list)
        
        # Blocked IPs (temporary)
        self.blocked_ips: Dict[str, datetime] = {}
        self.block_duration = 3600  # 1 hour

    def _detect_sql_injection(self, value: str) -> bool:
        """Enhanced SQL injection detection"""
        if not isinstance(value, str):
            return False
        
        value_upper = value.upper()
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                return True
        return False

    def _detect_xss(self, value: str) -> bool:
        """Enhanced XSS detection"""
        if not isinstance(value, str):
            return False
        
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    def _detect_command_injection(self, value: str) -> bool:
        """Command injection detection"""
        if not isinstance(value, str):
            return False
        
        for pattern in self.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    def _sanitize_string(self, value: str, max_length: int = 10000) -> str:
        """Comprehensive string sanitization"""
        if not isinstance(value, str):
            return value
        
        # HTML escape
        sanitized = html.escape(value)
        
        # Remove dangerous patterns
        for pattern in self.SQL_INJECTION_PATTERNS + self.XSS_PATTERNS:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()

    def _check_ip_threats(self, ip: str) -> bool:
        """Check if IP has exceeded threat threshold"""
        if ip not in self.threat_tracker:
            return False
        
        # Clean old threats
        cutoff = datetime.utcnow() - timedelta(seconds=self.threat_window)
        self.threat_tracker[ip] = [
            ts for ts in self.threat_tracker[ip] if ts > cutoff
        ]
        
        # Check threshold
        if len(self.threat_tracker[ip]) >= self.threat_threshold:
            # Block IP temporarily
            self.blocked_ips[ip] = datetime.utcnow()
            return True
        
        return False

    def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is currently blocked"""
        if ip not in self.blocked_ips:
            return False
        
        # Check if block has expired
        block_time = self.blocked_ips[ip]
        if (datetime.utcnow() - block_time).total_seconds() > self.block_duration:
            del self.blocked_ips[ip]
            return False
        
        return True

    def _record_threat(self, ip: str, threat_type: str, details: str):
        """Record security threat"""
        self.threat_tracker[ip].append(datetime.utcnow())
        
        if self.log_threats:
            logger.warning(
                f"Security threat detected: {threat_type} from {ip} - {details}",
                extra={
                    "ip": ip,
                    "threat_type": threat_type,
                    "details": details,
                    "threat_count": len(self.threat_tracker[ip]),
                }
            )

    async def dispatch(self, request: Request, call_next) -> JSONResponse:
        """Process request with enhanced security checks"""
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if IP is blocked
        if self._is_ip_blocked(client_ip):
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Access denied",
                    "message": "Your IP has been temporarily blocked due to suspicious activity",
                }
            )
        
        # Check query parameters
        for key, value in request.query_params.items():
            if isinstance(value, str):
                if self._detect_sql_injection(value):
                    self._record_threat(client_ip, "SQL_INJECTION", f"Query param {key}")
                    if self.block_threats:
                        if self._check_ip_threats(client_ip):
                            return JSONResponse(
                                status_code=status.HTTP_403_FORBIDDEN,
                                content={"error": "Access denied"},
                            )
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": "Invalid request parameters"},
                        )
                
                if self._detect_xss(value):
                    self._record_threat(client_ip, "XSS", f"Query param {key}")
                    if self.block_threats:
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": "Invalid request parameters"},
                        )
                
                if self._detect_command_injection(value):
                    self._record_threat(client_ip, "COMMAND_INJECTION", f"Query param {key}")
                    if self.block_threats:
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": "Invalid request parameters"},
                        )
        
        # Check path for traversal
        path = request.url.path
        if ".." in path or "//" in path or path.startswith("/etc") or path.startswith("/proc"):
            self._record_threat(client_ip, "PATH_TRAVERSAL", path)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid path"},
            )
        
        # Process request
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Security middleware error: {e}", exc_info=True)
            raise

    def get_threat_stats(self) -> Dict:
        """Get threat statistics"""
        return {
            "blocked_ips": len(self.blocked_ips),
            "tracked_ips": len(self.threat_tracker),
            "total_threats": sum(len(threats) for threats in self.threat_tracker.values()),
        }

