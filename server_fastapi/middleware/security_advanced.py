"""
Advanced Security Enhancements
Provides additional security features beyond basic middleware
"""

import hashlib
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class SecurityThreatDetector:
    """
    Advanced threat detection

    Features:
    - SQL injection detection
    - XSS detection
    - Command injection detection
    - Path traversal detection
    - Rate limiting per IP
    - Suspicious pattern detection
    """

    def __init__(self):
        # SQL injection patterns
        self.sql_patterns = [
            r"(?i)(union\s+select|select\s+.*\s+from|insert\s+into|delete\s+from|update\s+.*\s+set|drop\s+table|exec\s*\(|execute\s*\(|--|;|(?<!\*)/\*|\*/)",
            r"(?i)(or\s+1\s*=\s*1|or\s+'1'\s*=\s*'1'|or\s+\"1\"\s*=\s*\"1\")",
            r"(?i)(';?\s*(drop|delete|insert|update|create|alter|exec|execute))",
        ]

        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
        ]

        # Command injection patterns
        self.command_patterns = [
            r"[;&|`$(){}[\]]",
            r"(?i)(cat\s+|ls\s+|pwd|whoami|id|uname|ps\s+aux|netstat|ifconfig)",
            r"(?i)(rm\s+-|del\s+|rmdir|mkdir)",
        ]

        # Path traversal patterns
        self.path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"\.\.%2f",
            r"\.\.%5c",
            r"%2e%2e%2f",
            r"%2e%2e%5c",
        ]

        # Threat tracking
        self.threats: dict[str, list[datetime]] = {}
        self.blocked_ips: set[str] = set()
        self.threat_threshold = 5  # Block after 5 threats
        self.threat_window = timedelta(minutes=5)

    def detect_threats(self, request: Request) -> list[str]:
        """Detect security threats in request"""
        threats = []

        # Check URL path
        path_threats = self._check_path(request.url.path)
        threats.extend(path_threats)

        # Check query parameters
        for key, value in request.query_params.items():
            param_threats = self._check_value(f"query.{key}", value)
            threats.extend(param_threats)

        # Check headers (except auth and common metadata headers)
        for key, value in request.headers.items():
            if key.lower() not in [
                "authorization",
                "cookie",
                "x-api-key",
                "accept",
                "user-agent",
                "referer",
            ]:
                header_threats = self._check_value(f"header.{key}", value)
                threats.extend(header_threats)

        return threats

    def _check_path(self, path: str) -> list[str]:
        """Check path for threats"""
        threats = []

        # SQL injection
        for pattern in self.sql_patterns:
            if re.search(pattern, path):
                threats.append("sql_injection")

        # Path traversal
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, path):
                threats.append("path_traversal")

        # Command injection
        for pattern in self.command_patterns:
            if re.search(pattern, path):
                threats.append("command_injection")

        return threats

    def _check_value(self, field: str, value: str) -> list[str]:
        """Check value for threats"""
        threats = []

        if not isinstance(value, str):
            return threats

        # SQL injection
        for pattern in self.sql_patterns:
            if re.search(pattern, value):
                threats.append(f"sql_injection:{field}")

        # XSS
        for pattern in self.xss_patterns:
            if re.search(pattern, value):
                threats.append(f"xss:{field}")

        # Command injection
        for pattern in self.command_patterns:
            if re.search(pattern, value):
                threats.append(f"command_injection:{field}")

        return threats

    def record_threat(self, ip: str, threat_type: str):
        """Record a security threat"""
        if ip not in self.threats:
            self.threats[ip] = []

        self.threats[ip].append(datetime.utcnow())

        # Clean old threats
        cutoff = datetime.utcnow() - self.threat_window
        self.threats[ip] = [t for t in self.threats[ip] if t > cutoff]

        # Check if should block
        if len(self.threats[ip]) >= self.threat_threshold:
            self.blocked_ips.add(ip)
            logger.warning(f"IP {ip} blocked due to {len(self.threats[ip])} threats")

    def is_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        return ip in self.blocked_ips

    def unblock(self, ip: str):
        """Unblock an IP address"""
        self.blocked_ips.discard(ip)
        if ip in self.threats:
            del self.threats[ip]


class APIKeyManager:
    """API key management and validation"""

    def __init__(self):
        self.keys: dict[str, dict[str, Any]] = {}
        self.key_usage: dict[str, list[datetime]] = {}

    def generate_key(self, user_id: str, permissions: list[str]) -> str:
        """Generate API key"""
        key_data = f"{user_id}:{time.time()}:{permissions}"
        api_key = hashlib.sha256(key_data.encode()).hexdigest()

        self.keys[api_key] = {
            "user_id": user_id,
            "permissions": permissions,
            "created_at": datetime.utcnow(),
            "last_used": None,
            "usage_count": 0,
        }

        return api_key

    def validate_key(self, api_key: str) -> dict[str, Any] | None:
        """Validate API key"""
        if api_key not in self.keys:
            return None

        key_info = self.keys[api_key]
        key_info["last_used"] = datetime.utcnow()
        key_info["usage_count"] += 1

        # Track usage
        if api_key not in self.key_usage:
            self.key_usage[api_key] = []
        self.key_usage[api_key].append(datetime.utcnow())

        return key_info

    def revoke_key(self, api_key: str):
        """Revoke API key"""
        if api_key in self.keys:
            del self.keys[api_key]
        if api_key in self.key_usage:
            del self.key_usage[api_key]


class AdvancedSecurityMiddleware(BaseHTTPMiddleware):
    """Advanced security middleware"""

    def __init__(self, app):
        super().__init__(app)
        self.threat_detector = SecurityThreatDetector()
        self.api_key_manager = APIKeyManager()

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with advanced security"""
        # Skip security checks for health endpoints and internal requests
        # Normalize path by removing trailing slash for comparison
        normalized_path = request.url.path.rstrip("/") or "/"
        health_paths = [
            "/health",
            "/healthz",
            "/api/health",
            "/api/status",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]
        if normalized_path in health_paths:
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Allow localhost/127.0.0.1 for health checks
        if client_ip in ["127.0.0.1", "localhost", "::1"]:
            return await call_next(request)

        # Check if IP is blocked
        if self.threat_detector.is_blocked(client_ip):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="IP address has been blocked due to security threats",
            )

        # Detect threats
        threats = self.threat_detector.detect_threats(request)

        if threats:
            # Record threat
            for threat in threats:
                self.threat_detector.record_threat(client_ip, threat)

            # Block if threshold exceeded
            if self.threat_detector.is_blocked(client_ip):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Request blocked due to security threats",
                )

            # Log threat
            logger.warning(
                f"Security threat detected from {client_ip}: {threats}",
                extra={"ip": client_ip, "threats": threats, "path": request.url.path},
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request contains potentially malicious content",
            )

        # Validate API key if present
        api_key = request.headers.get("X-API-Key")
        if api_key:
            key_info = self.api_key_manager.validate_key(api_key)
            if not key_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                )
            # Store in request state
            request.state.api_key_info = key_info

        # Process request
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response


# Global instances
threat_detector = SecurityThreatDetector()
api_key_manager = APIKeyManager()
