import asyncio
import time
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RiskMetrics(BaseModel):
    portfolioRisk: float = Field(ge=0, le=100)
    maxDrawdown: float = Field(ge=0, le=1)
    var95: float = Field(ge=0, le=1)
    var99: float = Field(ge=0, le=1)
    sharpeRatio: float
    correlationScore: float = Field(ge=-1, le=1)
    diversificationRatio: float = Field(ge=0, le=1)
    exposureByAsset: Dict[str, float]
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
    def validate_type(cls, v: str):
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

    def __init__(self, db_session: Optional[AsyncSession] = None, ttl_seconds: int = 10):
        self.db = db_session
        self._limits: RiskLimits = RiskLimits()
        self._alerts: Dict[str, RiskAlert] = {}
        self._metrics_cache: Optional[RiskMetrics] = None
        self._metrics_cached_at: float = 0.0
        self._ttl = ttl_seconds
        self._lock = asyncio.Lock()
        # seed example alert
        self._alerts["drawdown"] = RiskAlert(
            id="drawdown",
            type="warning",
            message="Max drawdown approaching threshold",
            threshold=0.05,
            currentValue=0.042,
            timestamp=int(time.time() * 1000),
            acknowledged=False,
        )

    async def create_alert_db(
        self, user_id: str, alert_type: str, severity: str, message: str,
        current_value: Optional[float] = None, threshold_value: Optional[float] = None
    ):
        """Persist risk alert to database"""
        if not self.db:
            logger.warning("Database session not available for alert persistence")
            return None
        
        from ..models.risk_alert import RiskAlert as RiskAlertModel
        
        alert = RiskAlertModel(
            user_id=user_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            current_value=current_value,
            threshold_value=threshold_value,
        )
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        logger.info(f"Risk alert created: {alert.id} for user {user_id}")
        return alert
    
    async def get_user_alerts_db(self, user_id: str, limit: int = 50, unresolved_only: bool = False):
        """Retrieve user's risk alerts from database"""
        if not self.db:
            logger.warning("Database session not available")
            return []
        
        from ..models.risk_alert import RiskAlert as RiskAlertModel
        
        stmt = select(RiskAlertModel).where(RiskAlertModel.user_id == user_id)
        
        if unresolved_only:
            stmt = stmt.where(RiskAlertModel.resolved == False)
        
        stmt = stmt.order_by(RiskAlertModel.created_at.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def acknowledge_alert_db(self, alert_id: int):
        """Acknowledge a database alert"""
        if not self.db:
            logger.warning("Database session not available")
            return None
        
        from ..models.risk_alert import RiskAlert as RiskAlertModel
        
        stmt = update(RiskAlertModel).where(
            RiskAlertModel.id == alert_id
        ).values(
            acknowledged=True,
            acknowledged_at=datetime.utcnow()
        )
        
        await self.db.execute(stmt)
        await self.db.commit()
        logger.info(f"Alert {alert_id} acknowledged")
        return True
    
    async def set_risk_limit_db(self, user_id: str, limit_type: str, value: float):
        """Set or update risk limit in database"""
        if not self.db:
            logger.warning("Database session not available")
            return None
        
        from ..models.risk_limit import RiskLimit as RiskLimitModel
        
        # Check if limit exists
        stmt = select(RiskLimitModel).where(
            RiskLimitModel.user_id == user_id,
            RiskLimitModel.limit_type == limit_type
        )
        result = await self.db.execute(stmt)
        limit = result.scalar_one_or_none()
        
        if limit:
            limit.value = value
            limit.updated_at = datetime.utcnow()
        else:
            limit = RiskLimitModel(
                user_id=user_id,
                limit_type=limit_type,
                value=value
            )
            self.db.add(limit)
        
        await self.db.commit()
        await self.db.refresh(limit)
        logger.info(f"Risk limit set: {limit_type}={value} for user {user_id}")
        return limit
    
    async def get_user_limits_db(self, user_id: str):
        """Get all risk limits for a user"""
        if not self.db:
            logger.warning("Database session not available")
            return []
        
        from ..models.risk_limit import RiskLimit as RiskLimitModel
        
        stmt = select(RiskLimitModel).where(
            RiskLimitModel.user_id == user_id,
            RiskLimitModel.enabled == True
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_limits(self) -> RiskLimits:
        return self._limits

    async def update_limits(self, updates: Dict) -> RiskLimits:
        # basic validation is enforced by Pydantic on construction
        async with self._lock:
            self._limits = self._limits.model_copy(update=updates)
            return self._limits

    async def acknowledge_alert(self, alert_id: str) -> RiskAlert:
        async with self._lock:
            alert = self._alerts.get(alert_id)
            if not alert:
                raise KeyError(alert_id)
            alert.acknowledged = True
            self._alerts[alert_id] = alert
            return alert

    async def get_alerts(self) -> List[RiskAlert]:
        return list(self._alerts.values())

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


# Singleton accessor matching project pattern
_risk_service_instance: Optional[RiskService] = None


def get_risk_service() -> RiskService:
    global _risk_service_instance
    if _risk_service_instance is None:
        _risk_service_instance = RiskService()
    return _risk_service_instance
