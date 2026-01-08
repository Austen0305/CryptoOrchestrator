"""
Tests for User Onboarding System
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server_fastapi.models.user import User
from server_fastapi.services.onboarding_service import OnboardingService

pytestmark = pytest.mark.asyncio


class TestOnboardingProgress:
    """Tests for OnboardingProgress model and service"""

    async def test_get_or_create_progress(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test getting or creating onboarding progress"""
        service = OnboardingService(db_session)

        progress = await service.get_or_create_progress(test_user.id)

        assert progress.user_id == test_user.id
        assert progress.current_step == "welcome"
        assert progress.progress_percentage == 0
        assert progress.is_completed is False

    async def test_complete_step(self, db_session: AsyncSession, test_user: User):
        """Test completing an onboarding step"""
        service = OnboardingService(db_session)

        progress = await service.get_or_create_progress(test_user.id)

        # Complete first step
        updated = await service.complete_step(test_user.id, "welcome")

        assert "welcome" in updated.completed_steps
        assert updated.current_step == "wallet_setup"
        assert updated.progress_percentage > 0

    async def test_skip_step(self, db_session: AsyncSession, test_user: User):
        """Test skipping an onboarding step"""
        service = OnboardingService(db_session)

        progress = await service.get_or_create_progress(test_user.id)

        # Skip first step
        updated = await service.skip_step(test_user.id, "welcome")

        assert "welcome" in updated.skipped_steps
        assert updated.current_step == "wallet_setup"

    async def test_reset_progress(self, db_session: AsyncSession, test_user: User):
        """Test resetting onboarding progress"""
        service = OnboardingService(db_session)

        # Complete a step
        await service.complete_step(test_user.id, "welcome")

        # Reset
        reset = await service.reset_progress(test_user.id)

        assert reset.progress_percentage == 0
        assert len(reset.completed_steps) == 0
        assert reset.current_step == "welcome"


class TestUserAchievements:
    """Tests for UserAchievement model and service"""

    async def test_check_and_unlock_achievement(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test checking and unlocking achievements"""
        service = OnboardingService(db_session)

        # Check first trade achievement
        achievement = await service.check_and_unlock_achievement(
            test_user.id,
            "first_trade",
            progress_value=1,
        )

        assert achievement is not None
        assert achievement.is_unlocked is True
        assert achievement.achievement_id == "first_trade"
        assert achievement.unlocked_at is not None

    async def test_achievement_progress(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test achievement progress tracking"""
        service = OnboardingService(db_session)

        # Check ten_trades achievement (not yet unlocked)
        achievement = await service.check_and_unlock_achievement(
            test_user.id,
            "ten_trades",
            progress_value=5,  # Halfway
        )

        # Should not be unlocked yet
        if achievement:
            assert achievement.progress == 5
            assert achievement.is_unlocked is False

        # Complete achievement
        achievement = await service.check_and_unlock_achievement(
            test_user.id,
            "ten_trades",
            progress_value=10,
        )

        assert achievement is not None
        assert achievement.is_unlocked is True


class TestFeatureAccess:
    """Tests for FeatureAccess model and service"""

    async def test_check_and_unlock_feature(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test checking and unlocking features"""
        service = OnboardingService(db_session)

        # Check copy_trading feature (requires 1 trade)
        feature = await service.check_and_unlock_feature(
            test_user.id,
            "copy_trading",
            user_stats={"trade_count": 1, "account_age_days": 0},
        )

        assert feature is not None
        assert feature.is_unlocked is True
        assert feature.feature_name == "copy_trading"
        assert feature.unlocked_at is not None

    async def test_feature_requirements_not_met(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test feature that doesn't meet requirements"""
        service = OnboardingService(db_session)

        # Check advanced_orders (requires 5 trades, only have 1)
        feature = await service.check_and_unlock_feature(
            test_user.id,
            "advanced_orders",
            user_stats={"trade_count": 1},
        )

        # Should not be unlocked
        assert feature is None

        # Now with 5 trades
        feature = await service.check_and_unlock_feature(
            test_user.id,
            "advanced_orders",
            user_stats={"trade_count": 5},
        )

        assert feature is not None
        assert feature.is_unlocked is True
