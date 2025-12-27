"""
User Analytics Service
Manages user behavior tracking, feature usage, conversion funnels, and user journeys
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload

from ..models.user_analytics import (
    UserEvent,
    FeatureUsage,
    ConversionFunnel,
    UserJourney,
    UserSatisfaction,
)


class UserAnalyticsService:
    """Service for managing user analytics"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # User Event Methods
    async def track_event(
        self,
        user_id: Optional[int],
        session_id: Optional[str],
        event_type: str,
        event_name: str,
        event_category: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        page_url: Optional[str] = None,
        page_title: Optional[str] = None,
        referrer: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        device_type: Optional[str] = None,
        browser: Optional[str] = None,
        os: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> UserEvent:
        """Track a user event"""
        event = UserEvent(
            user_id=user_id,
            session_id=session_id,
            event_type=event_type,
            event_name=event_name,
            event_category=event_category,
            properties=properties or {},
            page_url=page_url,
            page_title=page_title,
            referrer=referrer,
            user_agent=user_agent,
            ip_address=ip_address,
            device_type=device_type,
            browser=browser,
            os=os,
            duration_ms=duration_ms,
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def get_user_events(
        self,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        event_type: Optional[str] = None,
        event_category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[UserEvent]:
        """Get user events with filtering"""
        stmt = select(UserEvent)

        if user_id:
            stmt = stmt.where(UserEvent.user_id == user_id)
        if session_id:
            stmt = stmt.where(UserEvent.session_id == session_id)
        if event_type:
            stmt = stmt.where(UserEvent.event_type == event_type)
        if event_category:
            stmt = stmt.where(UserEvent.event_category == event_category)
        if start_date:
            stmt = stmt.where(UserEvent.created_at >= start_date)
        if end_date:
            stmt = stmt.where(UserEvent.created_at <= end_date)

        stmt = stmt.order_by(UserEvent.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_event_analytics(
        self,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get aggregated event analytics"""
        stmt = select(
            UserEvent.event_type,
            func.count(UserEvent.id).label("count"),
            func.avg(UserEvent.duration_ms).label("avg_duration"),
        )

        if event_type:
            stmt = stmt.where(UserEvent.event_type == event_type)
        if start_date:
            stmt = stmt.where(UserEvent.created_at >= start_date)
        if end_date:
            stmt = stmt.where(UserEvent.created_at <= end_date)

        stmt = stmt.group_by(UserEvent.event_type)

        result = await self.db.execute(stmt)
        rows = result.all()

        return {
            "event_types": [
                {
                    "event_type": row.event_type,
                    "count": row.count,
                    "avg_duration_ms": float(row.avg_duration) if row.avg_duration else None,
                }
                for row in rows
            ],
            "total_events": sum(row.count for row in rows),
        }

    # Feature Usage Methods
    async def track_feature_usage(
        self,
        user_id: int,
        feature_name: str,
        action: str,
        feature_category: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        success: bool = True,
        properties: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> FeatureUsage:
        """Track feature usage"""
        usage = FeatureUsage(
            user_id=user_id,
            feature_name=feature_name,
            feature_category=feature_category,
            action=action,
            duration_seconds=duration_seconds,
            success=success,
            properties=properties or {},
            error_message=error_message,
        )
        self.db.add(usage)
        await self.db.commit()
        await self.db.refresh(usage)
        return usage

    async def get_feature_usage_stats(
        self,
        feature_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get feature usage statistics"""
        stmt = select(
            FeatureUsage.feature_name,
            func.count(FeatureUsage.id).label("total_uses"),
            func.count(case((FeatureUsage.success == True, 1))).label("successful_uses"),
            func.avg(FeatureUsage.duration_seconds).label("avg_duration"),
            func.count(func.distinct(FeatureUsage.user_id)).label("unique_users"),
        )

        if feature_name:
            stmt = stmt.where(FeatureUsage.feature_name == feature_name)
        if start_date:
            stmt = stmt.where(FeatureUsage.created_at >= start_date)
        if end_date:
            stmt = stmt.where(FeatureUsage.created_at <= end_date)

        stmt = stmt.group_by(FeatureUsage.feature_name)

        result = await self.db.execute(stmt)
        rows = result.all()

        return {
            "features": [
                {
                    "feature_name": row.feature_name,
                    "total_uses": row.total_uses,
                    "successful_uses": row.successful_uses,
                    "success_rate": float(row.successful_uses / row.total_uses * 100) if row.total_uses > 0 else 0,
                    "avg_duration_seconds": float(row.avg_duration) if row.avg_duration else None,
                    "unique_users": row.unique_users,
                }
                for row in rows
            ],
        }

    # Conversion Funnel Methods
    async def track_funnel_stage(
        self,
        user_id: Optional[int],
        session_id: Optional[str],
        funnel_name: str,
        stage: str,
        stage_order: int,
        time_to_stage_seconds: Optional[int] = None,
        time_in_stage_seconds: Optional[int] = None,
        properties: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> ConversionFunnel:
        """Track a conversion funnel stage"""
        funnel = ConversionFunnel(
            user_id=user_id,
            session_id=session_id,
            funnel_name=funnel_name,
            stage=stage,
            stage_order=stage_order,
            time_to_stage_seconds=time_to_stage_seconds,
            time_in_stage_seconds=time_in_stage_seconds,
            properties=properties or {},
            source=source,
        )
        self.db.add(funnel)
        await self.db.commit()
        await self.db.refresh(funnel)
        return funnel

    async def complete_funnel(
        self,
        user_id: Optional[int],
        session_id: Optional[str],
        funnel_name: str,
    ) -> bool:
        """Mark a funnel as completed"""
        # Get the latest funnel entry
        stmt = select(ConversionFunnel).where(
            and_(
                ConversionFunnel.funnel_name == funnel_name,
                or_(
                    ConversionFunnel.user_id == user_id if user_id else False,
                    ConversionFunnel.session_id == session_id if session_id else False,
                ),
                ConversionFunnel.is_completed == False,
            )
        ).order_by(ConversionFunnel.created_at.desc()).limit(1)

        result = await self.db.execute(stmt)
        funnel = result.scalar_one_or_none()

        if funnel:
            funnel.is_completed = True
            funnel.completed_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(funnel)
            return True

        return False

    async def get_funnel_analytics(
        self,
        funnel_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get conversion funnel analytics"""
        stmt = select(
            ConversionFunnel.stage,
            ConversionFunnel.stage_order,
            func.count(ConversionFunnel.id).label("users_reached"),
            func.count(case((ConversionFunnel.is_completed == True, 1))).label("users_completed"),
            func.avg(ConversionFunnel.time_to_stage_seconds).label("avg_time_to_stage"),
            func.avg(ConversionFunnel.time_in_stage_seconds).label("avg_time_in_stage"),
        ).where(ConversionFunnel.funnel_name == funnel_name)

        if start_date:
            stmt = stmt.where(ConversionFunnel.created_at >= start_date)
        if end_date:
            stmt = stmt.where(ConversionFunnel.created_at <= end_date)

        stmt = stmt.group_by(ConversionFunnel.stage, ConversionFunnel.stage_order)
        stmt = stmt.order_by(ConversionFunnel.stage_order)

        result = await self.db.execute(stmt)
        rows = result.all()

        stages = []
        previous_count = None
        for row in rows:
            conversion_rate = (
                float(row.users_reached / previous_count * 100)
                if previous_count and previous_count > 0
                else 100.0
            )
            stages.append({
                "stage": row.stage,
                "stage_order": row.stage_order,
                "users_reached": row.users_reached,
                "users_completed": row.users_completed,
                "conversion_rate": conversion_rate,
                "drop_off_rate": 100.0 - conversion_rate if previous_count else 0.0,
                "avg_time_to_stage_seconds": float(row.avg_time_to_stage) if row.avg_time_to_stage else None,
                "avg_time_in_stage_seconds": float(row.avg_time_in_stage) if row.avg_time_in_stage else None,
            })
            previous_count = row.users_reached

        total_started = stages[0]["users_reached"] if stages else 0
        total_completed = sum(s["users_completed"] for s in stages)

        return {
            "funnel_name": funnel_name,
            "stages": stages,
            "total_started": total_started,
            "total_completed": total_completed,
            "overall_conversion_rate": (
                float(total_completed / total_started * 100) if total_started > 0 else 0.0
            ),
        }

    # User Journey Methods
    async def track_journey_step(
        self,
        user_id: Optional[int],
        session_id: str,
        journey_type: str,
        step_name: str,
        step_order: int,
        previous_step: Optional[str] = None,
        next_step: Optional[str] = None,
        path: Optional[List[str]] = None,
        time_to_step_seconds: Optional[int] = None,
        time_in_step_seconds: Optional[int] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> UserJourney:
        """Track a user journey step"""
        journey = UserJourney(
            user_id=user_id,
            session_id=session_id,
            journey_type=journey_type,
            step_name=step_name,
            step_order=step_order,
            previous_step=previous_step,
            next_step=next_step,
            path=path or [],
            time_to_step_seconds=time_to_step_seconds,
            time_in_step_seconds=time_in_step_seconds,
            properties=properties or {},
        )
        self.db.add(journey)
        await self.db.commit()
        await self.db.refresh(journey)
        return journey

    async def complete_journey(
        self,
        session_id: str,
        journey_type: str,
    ) -> bool:
        """Mark a journey as completed"""
        stmt = select(UserJourney).where(
            and_(
                UserJourney.session_id == session_id,
                UserJourney.journey_type == journey_type,
                UserJourney.is_completed == False,
            )
        ).order_by(UserJourney.created_at.desc()).limit(1)

        result = await self.db.execute(stmt)
        journey = result.scalar_one_or_none()

        if journey:
            journey.is_completed = True
            journey.completed_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(journey)
            return True

        return False

    async def get_journey_analytics(
        self,
        journey_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get user journey analytics"""
        stmt = select(
            UserJourney.journey_type,
            UserJourney.step_name,
            func.count(UserJourney.id).label("step_count"),
            func.count(func.distinct(UserJourney.session_id)).label("unique_sessions"),
            func.avg(UserJourney.time_in_step_seconds).label("avg_time_in_step"),
            func.count(case((UserJourney.is_completed == True, 1))).label("completed_count"),
        )

        if journey_type:
            stmt = stmt.where(UserJourney.journey_type == journey_type)
        if start_date:
            stmt = stmt.where(UserJourney.created_at >= start_date)
        if end_date:
            stmt = stmt.where(UserJourney.created_at <= end_date)

        stmt = stmt.group_by(UserJourney.journey_type, UserJourney.step_name)

        result = await self.db.execute(stmt)
        rows = result.all()

        return {
            "journeys": [
                {
                    "journey_type": row.journey_type,
                    "step_name": row.step_name,
                    "step_count": row.step_count,
                    "unique_sessions": row.unique_sessions,
                    "avg_time_in_step_seconds": float(row.avg_time_in_step) if row.avg_time_in_step else None,
                    "completed_count": row.completed_count,
                }
                for row in rows
            ],
        }

    # User Satisfaction Methods
    async def record_satisfaction(
        self,
        user_id: Optional[int],
        survey_type: str,
        score: int,
        question: Optional[str] = None,
        response: Optional[str] = None,
        context: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> UserSatisfaction:
        """Record user satisfaction score"""
        satisfaction = UserSatisfaction(
            user_id=user_id,
            survey_type=survey_type,
            score=score,
            question=question,
            response=response,
            context=context,
            properties=properties or {},
        )
        self.db.add(satisfaction)
        await self.db.commit()
        await self.db.refresh(satisfaction)
        return satisfaction

    async def get_satisfaction_metrics(
        self,
        survey_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get user satisfaction metrics"""
        stmt = select(
            UserSatisfaction.survey_type,
            func.count(UserSatisfaction.id).label("total_responses"),
            func.avg(UserSatisfaction.score).label("avg_score"),
            func.min(UserSatisfaction.score).label("min_score"),
            func.max(UserSatisfaction.score).label("max_score"),
        )

        if survey_type:
            stmt = stmt.where(UserSatisfaction.survey_type == survey_type)
        if start_date:
            stmt = stmt.where(UserSatisfaction.created_at >= start_date)
        if end_date:
            stmt = stmt.where(UserSatisfaction.created_at <= end_date)

        stmt = stmt.group_by(UserSatisfaction.survey_type)

        result = await self.db.execute(stmt)
        rows = result.all()

        return {
            "satisfaction_metrics": [
                {
                    "survey_type": row.survey_type,
                    "total_responses": row.total_responses,
                    "avg_score": float(row.avg_score) if row.avg_score else None,
                    "min_score": row.min_score,
                    "max_score": row.max_score,
                }
                for row in rows
            ],
        }
