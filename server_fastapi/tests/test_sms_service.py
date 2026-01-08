"""
Tests for SMS Service
"""

import pytest

from server_fastapi.services.sms_service import sms_service


def test_sms_service_initialization():
    """Test SMS service initializes correctly"""
    assert sms_service is not None
    # Service may be disabled if Twilio credentials not configured
    assert hasattr(sms_service, "enabled")
    assert hasattr(sms_service, "send_sms")


@pytest.mark.asyncio
async def test_sms_service_methods():
    """Test SMS service methods exist"""
    assert hasattr(sms_service, "send_sms")
    assert hasattr(sms_service, "send_verification_code")
    assert hasattr(sms_service, "send_trade_notification")
    assert hasattr(sms_service, "send_security_alert")
