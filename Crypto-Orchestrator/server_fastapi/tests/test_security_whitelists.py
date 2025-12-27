"""
Tests for Security Whitelist Services
"""

import pytest

from server_fastapi.services.security.ip_whitelist_service import ip_whitelist_service
from server_fastapi.services.security.withdrawal_whitelist_service import (
    withdrawal_whitelist_service,
)


def test_ip_whitelist_service_initialization():
    """Test IP whitelist service initializes correctly"""
    assert ip_whitelist_service is not None


def test_withdrawal_whitelist_service_initialization():
    """Test withdrawal whitelist service initializes correctly"""
    assert withdrawal_whitelist_service is not None
    assert withdrawal_whitelist_service.cooldown_hours == 24
