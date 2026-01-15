"""
Feature Flags Service
Manages feature flags and A/B testing
"""

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.feature_flags import (
    ABTestExperiment,
    ExperimentAssignment,
    FeatureFlag,
    FlagEvaluation,
    FlagStatus,
)


class FeatureFlagsService:
    """Service for feature flags and A/B testing"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_flag(
        self,
        flag_key: str,
        flag_name: str,
        description: str | None = None,
        status: FlagStatus = FlagStatus.DISABLED,
        rollout_percentage: int = 0,
        target_users: list[int] | None = None,
        target_segments: list[str] | None = None,
        variants: dict[str, Any] | None = None,
        created_by_user_id: int | None = None,
    ) -> FeatureFlag:
        """Create a feature flag"""
        flag = FeatureFlag(
            flag_key=flag_key,
            flag_name=flag_name,
            description=description,
            status=status,
            rollout_percentage=rollout_percentage,
            target_users=target_users or [],
            target_segments=target_segments or [],
            variants=variants or {},
            created_by_user_id=created_by_user_id,
        )
        self.db.add(flag)
        await self.db.commit()
        await self.db.refresh(flag)
        return flag

    async def evaluate_flag(
        self,
        flag_key: str,
        user_id: int | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Evaluate a feature flag for a user

        Returns:
            Dictionary with enabled status and variant
        """
        stmt = select(FeatureFlag).where(FeatureFlag.flag_key == flag_key)
        result = await self.db.execute(stmt)
        flag = result.scalar_one_or_none()

        if not flag:
            return {"enabled": False, "variant": None}

        # Check if flag is enabled
        if flag.status == FlagStatus.DISABLED:
            enabled = False
            variant = None
        elif flag.status == FlagStatus.ENABLED:
            enabled = True
            variant = None
        elif flag.status == FlagStatus.ROLLING_OUT:
            # Check rollout percentage
            enabled = await self._check_rollout(flag, user_id)
            variant = None
        else:  # DEPRECATED
            enabled = False
            variant = None

        # Check targeting
        if enabled and user_id:
            if flag.target_users and user_id not in flag.target_users:
                enabled = False
            # Additional targeting logic can be added here

        # Log evaluation
        evaluation = FlagEvaluation(
            flag_id=flag.id,
            user_id=user_id,
            enabled=enabled,
            variant=variant,
            context=context or {},
        )
        self.db.add(evaluation)
        await self.db.commit()

        return {
            "enabled": enabled,
            "variant": variant,
            "flag_key": flag_key,
        }

    async def _check_rollout(self, flag: FeatureFlag, user_id: int | None) -> bool:
        """Check if user should get the feature based on rollout percentage"""
        if not user_id:
            # Anonymous users: use hash of session/IP
            return False

        # Consistent hashing based on user_id and flag_key
        hash_input = f"{flag.flag_key}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        user_percentage = (hash_value % 100) + 1

        return user_percentage <= flag.rollout_percentage

    async def get_flag_stats(
        self,
        flag_key: str,
        days: int = 7,
    ) -> dict[str, Any]:
        """Get feature flag statistics"""
        stmt = select(FeatureFlag).where(FeatureFlag.flag_key == flag_key)
        result = await self.db.execute(stmt)
        flag = result.scalar_one_or_none()

        if not flag:
            return {}

        # Get evaluation stats
        start_date = datetime.now(UTC) - timedelta(days=days)
        eval_stmt = select(
            func.count(FlagEvaluation.id).label("total_evaluations"),
            func.count(case((FlagEvaluation.enabled, 1))).label(
                "enabled_count"
            ),
        ).where(
            and_(
                FlagEvaluation.flag_id == flag.id,
                FlagEvaluation.created_at >= start_date,
            )
        )
        eval_result = await self.db.execute(eval_stmt)
        stats = eval_result.fetchone()

        total = stats.total_evaluations or 0
        enabled = stats.enabled_count or 0

        return {
            "flag_key": flag_key,
            "status": flag.status.value,
            "rollout_percentage": flag.rollout_percentage,
            "total_evaluations": total,
            "enabled_count": enabled,
            "enabled_percentage": (enabled / total * 100) if total > 0 else 0,
            "period_days": days,
        }

    # A/B Testing Methods
    async def create_experiment(
        self,
        flag_id: int,
        experiment_name: str,
        variants: dict[str, float],  # variant_name -> traffic_percentage
        primary_metric: str,
        description: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> ABTestExperiment:
        """Create an A/B test experiment"""
        experiment = ABTestExperiment(
            flag_id=flag_id,
            experiment_name=experiment_name,
            description=description,
            variants=variants,
            primary_metric=primary_metric,
            start_date=start_date or datetime.now(UTC),
            end_date=end_date,
            is_active=True,
        )
        self.db.add(experiment)
        await self.db.commit()
        await self.db.refresh(experiment)
        return experiment

    async def assign_variant(
        self,
        experiment_id: int,
        user_id: int,
    ) -> str:
        """
        Assign a variant to a user for an experiment

        Returns:
            Variant name assigned
        """
        # Check if already assigned
        stmt = select(ExperimentAssignment).where(
            and_(
                ExperimentAssignment.experiment_id == experiment_id,
                ExperimentAssignment.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return existing.variant

        # Get experiment
        experiment = await self.db.get(ABTestExperiment, experiment_id)
        if not experiment or not experiment.is_active:
            return "control"  # Default variant

        # Assign variant based on traffic split
        variant = await self._select_variant(experiment, user_id)

        assignment = ExperimentAssignment(
            experiment_id=experiment_id,
            user_id=user_id,
            variant=variant,
        )
        self.db.add(assignment)
        await self.db.commit()

        return variant

    async def _select_variant(
        self,
        experiment: ABTestExperiment,
        user_id: int,
    ) -> str:
        """Select variant for user using consistent hashing"""
        variants = experiment.variants

        # Consistent hashing
        hash_input = f"{experiment.id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        user_percentage = (hash_value % 100) + 1

        cumulative = 0
        for variant_name, percentage in variants.items():
            cumulative += percentage
            if user_percentage <= cumulative:
                return variant_name

        return "control"  # Default

    async def record_conversion(
        self,
        experiment_id: int,
        user_id: int,
        conversion_value: float | None = None,
    ) -> bool:
        """Record a conversion for an experiment"""
        stmt = select(ExperimentAssignment).where(
            and_(
                ExperimentAssignment.experiment_id == experiment_id,
                ExperimentAssignment.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        assignment = result.scalar_one_or_none()

        if not assignment:
            return False

        if not assignment.converted:
            assignment.converted = True
            assignment.converted_at = datetime.now(UTC)
            if conversion_value:
                assignment.conversion_value = conversion_value
            await self.db.commit()
            await self.db.refresh(assignment)
            return True

        return False

    async def get_experiment_results(
        self,
        experiment_id: int,
    ) -> dict[str, Any]:
        """Get A/B test experiment results"""
        experiment = await self.db.get(ABTestExperiment, experiment_id)
        if not experiment:
            return {}

        # Get assignments by variant
        stmt = (
            select(
                ExperimentAssignment.variant,
                func.count(ExperimentAssignment.id).label("total_assignments"),
                func.count(case((ExperimentAssignment.converted, 1))).label(
                    "conversions"
                ),
                func.sum(ExperimentAssignment.conversion_value).label("total_value"),
            )
            .where(ExperimentAssignment.experiment_id == experiment_id)
            .group_by(ExperimentAssignment.variant)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        variant_results = {}
        for row in rows:
            total = row.total_assignments or 0
            conversions = row.conversions or 0
            conversion_rate = (conversions / total * 100) if total > 0 else 0

            variant_results[row.variant] = {
                "total_assignments": total,
                "conversions": conversions,
                "conversion_rate": round(conversion_rate, 2),
                "total_value": float(row.total_value or 0),
            }

        # Calculate statistical significance (simplified)
        # In production, would use proper statistical tests (chi-square, t-test, etc.)

        return {
            "experiment_id": experiment_id,
            "experiment_name": experiment.experiment_name,
            "primary_metric": experiment.primary_metric,
            "variant_results": variant_results,
            "is_active": experiment.is_active,
        }
