"""
Social Service
Manages strategy sharing, social feed, user profiles, achievements, and challenges
"""

import secrets
from datetime import datetime
from typing import Any

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.social import (
    Achievement,
    ChallengeParticipant,
    CommunityChallenge,
    SharedStrategy,
    SocialFeedEvent,
    StrategyComment,
    StrategyLike,
    StrategyVisibility,
    UserAchievement,
    UserProfile,
)


class SocialService:
    """Service for social and community features"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # Strategy Sharing Methods
    async def share_strategy(
        self,
        user_id: int,
        name: str,
        strategy_config: dict[str, Any],
        description: str | None = None,
        visibility: StrategyVisibility = StrategyVisibility.PUBLIC,
        tags: list[str] | None = None,
        category: str | None = None,
    ) -> SharedStrategy:
        """Share a trading strategy"""
        share_token = None
        if visibility == StrategyVisibility.UNLISTED:
            share_token = secrets.token_urlsafe(32)

        strategy = SharedStrategy(
            user_id=user_id,
            name=name,
            description=description,
            strategy_config=strategy_config,
            visibility=visibility,
            share_token=share_token,
            tags=tags or [],
            category=category,
        )
        self.db.add(strategy)
        await self.db.commit()
        await self.db.refresh(strategy)

        # Create social feed event
        await self.create_feed_event(
            user_id=user_id,
            event_type="strategy_shared",
            event_data={"strategy_id": strategy.id, "strategy_name": name},
        )

        return strategy

    async def get_strategies(
        self,
        user_id: int | None = None,
        category: str | None = None,
        featured_only: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> list[SharedStrategy]:
        """Get shared strategies"""
        stmt = select(SharedStrategy).where(
            or_(
                SharedStrategy.visibility == StrategyVisibility.PUBLIC,
                SharedStrategy.user_id == user_id if user_id else False,
            )
        )

        if category:
            stmt = stmt.where(SharedStrategy.category == category)
        if featured_only:
            stmt = stmt.where(SharedStrategy.is_featured == True)

        stmt = stmt.order_by(desc(SharedStrategy.created_at))
        stmt = stmt.limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def like_strategy(
        self,
        user_id: int,
        strategy_id: int,
    ) -> bool:
        """Like/unlike a strategy"""
        # Check if already liked
        stmt = select(StrategyLike).where(
            and_(
                StrategyLike.user_id == user_id,
                StrategyLike.strategy_id == strategy_id,
            )
        )
        result = await self.db.execute(stmt)
        existing_like = result.scalar_one_or_none()

        if existing_like:
            # Unlike
            await self.db.delete(existing_like)
            # Decrement like count
            strategy = await self.db.get(SharedStrategy, strategy_id)
            if strategy:
                strategy.like_count = max(0, strategy.like_count - 1)
            await self.db.commit()
            return False
        else:
            # Like
            like = StrategyLike(user_id=user_id, strategy_id=strategy_id)
            self.db.add(like)
            # Increment like count
            strategy = await self.db.get(SharedStrategy, strategy_id)
            if strategy:
                strategy.like_count += 1
            await self.db.commit()
            return True

    async def comment_on_strategy(
        self,
        user_id: int,
        strategy_id: int,
        content: str,
        parent_comment_id: int | None = None,
    ) -> StrategyComment:
        """Comment on a strategy"""
        comment = StrategyComment(
            user_id=user_id,
            strategy_id=strategy_id,
            content=content,
            parent_comment_id=parent_comment_id,
        )
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    # Social Feed Methods
    async def create_feed_event(
        self,
        user_id: int,
        event_type: str,
        event_data: dict[str, Any],
        is_public: bool = True,
    ) -> SocialFeedEvent:
        """Create a social feed event"""
        event = SocialFeedEvent(
            user_id=user_id,
            event_type=event_type,
            event_data=event_data,
            is_public=is_public,
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def get_feed(
        self,
        user_id: int | None = None,
        following_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SocialFeedEvent]:
        """Get social feed"""
        stmt = select(SocialFeedEvent).where(SocialFeedEvent.is_public == True)

        if following_only and user_id:
            # Get users being followed
            from ..models.follow import Follow

            following_stmt = select(Follow.trader_id).where(
                and_(
                    Follow.follower_id == user_id,
                    Follow.is_active == True,
                )
            )
            stmt = stmt.where(SocialFeedEvent.user_id.in_(following_stmt))

        stmt = stmt.order_by(desc(SocialFeedEvent.created_at))
        stmt = stmt.limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # User Profile Methods
    async def get_or_create_profile(self, user_id: int) -> UserProfile:
        """Get or create user profile"""
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)

        return profile

    async def update_profile(
        self,
        user_id: int,
        display_name: str | None = None,
        bio: str | None = None,
        avatar_url: str | None = None,
        website_url: str | None = None,
        twitter_handle: str | None = None,
        telegram_handle: str | None = None,
        is_public: bool | None = None,
        show_trading_stats: bool | None = None,
    ) -> UserProfile:
        """Update user profile"""
        profile = await self.get_or_create_profile(user_id)

        if display_name is not None:
            profile.display_name = display_name
        if bio is not None:
            profile.bio = bio
        if avatar_url is not None:
            profile.avatar_url = avatar_url
        if website_url is not None:
            profile.website_url = website_url
        if twitter_handle is not None:
            profile.twitter_handle = twitter_handle
        if telegram_handle is not None:
            profile.telegram_handle = telegram_handle
        if is_public is not None:
            profile.is_public = is_public
        if show_trading_stats is not None:
            profile.show_trading_stats = show_trading_stats

        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def update_profile_stats(self, user_id: int) -> UserProfile:
        """Update cached profile statistics"""
        profile = await self.get_or_create_profile(user_id)

        # Calculate trading stats
        from ..models.follow import Follow
        from ..models.trade import Trade

        # Total trades
        trade_stmt = select(func.count(Trade.id)).where(Trade.user_id == user_id)
        trade_result = await self.db.execute(trade_stmt)
        profile.total_trades = trade_result.scalar() or 0

        # Win rate
        win_stmt = select(func.count(Trade.id)).where(
            and_(
                Trade.user_id == user_id,
                Trade.pnl > 0,
            )
        )
        win_result = await self.db.execute(win_stmt)
        win_count = win_result.scalar() or 0
        profile.win_rate = (
            (win_count / profile.total_trades * 100)
            if profile.total_trades > 0
            else 0.0
        )

        # Total PnL
        pnl_stmt = select(func.sum(Trade.pnl)).where(Trade.user_id == user_id)
        pnl_result = await self.db.execute(pnl_stmt)
        profile.total_pnl = float(pnl_result.scalar() or 0)

        # Followers count
        followers_stmt = select(func.count(Follow.id)).where(
            and_(
                Follow.trader_id == user_id,
                Follow.is_active == True,
            )
        )
        followers_result = await self.db.execute(followers_stmt)
        profile.followers_count = followers_result.scalar() or 0

        # Following count
        following_stmt = select(func.count(Follow.id)).where(
            and_(
                Follow.follower_id == user_id,
                Follow.is_active == True,
            )
        )
        following_result = await self.db.execute(following_stmt)
        profile.following_count = following_result.scalar() or 0

        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    # Achievement Methods
    async def check_and_award_achievements(self, user_id: int) -> list[UserAchievement]:
        """Check and award achievements for a user"""
        # Get all achievements
        achievements_stmt = select(Achievement)
        achievements_result = await self.db.execute(achievements_stmt)
        all_achievements = achievements_result.scalars().all()

        # Get user's existing achievements
        user_achievements_stmt = select(UserAchievement).where(
            UserAchievement.user_id == user_id
        )
        user_achievements_result = await self.db.execute(user_achievements_stmt)
        existing_achievements = {
            ua.achievement_id for ua in user_achievements_result.scalars().all()
        }

        newly_awarded = []

        for achievement in all_achievements:
            if achievement.id in existing_achievements:
                continue

            # Check if achievement requirements are met
            if await self._check_achievement_requirement(user_id, achievement):
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    is_completed=True,
                    completed_at=datetime.utcnow(),
                )
                self.db.add(user_achievement)
                newly_awarded.append(user_achievement)

                # Create feed event
                await self.create_feed_event(
                    user_id=user_id,
                    event_type="achievement_earned",
                    event_data={
                        "achievement_id": achievement.id,
                        "achievement_name": achievement.name,
                    },
                )

        if newly_awarded:
            await self.db.commit()
            for ua in newly_awarded:
                await self.db.refresh(ua)

        return newly_awarded

    async def _check_achievement_requirement(
        self, user_id: int, achievement: Achievement
    ) -> bool:
        """Check if achievement requirement is met"""
        req_type = achievement.requirement_type
        req_value = achievement.requirement_value

        if req_type == "trade_count":
            from ..models.trade import Trade

            stmt = select(func.count(Trade.id)).where(Trade.user_id == user_id)
            result = await self.db.execute(stmt)
            count = result.scalar() or 0
            return count >= req_value.get("count", 0)

        elif req_type == "profit_amount":
            from ..models.trade import Trade

            stmt = select(func.sum(Trade.pnl)).where(
                and_(
                    Trade.user_id == user_id,
                    Trade.pnl > 0,
                )
            )
            result = await self.db.execute(stmt)
            total_profit = float(result.scalar() or 0)
            return total_profit >= req_value.get("amount", 0)

        elif req_type == "win_streak":
            from ..models.trade import Trade

            # Get recent trades ordered by time
            stmt = (
                select(Trade)
                .where(Trade.user_id == user_id)
                .order_by(desc(Trade.created_at))
                .limit(req_value.get("streak", 0))
            )
            result = await self.db.execute(stmt)
            trades = result.scalars().all()
            if len(trades) < req_value.get("streak", 0):
                return False
            return all(trade.pnl > 0 for trade in trades)

        return False

    async def get_user_achievements(
        self,
        user_id: int,
        completed_only: bool = False,
    ) -> list[UserAchievement]:
        """Get user achievements"""
        stmt = select(UserAchievement).where(UserAchievement.user_id == user_id)

        if completed_only:
            stmt = stmt.where(UserAchievement.is_completed == True)

        stmt = stmt.options(selectinload(UserAchievement.achievement))
        stmt = stmt.order_by(desc(UserAchievement.completed_at))

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # Community Challenge Methods
    async def create_challenge(
        self,
        name: str,
        description: str,
        challenge_type: str,
        rules: dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        created_by_user_id: int | None = None,
        prizes: dict[str, Any] | None = None,
    ) -> CommunityChallenge:
        """Create a community challenge"""
        challenge = CommunityChallenge(
            name=name,
            description=description,
            challenge_type=challenge_type,
            rules=rules,
            start_date=start_date,
            end_date=end_date,
            created_by_user_id=created_by_user_id,
            prizes=prizes,
        )
        self.db.add(challenge)
        await self.db.commit()
        await self.db.refresh(challenge)
        return challenge

    async def join_challenge(
        self,
        user_id: int,
        challenge_id: int,
    ) -> ChallengeParticipant:
        """Join a community challenge"""
        # Check if already participating
        stmt = select(ChallengeParticipant).where(
            and_(
                ChallengeParticipant.user_id == user_id,
                ChallengeParticipant.challenge_id == challenge_id,
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return existing

        participant = ChallengeParticipant(
            user_id=user_id,
            challenge_id=challenge_id,
        )
        self.db.add(participant)

        # Increment participant count
        challenge = await self.db.get(CommunityChallenge, challenge_id)
        if challenge:
            challenge.participant_count += 1

        await self.db.commit()
        await self.db.refresh(participant)
        return participant

    async def get_challenge_leaderboard(
        self,
        challenge_id: int,
        limit: int = 100,
    ) -> list[ChallengeParticipant]:
        """Get challenge leaderboard"""
        stmt = select(ChallengeParticipant).where(
            ChallengeParticipant.challenge_id == challenge_id
        )
        stmt = stmt.order_by(desc(ChallengeParticipant.score))
        stmt = stmt.limit(limit)
        stmt = stmt.options(selectinload(ChallengeParticipant.user))

        result = await self.db.execute(stmt)
        participants = list(result.scalars().all())

        # Update ranks
        for rank, participant in enumerate(participants, start=1):
            participant.rank = rank

        await self.db.commit()
        return participants
