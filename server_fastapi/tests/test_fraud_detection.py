"""
Tests for Fraud Detection Service
"""

import pytest

from server_fastapi.services.fraud_detection.fraud_detection_service import (
    fraud_detection_service,
)


@pytest.mark.asyncio
async def test_fraud_detection_service_initialization():
    """Test fraud detection service initializes correctly"""
    assert fraud_detection_service is not None
    assert fraud_detection_service.risk_threshold == 0.7
    assert fraud_detection_service.max_transactions_per_hour == 50


@pytest.mark.asyncio
async def test_analyze_transaction_basic():
    """Test basic transaction analysis"""
    # This would require a database session
    # For now, just verify service is accessible
    assert hasattr(fraud_detection_service, "analyze_transaction")
    assert hasattr(fraud_detection_service, "get_user_risk_profile")


def test_time_anomaly_check():
    """Test time anomaly detection"""
    result = fraud_detection_service._check_time_anomaly()
    assert isinstance(result, dict)
    assert "is_suspicious" in result
    assert "message" in result
