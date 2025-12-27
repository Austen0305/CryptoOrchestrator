"""
Tests for Analytics Threshold Notification System
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from server_fastapi.models.analytics_threshold import (
    AnalyticsThreshold,
    ThresholdType,
    ThresholdMetric,
    ThresholdOperator,
)
from server_fastapi.models.signal_provider import SignalProvider, CuratorStatus
from server_fastapi.models.user import User
from server_fastapi.services.marketplace_threshold_service import MarketplaceThresholdService


pytestmark = pytest.mark.asyncio


class TestAnalyticsThresholdModel:
    """Tests for AnalyticsThreshold model"""

    async def test_create_threshold(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test creating an analytics threshold"""
        threshold = AnalyticsThreshold(
            user_id=test_user.id,
            threshold_type=ThresholdType.PROVIDER.value,
            metric=ThresholdMetric.TOTAL_RETURN.value,
            operator=ThresholdOperator.LESS_THAN.value,
            threshold_value=-10.0,
            context={"provider_id": 1},
            enabled=True,
            notification_channels={"email": True, "push": True},
            cooldown_minutes=60,
            name="Low Return Alert",
            description="Alert when total return drops below -10%",
        )
        
        db_session.add(threshold)
        await db_session.commit()
        await db_session.refresh(threshold)
        
        assert threshold.id is not None
        assert threshold.user_id == test_user.id
        assert threshold.threshold_type == ThresholdType.PROVIDER.value
        assert threshold.metric == ThresholdMetric.TOTAL_RETURN.value
        assert threshold.enabled is True

    async def test_threshold_cooldown(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test threshold cooldown functionality"""
        threshold = AnalyticsThreshold(
            user_id=test_user.id,
            threshold_type=ThresholdType.PROVIDER.value,
            metric=ThresholdMetric.TOTAL_RETURN.value,
            operator=ThresholdOperator.LESS_THAN.value,
            threshold_value=-10.0,
            enabled=True,
            cooldown_minutes=60,
        )
        
        db.add(threshold)
        await db_session.commit()
        
        # Set last triggered to 30 minutes ago (within cooldown)
        threshold.last_triggered_at = datetime.utcnow() - timedelta(minutes=30)
        await db_session.commit()
        
        # Should still be in cooldown
        time_since_last = datetime.utcnow() - threshold.last_triggered_at
        assert time_since_last.total_seconds() < (threshold.cooldown_minutes * 60)


class TestMarketplaceThresholdService:
    """Tests for MarketplaceThresholdService"""

    async def test_check_threshold_not_triggered(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test threshold check when condition is not met"""
        # Create threshold for total_return < -10%
        threshold = AnalyticsThreshold(
            user_id=test_user.id,
            threshold_type=ThresholdType.PROVIDER.value,
            metric=ThresholdMetric.TOTAL_RETURN.value,
            operator=ThresholdOperator.LESS_THAN.value,
            threshold_value=-10.0,
            context={"provider_id": 1},
            enabled=True,
        )
        
        db.add(threshold)
        await db_session.commit()
        
        # Mock analytics service to return value that doesn't trigger
        service = MarketplaceThresholdService(db_session)
        
        # Since we don't have a real provider, this will return None
        # But we can test the evaluation logic
        result = service._evaluate_threshold(-5.0, ThresholdOperator.LESS_THAN.value, -10.0)
        assert result is False  # -5.0 is not less than -10.0

    async def test_check_threshold_triggered(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test threshold check when condition is met"""
        service = MarketplaceThresholdService(db_session)
        
        # Test evaluation logic
        result = service._evaluate_threshold(-15.0, ThresholdOperator.LESS_THAN.value, -10.0)
        assert result is True  # -15.0 is less than -10.0

    async def test_evaluate_threshold_operators(
        self, db_session: AsyncSession
    ):
        """Test all threshold operators"""
        service = MarketplaceThresholdService(db_session)
        
        # Greater than
        assert service._evaluate_threshold(15.0, ThresholdOperator.GREATER_THAN.value, 10.0) is True
        assert service._evaluate_threshold(5.0, ThresholdOperator.GREATER_THAN.value, 10.0) is False
        
        # Less than
        assert service._evaluate_threshold(5.0, ThresholdOperator.LESS_THAN.value, 10.0) is True
        assert service._evaluate_threshold(15.0, ThresholdOperator.LESS_THAN.value, 10.0) is False
        
        # Equals
        assert service._evaluate_threshold(10.0, ThresholdOperator.EQUALS.value, 10.0) is True
        assert service._evaluate_threshold(10.1, ThresholdOperator.EQUALS.value, 10.0) is False
        
        # Greater than or equal
        assert service._evaluate_threshold(10.0, ThresholdOperator.GREATER_THAN_OR_EQUAL.value, 10.0) is True
        assert service._evaluate_threshold(11.0, ThresholdOperator.GREATER_THAN_OR_EQUAL.value, 10.0) is True
        assert service._evaluate_threshold(9.0, ThresholdOperator.GREATER_THAN_OR_EQUAL.value, 10.0) is False
        
        # Less than or equal
        assert service._evaluate_threshold(10.0, ThresholdOperator.LESS_THAN_OR_EQUAL.value, 10.0) is True
        assert service._evaluate_threshold(9.0, ThresholdOperator.LESS_THAN_OR_EQUAL.value, 10.0) is True
        assert service._evaluate_threshold(11.0, ThresholdOperator.LESS_THAN_OR_EQUAL.value, 10.0) is False


class TestAnalyticsThresholdAPI:
    """Tests for Analytics Threshold API routes"""

    async def test_create_threshold(
        self, client: AsyncClient, test_user_with_auth: dict
    ):
        """Test creating a threshold via API"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}
        
        payload = {
            "threshold_type": ThresholdType.PROVIDER.value,
            "metric": ThresholdMetric.TOTAL_RETURN.value,
            "operator": ThresholdOperator.LESS_THAN.value,
            "threshold_value": -10.0,
            "context": {"provider_id": 1},
            "enabled": True,
            "name": "Low Return Alert",
            "description": "Alert when return drops below -10%",
            "cooldown_minutes": 60,
        }
        
        response = await client.post(
            "/api/marketplace/analytics/thresholds",
            headers=headers,
            json=payload,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["threshold_type"] == ThresholdType.PROVIDER.value
        assert data["metric"] == ThresholdMetric.TOTAL_RETURN.value
        assert data["threshold_value"] == -10.0
        assert data["enabled"] is True
        assert "id" in data

    async def test_get_thresholds(
        self, client: AsyncClient, test_user_with_auth: dict, db: AsyncSession
    ):
        """Test getting all thresholds for a user"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}
        user_id = test_user_with_auth["user_id"]
        
        # Create a test threshold
        threshold = AnalyticsThreshold(
            user_id=user_id,
            threshold_type=ThresholdType.PROVIDER.value,
            metric=ThresholdMetric.TOTAL_RETURN.value,
            operator=ThresholdOperator.LESS_THAN.value,
            threshold_value=-10.0,
            enabled=True,
        )
        db.add(threshold)
        await db_session.commit()
        
        response = await client.get(
            "/api/marketplace/analytics/thresholds",
            headers=headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["threshold_type"] == ThresholdType.PROVIDER.value

    async def test_get_threshold_by_id(
        self, client: AsyncClient, test_user_with_auth: dict, db: AsyncSession
    ):
        """Test getting a specific threshold"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}
        user_id = test_user_with_auth["user_id"]
        
        # Create a test threshold
        threshold = AnalyticsThreshold(
            user_id=user_id,
            threshold_type=ThresholdType.PROVIDER.value,
            metric=ThresholdMetric.TOTAL_RETURN.value,
            operator=ThresholdOperator.LESS_THAN.value,
            threshold_value=-10.0,
            enabled=True,
            name="Test Threshold",
        )
        db_session.add(threshold)
        await db_session.commit()
        await db_session.refresh(threshold)
        
        response = await client.get(
            f"/api/marketplace/analytics/thresholds/{threshold.id}",
            headers=headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == threshold.id
        assert data["name"] == "Test Threshold"

    async def test_update_threshold(
        self, client: AsyncClient, test_user_with_auth: dict, db: AsyncSession
    ):
        """Test updating a threshold"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}
        user_id = test_user_with_auth["user_id"]
        
        # Create a test threshold
        threshold = AnalyticsThreshold(
            user_id=user_id,
            threshold_type=ThresholdType.PROVIDER.value,
            metric=ThresholdMetric.TOTAL_RETURN.value,
            operator=ThresholdOperator.LESS_THAN.value,
            threshold_value=-10.0,
            enabled=True,
        )
        db_session.add(threshold)
        await db_session.commit()
        await db_session.refresh(threshold)
        
        # Update threshold
        payload = {
            "enabled": False,
            "threshold_value": -15.0,
            "name": "Updated Threshold",
        }
        
        response = await client.put(
            f"/api/marketplace/analytics/thresholds/{threshold.id}",
            headers=headers,
            json=payload,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False
        assert data["threshold_value"] == -15.0

    async def test_delete_threshold(
        self, client: AsyncClient, test_user_with_auth: dict, db: AsyncSession
    ):
        """Test deleting a threshold"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}
        user_id = test_user_with_auth["user_id"]
        
        # Create a test threshold
        threshold = AnalyticsThreshold(
            user_id=user_id,
            threshold_type=ThresholdType.PROVIDER.value,
            metric=ThresholdMetric.TOTAL_RETURN.value,
            operator=ThresholdOperator.LESS_THAN.value,
            threshold_value=-10.0,
            enabled=True,
        )
        db_session.add(threshold)
        await db_session.commit()
        await db_session.refresh(threshold)
        threshold_id = threshold.id
        
        # Delete threshold
        response = await client.delete(
            f"/api/marketplace/analytics/thresholds/{threshold_id}",
            headers=headers,
        )
        
        assert response.status_code == 200
        
        # Verify it's deleted
        result = await db_session.execute(
            select(AnalyticsThreshold).where(AnalyticsThreshold.id == threshold_id)
        )
        deleted_threshold = result.scalar_one_or_none()
        assert deleted_threshold is None

    async def test_get_threshold_not_found(
        self, client: AsyncClient, test_user_with_auth: dict
    ):
        """Test getting a non-existent threshold"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}
        
        response = await client.get(
            "/api/marketplace/analytics/thresholds/99999",
            headers=headers,
        )
        
        assert response.status_code == 404

    async def test_get_threshold_unauthorized(
        self, client: AsyncClient, test_user_with_auth: dict, db: AsyncSession
    ):
        """Test that users cannot access other users' thresholds"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}
        
        # Create another user and threshold
        from ..models.user import User
        other_user = User(
            username="other_user",
            email="other@example.com",
            password_hash="hashed",
        )
        db.add(other_user)
        await db_session.commit()
        await db.refresh(other_user)
        
        threshold = AnalyticsThreshold(
            user_id=other_user.id,
            threshold_type=ThresholdType.PROVIDER.value,
            metric=ThresholdMetric.TOTAL_RETURN.value,
            operator=ThresholdOperator.LESS_THAN.value,
            threshold_value=-10.0,
            enabled=True,
        )
        db_session.add(threshold)
        await db_session.commit()
        await db_session.refresh(threshold)
        
        # Try to access other user's threshold
        response = await client.get(
            f"/api/marketplace/analytics/thresholds/{threshold.id}",
            headers=headers,
        )
        
        assert response.status_code == 404  # Not found (filtered by user_id)

    async def test_filter_thresholds_by_type(
        self, client: AsyncClient, test_user_with_auth: dict, db: AsyncSession
    ):
        """Test filtering thresholds by type"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}
        user_id = test_user_with_auth["user_id"]
        
        # Create thresholds of different types
        threshold1 = AnalyticsThreshold(
            user_id=user_id,
            threshold_type=ThresholdType.PROVIDER.value,
            metric=ThresholdMetric.TOTAL_RETURN.value,
            operator=ThresholdOperator.LESS_THAN.value,
            threshold_value=-10.0,
            enabled=True,
        )
        threshold2 = AnalyticsThreshold(
            user_id=user_id,
            threshold_type=ThresholdType.DEVELOPER.value,
            metric=ThresholdMetric.INDICATOR_REVENUE_DROP_PERCENT.value,
            operator=ThresholdOperator.LESS_THAN.value,
            threshold_value=100.0,
            enabled=True,
        )
        db_session.add(threshold1)
        db_session.add(threshold2)
        await db_session.commit()
        
        # Filter by provider type
        response = await client.get(
            f"/api/marketplace/analytics/thresholds?threshold_type={ThresholdType.PROVIDER.value}",
            headers=headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(t["threshold_type"] == ThresholdType.PROVIDER.value for t in data)
