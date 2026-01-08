import asyncio
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..repositories.risk_repository import RiskRepository
import logging

from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.risk_repository import RiskRepository

logger = logging.getLogger(__name__)


class RiskMetrics(BaseModel):
    portfolioRisk: float = Field(ge=0, le=100)
    maxDrawdown: float = Field(ge=0, le=1)
    var95: float = Field(ge=0, le=1)
    var99: float = Field(ge=0, le=1)
    sharpeRatio: float
    correlationScore: float = Field(ge=-1, le=1)
    diversificationRatio: float = Field(ge=0, le=1)
    exposureByAsset: dict[str, float]
    leverageRisk: float = Field(ge=0, le=1)
    liquidityRisk: float = Field(ge=0, le=1)
    concentrationRisk: float = Field(ge=0, le=1)


class RiskAlert(BaseModel):
    id: str
    type: str  # 'warning' | 'critical' | 'info'
    message: str
    threshold: float
    currentValue: float
    timestamp: int
    acknowledged: bool = False

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"warning", "critical", "info"}
        if v not in allowed:
            raise ValueError("type must be one of 'warning' | 'critical' | 'info'")
        return v


class RiskLimits(BaseModel):
    maxPositionSize: float = Field(10, ge=0, le=100)
    maxDailyLoss: float = Field(3, ge=0, le=100)
    maxPortfolioRisk: float = Field(60, ge=0, le=100)
    maxLeverage: int = Field(3, ge=1, le=10)
    maxCorrelation: float = Field(0.8, ge=0, le=1)
    minDiversification: float = Field(0.4, ge=0, le=1)


class RiskService:
    """Enhanced risk management service with database persistence."""

    FIELD_TO_LIMIT_TYPE = {
        "maxPositionSize": "max_position_size",
        "maxDailyLoss": "max_daily_loss",
        "maxPortfolioRisk": "max_portfolio_risk",
        "maxLeverage": "max_leverage",
        "maxCorrelation": "max_correlation",
        "minDiversification": "min_diversification",
    }
    LIMIT_TYPE_TO_FIELD = {value: key for key, value in FIELD_TO_LIMIT_TYPE.items()}

    def __init__(
        self, db_session: AsyncSession | None = None, ttl_seconds: int = 10
    ) -> None:
        # ✅ Repository created internally (Service Layer Pattern)
        self.risk_repository = RiskRepository()
        self.db = db_session  # Keep db for transaction handling
        # Default limits - used as base when no user-specific limits exist in DB
        self._default_limits: RiskLimits = RiskLimits()
        # In-memory storage only used as fallback when DB is unavailable (e.g., tests)
        self._alerts: dict[str, RiskAlert] = {}
        self._metrics_cache: RiskMetrics | None = None
        self._metrics_cached_at: float = 0.0
        self._ttl = ttl_seconds
        self._lock = asyncio.Lock()
        # Risk persistence service for database operations
        from .risk_persistence import RiskPersistenceService

        self._persistence: RiskPersistenceService | None = None
        if db_session:
            self._persistence = RiskPersistenceService(db_session)
        # Redis cache for risk data (with memory fallback)
        self._cache = None
        self._init_cache()
        # Note: No longer seeding example alerts - all alerts should come from database

    def _init_cache(self):
        """Initialize Redis cache with memory fallback"""
        try:
            import os

            from ..utils.cache_utils import MultiLevelCache

            redis_url = os.getenv("REDIS_URL")
            # MultiLevelCache handles Redis availability checking
            self._cache = MultiLevelCache(redis_url=redis_url)
        except Exception as e:
            logger.warning(f"Failed to initialize cache: {e}, using in-memory only")
            self._cache = None

    async def create_alert_db(
        self,
        user_id: str,
        alert_type: str,
        severity: str,
        message: str,
        current_value: float | None = None,
        threshold_value: float | None = None,
    ):
        """Persist risk alert to database with cache invalidation"""
        if not self.db:
            logger.warning(
                "Database session not available for alert persistence",
                extra={"user_id": user_id},
            )
            return None

        # ✅ Data access delegated to repository
        alert = await self.risk_repository.create_alert(
            self.db,
            user_id=user_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            current_value=current_value,
            threshold_value=threshold_value,
        )
        logger.info(
            f"Risk alert created: {alert.id} for user {user_id}",
            extra={"alert_id": alert.id, "user_id": user_id, "alert_type": alert_type},
        )

        # Invalidate alerts cache for this user
        if self._cache:
            try:
                await self._cache.delete(f"risk:alerts:{user_id}:all")
                await self._cache.delete(f"risk:alerts:{user_id}:unresolved")
            except Exception as e:
                logger.warning(f"Cache deletion error: {e}", extra={"user_id": user_id})

        return alert

    async def get_user_alerts_db(
        self, user_id: str, limit: int = 50, unresolved_only: bool = False
    ) -> list[Any]:
        """Retrieve user's risk alerts from database"""
        if not self.db:
            logger.warning("Database session not available", extra={"user_id": user_id})
            return []

        # ✅ Data access delegated to repository
        alerts = await self.risk_repository.get_user_alerts(
            self.db,
            user_id=user_id,
            resolved=False if unresolved_only else None,
            limit=limit,
        )
        return alerts

    async def acknowledge_alert_db(self, alert_id: int):
        """Acknowledge a database alert"""
        if not self.db:
            logger.warning(
                "Database session not available", extra={"alert_id": alert_id}
            )
            return None

        # ✅ Data access delegated to repository
        alert = await self.risk_repository.acknowledge_alert(self.db, alert_id)
        if alert:
            logger.info(
                f"Alert {alert_id} acknowledged",
                extra={"alert_id": alert_id, "user_id": alert.user_id},
            )
            return True
        return None

    async def set_risk_limit_db(
        self, user_id: str, limit_type: str, value: float
    ) -> Any | None:
        """Set or update risk limit in database"""
        if not self.db:
            logger.warning(
                "Database session not available",
                extra={"user_id": user_id, "limit_type": limit_type},
            )
            return None

        # ✅ Data access delegated to repository
        limit = await self.risk_repository.create_or_update_limit(
            self.db,
            user_id=user_id,
            limit_type=limit_type,
            value=value,
            enabled=True,
        )
        return limit

    async def get_user_limits_db(self, user_id: str):
        """Get all risk limits for a user"""
        if not self.db:
            logger.warning("Database session not available", extra={"user_id": user_id})
            return []

        # ✅ Data access delegated to repository
        limits = await self.risk_repository.get_user_limits(self.db, user_id)
        return limits

    async def get_limits(self) -> RiskLimits:
        return self._default_limits

    async def update_limits(self, updates: dict) -> RiskLimits:
        # Maintain default limits reference
        async with self._lock:
            self._default_limits = self._default_limits.model_copy(update=updates)
            return self._default_limits

    def _serialize_db_alert(self, alert_model: Any) -> RiskAlert:
        timestamp = (
            int(alert_model.created_at.timestamp() * 1000)
            if getattr(alert_model, "created_at", None)
            else int(time.time() * 1000)
        )
        return RiskAlert(
            id=str(alert_model.id),
            type=alert_model.alert_type,
            message=alert_model.message,
            threshold=alert_model.threshold_value or 0.0,
            currentValue=alert_model.current_value or 0.0,
            timestamp=timestamp,
            acknowledged=bool(alert_model.acknowledged),
        )

    async def get_user_alerts(
        self, user_id: str, unresolved_only: bool = False
    ) -> list[RiskAlert]:
        """Get user alerts with Redis caching"""
        # Try cache first
        cache_key = (
            f"risk:alerts:{user_id}:{'unresolved' if unresolved_only else 'all'}"
        )
        if self._cache:
            try:
                cached = await self._cache.get(cache_key)
                if cached is not None:
                    return cached
            except Exception as e:
                logger.warning(f"Cache get error: {e}")

        # ✅ Fallback to database or in-memory
        if not self.db:
            return list(self._alerts.values())

        alerts = await self.get_user_alerts_db(
            user_id,
            limit=1000,  # Get all alerts for serialization
            unresolved_only=unresolved_only,
        )
        serialized = [self._serialize_db_alert(alert) for alert in alerts]

        # Cache the result
        if self._cache:
            try:
                await self._cache.set(
                    cache_key, serialized, ttl=60
                )  # Cache for 1 minute
            except Exception as e:
                logger.warning(f"Cache set error: {e}")

        return serialized

    async def get_user_limits(self, user_id: str) -> RiskLimits:
        """Get user limits with Redis caching"""
        # Try cache first
        cache_key = f"risk:limits:{user_id}"
        if self._cache:
            try:
                cached = await self._cache.get(cache_key)
                if cached is not None:
                    return RiskLimits(**cached)
            except Exception as e:
                logger.warning(f"Cache get error: {e}")

        # Fallback to database or defaults
        base = self._default_limits.model_dump()
        if not self.db:
            return RiskLimits(**base)

        db_limits = await self.get_user_limits_db(user_id)
        for limit in db_limits:
            field = self.LIMIT_TYPE_TO_FIELD.get(limit.limit_type)
            if field:
                base[field] = limit.value

        result = RiskLimits(**base)

        # Cache the result
        if self._cache:
            try:
                await self._cache.set(cache_key, base, ttl=300)  # Cache for 5 minutes
            except Exception as e:
                logger.warning(f"Cache set error: {e}")

        return result

    async def update_user_limits(
        self, user_id: str, updates: dict[str, float]
    ) -> RiskLimits:
        """Update user limits with cache invalidation"""
        if not updates:
            return await self.get_user_limits(user_id)

        if self.db:
            for field, value in updates.items():
                limit_type = self.FIELD_TO_LIMIT_TYPE.get(field)
                if limit_type:
                    await self.set_risk_limit_db(user_id, limit_type, value)
        else:
            await self.update_limits(updates)

        # Invalidate cache
        cache_key = f"risk:limits:{user_id}"
        if self._cache:
            try:
                await self._cache.delete(cache_key)
            except Exception as e:
                logger.warning(f"Cache deletion error: {e}")

        return await self.get_user_limits(user_id)

    async def acknowledge_alert(self, alert_id: str, user_id: str) -> RiskAlert:
        """Acknowledge an alert - prefers database if available"""
        if self.db:
            # ✅ Use database method
            alert_id_int = int(alert_id) if alert_id.isdigit() else None
            if alert_id_int:
                await self.acknowledge_alert_db(alert_id_int)
                # ✅ Return updated alert from database using repository
                alert_model = await self.risk_repository.get_alert_by_id(
                    self.db, alert_id_int
                )
                if alert_model:
                    return self._serialize_db_alert(alert_model)
            raise KeyError(f"Alert {alert_id} not found")

        # Fallback to in-memory (only when DB unavailable)
        async with self._lock:
            alert = self._alerts.get(alert_id)
            if not alert:
                raise KeyError(alert_id)
            alert.acknowledged = True
            self._alerts[alert_id] = alert
            return alert

    async def get_alerts(self, user_id: str | None = None) -> list[RiskAlert]:
        """Get alerts - prefers database if available and user_id provided"""
        if self.db and user_id:
            return await self.get_user_alerts(user_id)
        # Fallback to in-memory (only when DB unavailable or no user_id)
        return list(self._alerts.values())

    async def create_alert(
        self,
        user_id: str,
        alert_type: str,
        severity: str,
        message: str,
        current_value: float | None = None,
        threshold_value: float | None = None,
    ) -> RiskAlert | None:
        """
        Create a risk alert - uses database by default, falls back to in-memory if DB unavailable.
        This is a convenience method that automatically uses the appropriate storage.
        """
        # Always prefer database when available
        if self.db:
            alert_model = await self.create_alert_db(
                user_id=user_id,
                alert_type=alert_type,
                severity=severity,
                message=message,
                current_value=current_value,
                threshold_value=threshold_value,
            )
            if alert_model:
                return self._serialize_db_alert(alert_model)
            return None

        # Fallback to in-memory only when DB is unavailable (e.g., tests)
        import time
        import uuid

        alert = RiskAlert(
            id=str(uuid.uuid4()),
            type=alert_type,
            message=message,
            threshold=threshold_value or 0.0,
            currentValue=current_value or 0.0,
            timestamp=int(time.time() * 1000),
            acknowledged=False,
        )
        async with self._lock:
            self._alerts[alert.id] = alert
        logger.warning(f"Alert created in-memory (DB unavailable): {alert.id}")
        return alert

    async def get_metrics(self) -> RiskMetrics:
        now = time.time()
        if self._metrics_cache and (now - self._metrics_cached_at) < self._ttl:
            return self._metrics_cache

        # In a real implementation, compute using market data and portfolio state.
        metrics = RiskMetrics(
            portfolioRisk=47.5,
            maxDrawdown=0.038,
            var95=0.021,
            var99=0.036,
            sharpeRatio=1.12,
            correlationScore=0.42,
            diversificationRatio=0.58,
            exposureByAsset={
                "BTC": 0.45,
                "ETH": 0.30,
                "SOL": 0.15,
                "USDT": 0.10,
            },
            leverageRisk=0.25,
            liquidityRisk=0.18,
            concentrationRisk=0.33,
        )

        self._metrics_cache = metrics
        self._metrics_cached_at = now
        return metrics
