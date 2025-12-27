"""
Tests for Copy Trading Marketplace Service
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from decimal import Decimal

from server_fastapi.services.marketplace_service import MarketplaceService
from server_fastapi.models.signal_provider import SignalProvider, SignalProviderRating, Payout, CuratorStatus
from server_fastapi.models.user import User
from sqlalchemy import select


pytestmark = pytest.mark.asyncio


class TestMarketplaceService:
    """Tests for MarketplaceService"""

    @pytest_asyncio.fixture
    async def test_user(self, db_session: AsyncSession):
        """Create a test user"""
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password_for_testing",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest_asyncio.fixture
    async def test_provider(self, db_session: AsyncSession, test_user):
        """Create a test signal provider"""
        provider = SignalProvider(
            user_id=test_user.id,
            curator_status=CuratorStatus.APPROVED.value,
            total_return=15.5,
            sharpe_ratio=1.8,
            win_rate=0.65,
            total_trades=100,
            follower_count=50,
        )
        db_session.add(provider)
        await db_session.commit()
        await db_session.refresh(provider)
        return provider

    async def test_apply_as_signal_provider(self, db_session: AsyncSession, test_user):
        """Test applying as a signal provider"""
        service = MarketplaceService(db_session)

        result = await service.apply_as_signal_provider(
            user_id=test_user.id,
            profile_description="Test signal provider",
        )

        assert result["status"] == "pending"
        assert result["user_id"] == test_user.id

        # Verify provider was created
        provider = await db_session.get(SignalProvider, result["id"])
        assert provider is not None
        assert provider.curator_status == CuratorStatus.PENDING.value

    async def test_approve_signal_provider(self, db: AsyncSession, test_user):
        """Test approving a signal provider"""
        service = MarketplaceService(db_session)

        # Create pending provider
        apply_result = await service.apply_as_signal_provider(
            user_id=test_user.id,
        )

        # Approve provider
        result = await service.approve_signal_provider(
            provider_id=apply_result["id"],
            curator_id=1,  # Admin user
        )

        assert result["status"] == "approved"

        # Verify status updated
        provider = await db.get(SignalProvider, apply_result["id"])
        assert provider.curator_status == CuratorStatus.APPROVED.value

    async def test_update_performance_metrics(self, db_session: AsyncSession, test_provider):
        """Test updating performance metrics"""
        service = MarketplaceService(db_session)

        # Create some trade history (simplified)
        trades = [
            {"pnl": 100.0, "timestamp": datetime.utcnow() - timedelta(days=1)},
            {"pnl": -50.0, "timestamp": datetime.utcnow() - timedelta(days=2)},
            {"pnl": 200.0, "timestamp": datetime.utcnow() - timedelta(days=3)},
        ]

        result = await service.update_performance_metrics(
            provider_id=test_provider.id,
            trades=trades,
        )

        assert result["total_return"] > 0
        assert "sharpe_ratio" in result
        assert "win_rate" in result

        # Verify metrics updated in database
        await db.refresh(test_provider)
        assert test_provider.total_return is not None

    async def test_rate_signal_provider(self, db: AsyncSession, test_provider, test_user):
        """Test rating a signal provider"""
        service = MarketplaceService(db_session)

        # Create another user to rate
        rater = User(
            email="rater@example.com",
            username="rater",
            password_hash="hashed_password_for_testing",
            is_active=True,
        )
        db_session.add(rater)
        await db_session.commit()
        await db_session.refresh(rater)

        result = await service.rate_signal_provider(
            provider_id=test_provider.id,
            user_id=rater.id,
            rating=5,
            comment="Excellent trader!",
        )

        assert result["rating"] == 5
        assert result["comment"] == "Excellent trader!"

        # Verify rating created
        rating = await db_session.execute(
            select(SignalProviderRating).where(
                SignalProviderRating.signal_provider_id == test_provider.id,
                SignalProviderRating.user_id == rater.id,
            )
        )
        rating_obj = rating.scalar_one_or_none()
        assert rating_obj is not None
        assert rating_obj.rating == 5

    async def test_get_marketplace_traders(self, db_session: AsyncSession, test_provider):
        """Test getting marketplace traders with filters"""
        service = MarketplaceService(db_session)

        result = await service.get_marketplace_traders(
            skip=0,
            limit=10,
            sort_by="sharpe_ratio",
            min_rating=None,
            min_win_rate=0.6,
            min_sharpe=None,
        )

        assert "traders" in result
        assert "total" in result
        assert len(result["traders"]) > 0

        # Verify filtering
        for trader in result["traders"]:
            assert trader["win_rate"] >= 0.6

    async def test_calculate_payout(self, db_session: AsyncSession, test_provider):
        """Test calculating payout"""
        service = MarketplaceService(db_session)

        period_start = datetime.utcnow() - timedelta(days=30)
        period_end = datetime.utcnow()
        total_revenue = 1000.0

        result = await service.calculate_payout(
            provider_id=test_provider.id,
            period_start=period_start,
            period_end=period_end,
            total_revenue=total_revenue,
        )

        assert result["total_revenue"] == total_revenue
        assert result["platform_fee"] == total_revenue * 0.20  # 20%
        assert result["provider_payout"] == total_revenue * 0.80  # 80%

    async def test_create_payout(self, db_session: AsyncSession, test_provider):
        """Test creating a payout"""
        service = MarketplaceService(db_session)

        period_start = datetime.utcnow() - timedelta(days=30)
        period_end = datetime.utcnow()
        total_revenue = 1000.0

        result = await service.create_payout(
            provider_id=test_provider.id,
            period_start=period_start,
            period_end=period_end,
            total_revenue=total_revenue,
        )

        assert result["status"] == "pending"
        assert result["total_revenue"] == total_revenue

        # Verify payout created
        payout = await db_session.get(Payout, result["id"])
        assert payout is not None
        assert payout.provider_payout == total_revenue * 0.80
