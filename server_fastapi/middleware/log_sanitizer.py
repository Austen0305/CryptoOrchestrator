"""
Log Sanitizer Middleware
Sanitizes log messages to prevent sensitive data leakage
"""

import re
import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class LogSanitizer:
    """Utility class for sanitizing sensitive data in logs"""
    
    # Sensitive patterns to mask
    SENSITIVE_PATTERNS = {
        'password': r'password["\s]*[:=]["\s]*([^"\s,}]+)',
        'api_key': r'api[_-]?key["\s]*[:=]["\s]*([^"\s,}]+)',
        'api_secret': r'api[_-]?secret["\s]*[:=]["\s]*([^"\s,}]+)',
        'secret': r'secret["\s]*[:=]["\s]*([^"\s,}]+)',
        'token': r'token["\s]*[:=]["\s]*([^"\s,}]+)',
        'authorization': r'authorization["\s]*[:=]["\s]*([^"\s,}]+)',
        'jwt': r'jwt["\s]*[:=]["\s]*([^"\s,}]+)',
        'access_token': r'access[_-]?token["\s]*[:=]["\s]*([^"\s,}]+)',
        'refresh_token': r'refresh[_-]?token["\s]*[:=]["\s]*([^"\s,}]+)',
        'passphrase': r'passphrase["\s]*[:=]["\s]*([^"\s,}]+)',
    }
    
    # Sensitive field names (case-insensitive)
    SENSITIVE_FIELDS = {
        'password', 'passwordhash', 'passwd', 'pwd',
        'api_key', 'apikey', 'api_secret', 'apisecret',
        'secret', 'secretkey', 'secret_key',
        'token', 'accesstoken', 'access_token',
        'refreshtoken', 'refresh_token',
        'authorization', 'auth', 'authorization_header',
        'jwt', 'jwttoken', 'jwt_token',
        'passphrase', 'passphrase_encrypted',
        'encryption_key', 'encryptionkey',
        'private_key', 'privatekey',
    }
    
    @staticmethod
    def sanitize_string(text: str, mask: str = "***MASKED***") -> str:
        """
        Sanitize a string by masking sensitive patterns
        
        Args:
            text: String to sanitize
            mask: Replacement string for sensitive data
            
        Returns:
            Sanitized string
        """
        if not isinstance(text, str):
            return text
            
        sanitized = text
        
        # Mask sensitive patterns
        for pattern_name, pattern in LogSanitizer.SENSITIVE_PATTERNS.items():
            sanitized = re.sub(
                pattern,
                lambda m: f'{m.group(0).split("=")[0].split(":")[0]}={mask}',
                sanitized,
                flags=re.IGNORECASE
            )
        
        # Mask common JWT token patterns (Bearer tokens, etc.)
        sanitized = re.sub(
            r'(Bearer|Token|Authorization)\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+',
            r'\1 ' + mask,
            sanitized,
            flags=re.IGNORECASE
        )
        
        # Mask long strings that look like keys/tokens (32+ chars)
        sanitized = re.sub(
            r'(["\']?[a-zA-Z0-9+/=]{32,}["\']?)',
            lambda m: mask if len(m.group(1)) > 31 else m.group(1),
            sanitized
        )
        
        return sanitized
    
    @staticmethod
    def sanitize_dict(data: Dict[str, Any], mask: str = "***MASKED***") -> Dict[str, Any]:
        """
        Sanitize a dictionary by masking sensitive fields
        
        Args:
            data: Dictionary to sanitize
            mask: Replacement value for sensitive data
            
        Returns:
            Sanitized dictionary
        """
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if key is sensitive
            if any(sensitive in key_lower for sensitive in LogSanitizer.SENSITIVE_FIELDS):
                sanitized[key] = mask
            elif isinstance(value, dict):
                sanitized[key] = LogSanitizer.sanitize_dict(value, mask)
            elif isinstance(value, list):
                sanitized[key] = LogSanitizer.sanitize_list(value, mask)
            elif isinstance(value, str):
                # Sanitize string values that might contain sensitive data
                sanitized[key] = LogSanitizer.sanitize_string(value, mask)
            else:
                sanitized[key] = value
        
        return sanitized
    
    @staticmethod
    def sanitize_list(data: List[Any], mask: str = "***MASKED***") -> List[Any]:
        """
        Sanitize a list by recursively sanitizing items
        
        Args:
            data: List to sanitize
            mask: Replacement value for sensitive data
            
        Returns:
            Sanitized list
        """
        if not isinstance(data, list):
            return data
        
        return [
            LogSanitizer.sanitize_dict(item, mask) if isinstance(item, dict)
            else LogSanitizer.sanitize_list(item, mask) if isinstance(item, list)
            else LogSanitizer.sanitize_string(item, mask) if isinstance(item, str)
            else item
            for item in data
        ]
    
    @staticmethod
    def sanitize_error_message(error: Exception, mask: str = "***MASKED***") -> str:
        """
        Sanitize error message to prevent sensitive data leakage
        
        Args:
            error: Exception object
            mask: Replacement string for sensitive data
            
        Returns:
            Sanitized error message
        """
        error_msg = str(error)
        return LogSanitizer.sanitize_string(error_msg, mask)
    
    @staticmethod
    def safe_log(level: int, message: str, *args, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Safely log a message with automatic sanitization
        
        Args:
            level: Logging level (logging.INFO, logging.ERROR, etc.)
            message: Log message (will be sanitized)
            *args: Additional positional arguments
            extra: Extra fields to log (will be sanitized)
            **kwargs: Additional keyword arguments
        """
        # Sanitize message
        sanitized_message = LogSanitizer.sanitize_string(message)
        
        # Sanitize extra fields
        sanitized_extra = LogSanitizer.sanitize_dict(extra or {})
        
        # Log with sanitized data
        logger.log(level, sanitized_message, *args, extra=sanitized_extra, **kwargs)


def sanitize_log_message(func):
    """
    Decorator to automatically sanitize log messages
    
    Usage:
        @sanitize_log_message
        def some_function():
            logger.info("Password: secret123")  # Will log "Password: ***MASKED***"
    """
    def wrapper(*args, **kwargs):
        # If the first argument is a string (log message), sanitize it
        if args and isinstance(args[0], str):
            args = (LogSanitizer.sanitize_string(args[0]),) + args[1:]
        
        # Sanitize kwargs that might contain sensitive data
        sanitized_kwargs = LogSanitizer.sanitize_dict(kwargs)
        
        return func(*args, **sanitized_kwargs)
    
    return wrapper

