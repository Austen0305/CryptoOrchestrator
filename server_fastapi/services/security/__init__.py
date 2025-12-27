"""
Security services module
"""

from .security_event_alerting import (
    SecurityEventAlertingService,
    get_security_event_alerting_service,
)

__all__ = [
    "SecurityEventAlertingService",
    "get_security_event_alerting_service",
]
