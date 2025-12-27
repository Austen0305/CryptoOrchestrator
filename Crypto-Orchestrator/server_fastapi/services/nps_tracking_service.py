"""
NPS Tracking Service
Tracks and analyzes Net Promoter Score (NPS) and other satisfaction metrics
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case

from ..models.user_analytics import UserSatisfaction

logger = logging.getLogger(__name__)


class NPSTrackingService:
    """Service for tracking and analyzing NPS"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_nps(
        self,
        user_id: Optional[int],
        score: int,
        response: Optional[str] = None,
        context: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> UserSatisfaction:
        """Record an NPS score"""
        if score < 0 or score > 10:
            raise ValueError("NPS score must be between 0 and 10")

        satisfaction = UserSatisfaction(
            user_id=user_id,
            survey_type="nps",
            score=score,
            question="How likely are you to recommend CryptoOrchestrator to a friend or colleague?",
            response=response,
            context=context,
            properties=properties or {},
        )

        self.db.add(satisfaction)
        await self.db.commit()
        await self.db.refresh(satisfaction)
        return satisfaction

    async def calculate_nps(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Calculate NPS score and breakdown"""
        try:
            stmt = select(UserSatisfaction).where(UserSatisfaction.survey_type == "nps")

            if start_date:
                stmt = stmt.where(UserSatisfaction.created_at >= start_date)
            if end_date:
                stmt = stmt.where(UserSatisfaction.created_at <= end_date)

            result = await self.db.execute(stmt)
            responses = list(result.scalars().all())

            if not responses:
                return {
                    "nps_score": 0,
                    "total_responses": 0,
                    "promoters": 0,
                    "passives": 0,
                    "detractors": 0,
                    "promoter_percentage": 0.0,
                    "passive_percentage": 0.0,
                    "detractor_percentage": 0.0,
                }

            # Categorize responses
            promoters = sum(1 for r in responses if r.score >= 9)
            passives = sum(1 for r in responses if 7 <= r.score <= 8)
            detractors = sum(1 for r in responses if r.score <= 6)

            total = len(responses)

            # Calculate NPS: % Promoters - % Detractors
            promoter_percentage = (promoters / total * 100) if total > 0 else 0
            detractor_percentage = (detractors / total * 100) if total > 0 else 0
            nps_score = promoter_percentage - detractor_percentage

            return {
                "nps_score": round(nps_score, 2),
                "total_responses": total,
                "promoters": promoters,
                "passives": passives,
                "detractors": detractors,
                "promoter_percentage": round(promoter_percentage, 2),
                "passive_percentage": round((passives / total * 100) if total > 0 else 0, 2),
                "detractor_percentage": round(detractor_percentage, 2),
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error calculating NPS: {e}", exc_info=True)
            return {
                "nps_score": 0,
                "total_responses": 0,
                "error": str(e),
            }

    async def get_nps_trend(
        self, days: int = 30, period: str = "daily"
    ) -> List[Dict[str, Any]]:
        """Get NPS trend over time"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            if period == "daily":
                date_func = func.date(UserSatisfaction.created_at)
            elif period == "weekly":
                date_func = func.date_trunc("week", UserSatisfaction.created_at)
            else:  # monthly
                date_func = func.date_trunc("month", UserSatisfaction.created_at)

            stmt = (
                select(
                    date_func.label("period"),
                    func.count(UserSatisfaction.id).label("total"),
                    func.sum(case((UserSatisfaction.score >= 9, 1), else_=0)).label(
                        "promoters"
                    ),
                    func.sum(case((and_(UserSatisfaction.score >= 7, UserSatisfaction.score <= 8), 1), else_=0)).label(
                        "passives"
                    ),
                    func.sum(case((UserSatisfaction.score <= 6, 1), else_=0)).label(
                        "detractors"
                    ),
                )
                .where(UserSatisfaction.survey_type == "nps")
                .where(UserSatisfaction.created_at >= start_date)
                .group_by(date_func)
                .order_by(date_func)
            )

            result = await self.db.execute(stmt)
            rows = result.all()

            trends = []
            for row in rows:
                total = row.total or 0
                promoters = row.promoters or 0
                detractors = row.detractors or 0

                if total > 0:
                    nps = ((promoters / total) - (detractors / total)) * 100
                else:
                    nps = 0

                trends.append(
                    {
                        "period": (
                            row.period.isoformat()
                            if hasattr(row.period, "isoformat")
                            else str(row.period)
                        ),
                        "nps_score": round(nps, 2),
                        "total_responses": total,
                        "promoters": promoters,
                        "passives": row.passives or 0,
                        "detractors": detractors,
                    }
                )

            return trends
        except Exception as e:
            logger.error(f"Error getting NPS trend: {e}", exc_info=True)
            return []

    async def get_nps_breakdown(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get detailed NPS breakdown with feedback"""
        try:
            nps_data = await self.calculate_nps(start_date, end_date)

            # Get sample feedback
            stmt = select(UserSatisfaction).where(UserSatisfaction.survey_type == "nps")
            if start_date:
                stmt = stmt.where(UserSatisfaction.created_at >= start_date)
            if end_date:
                stmt = stmt.where(UserSatisfaction.created_at <= end_date)

            # Get feedback samples
            stmt_promoters = stmt.where(UserSatisfaction.score >= 9).limit(5)
            stmt_detractors = stmt.where(UserSatisfaction.score <= 6).limit(5)

            promoters_result = await self.db.execute(stmt_promoters)
            detractors_result = await self.db.execute(stmt_detractors)

            promoter_feedback = [
                {"score": r.score, "response": r.response}
                for r in promoters_result.scalars().all()
                if r.response
            ]
            detractor_feedback = [
                {"score": r.score, "response": r.response}
                for r in detractors_result.scalars().all()
                if r.response
            ]

            return {
                **nps_data,
                "sample_feedback": {
                    "promoters": promoter_feedback,
                    "detractors": detractor_feedback,
                },
            }
        except Exception as e:
            logger.error(f"Error getting NPS breakdown: {e}", exc_info=True)
            return {"error": str(e)}
