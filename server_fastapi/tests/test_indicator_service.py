"""
Tests for Indicator Marketplace Service
"""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server_fastapi.models.indicator import (
    Indicator,
    IndicatorLanguage,
    IndicatorPurchase,
    IndicatorRating,
    IndicatorStatus,
    IndicatorVersion,
)
from server_fastapi.models.user import User
from server_fastapi.services.indicator_service import IndicatorService

pytestmark = pytest.mark.asyncio


class TestIndicatorService:
    """Tests for IndicatorService"""

    @pytest_asyncio.fixture
    async def test_user(self, db_session: AsyncSession):
        """Create a test user"""
        user = User(
            email="developer@example.com",
            username="developer",
            password_hash="hashed_password_for_testing",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest_asyncio.fixture
    async def test_indicator(self, db_session: AsyncSession, test_user):
        """Create a test indicator"""
        indicator = Indicator(
            developer_id=test_user.id,
            name="Test RSI",
            description="Test RSI indicator",
            category="momentum",
            tags="rsi, momentum",
            code="def calculate_rsi(data, period=14): return 50.0",
            language=IndicatorLanguage.PYTHON.value,
            parameters={"period": 14},
            price=0.0,
            is_free=True,
            status=IndicatorStatus.APPROVED.value,
            is_public=True,
        )
        db_session.add(indicator)
        await db_session.flush()

        # Create version
        version = IndicatorVersion(
            indicator_id=indicator.id,
            version=1,
            version_name="1.0.0",
            code=indicator.code,
            parameters=indicator.parameters,
            is_active=True,
        )
        db.add(version)
        indicator.latest_version_id = version.id
        await db_session.commit()
        await db_session.refresh(indicator)
        return indicator

    async def test_create_indicator(self, db_session: AsyncSession, test_user):
        """Test creating an indicator"""
        service = IndicatorService(db_session)

        result = await service.create_indicator(
            developer_id=test_user.id,
            name="Custom MACD",
            code="def calculate_macd(data): return 0.0",
            language="python",
            description="Custom MACD indicator",
            category="trend",
            tags="macd, trend",
            price=0.0,
            is_free=True,
            parameters={"fast": 12, "slow": 26},
        )

        assert result["name"] == "Custom MACD"
        assert result["status"] == IndicatorStatus.DRAFT.value

        # Verify indicator created
        indicator = await db_session.get(Indicator, result["id"])
        assert indicator is not None
        assert indicator.developer_id == test_user.id

    async def test_publish_indicator(self, db_session: AsyncSession, test_user):
        """Test publishing an indicator"""
        service = IndicatorService(db_session)

        # Create indicator
        create_result = await service.create_indicator(
            developer_id=test_user.id,
            name="Test Indicator",
            code="def calculate(data): return 0.0",
        )

        # Publish indicator
        result = await service.publish_indicator(
            indicator_id=create_result["id"],
            developer_id=test_user.id,
        )

        assert result["status"] == IndicatorStatus.PENDING.value

        # Verify status updated
        indicator = await db_session.get(Indicator, create_result["id"])
        assert indicator.status == IndicatorStatus.PENDING.value

    async def test_create_version(self, db: AsyncSession, test_indicator, test_user):
        """Test creating a new version"""
        service = IndicatorService(db_session)

        result = await service.create_version(
            indicator_id=test_indicator.id,
            developer_id=test_user.id,
            code="def calculate_rsi(data, period=14): return 55.0  # Updated",
            version_name="1.1.0",
            changelog="Improved calculation",
            parameters={"period": 14},
        )

        assert result["version"] == 2  # Second version
        assert result["version_name"] == "1.1.0"

        # Verify version created
        version_result = await db_session.execute(
            select(IndicatorVersion)
            .where(IndicatorVersion.indicator_id == test_indicator.id)
            .where(IndicatorVersion.version == 2)
        )
        version = version_result.scalar_one_or_none()
        assert version is not None

    async def test_purchase_indicator(self, db: AsyncSession, test_indicator):
        """Test purchasing an indicator"""
        service = IndicatorService(db_session)

        # Create buyer user
        buyer = User(
            email="buyer@example.com",
            username="buyer",
            password_hash="hashed_password_for_testing",
            is_active=True,
        )
        db.add(buyer)
        await db_session.commit()
        await db_session.refresh(buyer)

        # Set indicator as paid
        test_indicator.price = 10.0
        test_indicator.is_free = False
        await db_session.commit()

        result = await service.purchase_indicator(
            indicator_id=test_indicator.id,
            user_id=buyer.id,
        )

        assert result["status"] == "completed"
        assert result["price_paid"] == 10.0
        assert result["platform_fee"] == 3.0  # 30%
        assert result["developer_payout"] == 7.0  # 70%

        # Verify purchase created
        purchase_result = await db_session.execute(
            select(IndicatorPurchase).where(
                IndicatorPurchase.indicator_id == test_indicator.id,
                IndicatorPurchase.user_id == buyer.id,
            )
        )
        purchase = purchase_result.scalar_one_or_none()
        assert purchase is not None

    async def test_rate_indicator(self, db: AsyncSession, test_indicator):
        """Test rating an indicator"""
        service = IndicatorService(db_session)

        # Create rater user
        rater = User(
            email="rater@example.com",
            username="rater",
            password_hash="hashed_password_for_testing",
            is_active=True,
        )
        db_session.add(rater)
        await db_session.commit()
        await db_session.refresh(rater)

        result = await service.rate_indicator(
            indicator_id=test_indicator.id,
            user_id=rater.id,
            rating=5,
            comment="Excellent indicator!",
        )

        assert result["rating"] == 5
        assert result["comment"] == "Excellent indicator!"

        # Verify rating created
        rating_result = await db_session.execute(
            select(IndicatorRating).where(
                IndicatorRating.indicator_id == test_indicator.id,
                IndicatorRating.user_id == rater.id,
            )
        )
        rating = rating_result.scalar_one_or_none()
        assert rating is not None
        assert rating.rating == 5

    async def test_get_marketplace_indicators(self, db: AsyncSession, test_indicator):
        """Test getting marketplace indicators"""
        service = IndicatorService(db_session)

        result = await service.get_marketplace_indicators(
            skip=0,
            limit=10,
            sort_by="download_count",
            category=None,
            is_free=None,
            min_rating=None,
            search_query=None,
        )

        assert "indicators" in result
        assert "total" in result
        assert len(result["indicators"]) > 0

    async def test_execute_indicator(self, db: AsyncSession, test_indicator):
        """Test executing an indicator"""
        service = IndicatorService(db_session)

        # Create user who owns indicator
        market_data = [
            {
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,
                "close": 103.0,
                "volume": 1000,
                "timestamp": "2025-12-12T00:00:00Z",
            },
            {
                "open": 103.0,
                "high": 108.0,
                "low": 102.0,
                "close": 106.0,
                "volume": 1200,
                "timestamp": "2025-12-12T01:00:00Z",
            },
        ]

        result = await service.execute_indicator(
            indicator_id=test_indicator.id,
            user_id=test_indicator.developer_id,
            market_data=market_data,
            parameters={"period": 14},
        )

        assert result["status"] == "success"
        assert "values" in result or "output" in result
