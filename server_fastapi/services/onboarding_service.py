"""
Onboarding Service
Manages user onboarding progress, achievements, and feature unlocking
"""

import logging
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.onboarding import (
    OnboardingProgress,
    OnboardingStep,
    UserAchievement,
)

logger = logging.getLogger(__name__)


class OnboardingService:
    """
    Service for managing user onboarding

    Features:
    - Step tracking and completion
    - Progress calculation
    - Achievement unlocking
    - Resume functionality
    """

    # Define onboarding steps in order
    ONBOARDING_STEPS = [
        OnboardingStep.WELCOME,
        OnboardingStep.WALLET_SETUP,
        OnboardingStep.FIRST_DEPOSIT,
        OnboardingStep.FIRST_TRADE,
        OnboardingStep.BOT_CREATION,
        OnboardingStep.MARKETPLACE_EXPLORE,
        OnboardingStep.ADVANCED_FEATURES,
    ]

    # Define achievements
    ACHIEVEMENTS = {
        "first_trade": {
            "name": "First Trade",
            "description": "Completed your first trade",
            "requirement": {"type": "trade_count", "value": 1},
        },
        "ten_trades": {
            "name": "Trading Veteran",
            "description": "Completed 10 trades",
            "requirement": {"type": "trade_count", "value": 10},
        },
        "first_bot": {
            "name": "Bot Master",
            "description": "Created your first trading bot",
            "requirement": {"type": "bot_count", "value": 1},
        },
        "copy_trader": {
            "name": "Copy Trader",
            "description": "Started copy trading",
            "requirement": {"type": "copy_trade", "value": 1},
        },
        "marketplace_explorer": {
            "name": "Marketplace Explorer",
            "description": "Explored the marketplace",
            "requirement": {"type": "marketplace_view", "value": 1},
        },
    }

    def __init__(self, db: AsyncSession):
        """
        Initialize onboarding service

        Args:
            db: Async database session
        """
        self.db = db

    async def get_or_create_progress(
        self,
        user_id: int,
    ) -> OnboardingProgress:
        """
        Get or create onboarding progress for user

        Args:
            user_id: User ID

        Returns:
            OnboardingProgress
        """
        stmt = select(OnboardingProgress).where(OnboardingProgress.user_id == user_id)
        result = await self.db.execute(stmt)
        progress = result.scalar_one_or_none()

        if not progress:
            progress = OnboardingProgress(
                user_id=user_id,
                current_step=self.ONBOARDING_STEPS[0],
                total_steps=len(self.ONBOARDING_STEPS),
            )
            self.db.add(progress)
            await self.db.commit()
            await self.db.refresh(progress)

        return progress

    async def complete_step(
        self,
        user_id: int,
        step_id: str,
    ) -> OnboardingProgress:
        """
        Mark a step as completed

        Args:
            user_id: User ID
            step_id: Step identifier

        Returns:
            Updated OnboardingProgress
        """
        progress = await self.get_or_create_progress(user_id)

        # Mark step as completed
        if not progress.completed_steps:
            progress.completed_steps = {}

        if step_id not in progress.completed_steps:
            progress.completed_steps[step_id] = datetime.utcnow().isoformat()

        # Update current step
        try:
            current_index = self.ONBOARDING_STEPS.index(step_id)
            if current_index < len(self.ONBOARDING_STEPS) - 1:
                progress.current_step = self.ONBOARDING_STEPS[current_index + 1]
        except ValueError:
            pass  # Step not in list

        # Recalculate progress
        progress.progress_percentage = int(
            (len(progress.completed_steps) / progress.total_steps) * 100
        )

        # Check if completed
        if progress.progress_percentage >= 100:
            progress.is_completed = True
            progress.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(progress)

        logger.info(f"Step {step_id} completed for user {user_id}")

        return progress

    async def skip_step(
        self,
        user_id: int,
        step_id: str,
    ) -> OnboardingProgress:
        """
        Skip a step

        Args:
            user_id: User ID
            step_id: Step identifier

        Returns:
            Updated OnboardingProgress
        """
        progress = await self.get_or_create_progress(user_id)

        if not progress.skipped_steps:
            progress.skipped_steps = {}

        if step_id not in progress.skipped_steps:
            progress.skipped_steps[step_id] = datetime.utcnow().isoformat()

        # Move to next step
        try:
            current_index = self.ONBOARDING_STEPS.index(step_id)
            if current_index < len(self.ONBOARDING_STEPS) - 1:
                progress.current_step = self.ONBOARDING_STEPS[current_index + 1]
        except ValueError:
            pass

        await self.db.commit()
        await self.db.refresh(progress)

        return progress

    async def reset_progress(
        self,
        user_id: int,
    ) -> OnboardingProgress:
        """
        Reset onboarding progress

        Args:
            user_id: User ID

        Returns:
            Reset OnboardingProgress
        """
        progress = await self.get_or_create_progress(user_id)

        progress.current_step = self.ONBOARDING_STEPS[0]
        progress.completed_steps = {}
        progress.skipped_steps = {}
        progress.progress_percentage = 0
        progress.is_completed = False
        progress.completed_at = None

        await self.db.commit()
        await self.db.refresh(progress)

        return progress

    async def check_and_unlock_achievement(
        self,
        user_id: int,
        achievement_id: str,
        progress_value: int = 1,
    ) -> UserAchievement | None:
        """
        Check and unlock achievement if requirements met

        Args:
            user_id: User ID
            achievement_id: Achievement identifier
            progress_value: Progress value (e.g., trade count)

        Returns:
            UserAchievement if unlocked, None otherwise
        """
        if achievement_id not in self.ACHIEVEMENTS:
            return None

        achievement_def = self.ACHIEVEMENTS[achievement_id]

        # Get or create achievement
        stmt = select(UserAchievement).where(
            and_(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement_id,
            )
        )
        result = await self.db.execute(stmt)
        achievement = result.scalar_one_or_none()

        if not achievement:
            achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement_id,
                achievement_name=achievement_def["name"],
                achievement_description=achievement_def["description"],
                max_progress=achievement_def["requirement"]["value"],
            )
            self.db.add(achievement)
        else:
            if achievement.is_unlocked:
                return achievement  # Already unlocked

        # Update progress
        achievement.progress = min(progress_value, achievement.max_progress)

        # Check if unlocked
        if (
            achievement.progress >= achievement.max_progress
            and not achievement.is_unlocked
        ):
            achievement.is_unlocked = True
            achievement.unlocked_at = datetime.utcnow()
            logger.info(f"Achievement {achievement_id} unlocked for user {user_id}")

        await self.db.commit()
        await self.db.refresh(achievement)

        return achievement if achievement.is_unlocked else None

    async def get_user_achievements(
        self,
        user_id: int,
    ) -> list[UserAchievement]:
        """Get all achievements for user"""
        stmt = (
            select(UserAchievement)
            .where(UserAchievement.user_id == user_id)
            .order_by(UserAchievement.unlocked_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
