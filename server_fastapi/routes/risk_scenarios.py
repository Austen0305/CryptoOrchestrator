from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from ..services.risk_scenarios import risk_scenario_service
from ..services.notification_service import NotificationService, NotificationCategory
from ..database import get_db_session
import jwt
import os

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer(auto_error=False)
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")


def get_notification_service(db: AsyncSession = Depends(get_db_session)) -> NotificationService:
    """Dependency to get NotificationService instance"""
    return NotificationService(db)


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """Optionally decode current user from JWT; returns None if no credentials provided."""
    if not credentials:
        return None
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("id")
        if not user_id:
            return None
        return {"id": user_id, "email": f"user{user_id}@example.com"}
    except Exception:
        return None


class ScenarioRequest(BaseModel):
    portfolio_value: float = Field(
        ..., gt=0, description="Total portfolio value in quote currency"
    )
    baseline_var: float = Field(
        ..., ge=0, description="Baseline VaR (absolute currency)"
    )
    shock_percent: float = Field(
        ..., ge=-1, le=1, description="Shock percentage, e.g. -0.12 for -12%"
    )
    horizon_days: int = Field(1, ge=1, le=365, description="Projection horizon in days")
    correlation_factor: float = Field(
        1.0, ge=0, le=5, description="Correlation amplification factor"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "portfolio_value": 100000,
                "baseline_var": 2500,
                "shock_percent": -0.1,
                "horizon_days": 7,
                "correlation_factor": 1.2,
            }
        }


class ScenarioResponse(BaseModel):
    portfolio_value: float
    baseline_var: float
    shock_percent: float
    correlation_factor: float
    horizon_days: int
    shocked_var: float
    projected_var: float
    stress_loss: float
    horizon_scale: float
    explanation: str


@router.post("/simulate", response_model=ScenarioResponse)
async def simulate_scenario(
    req: ScenarioRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    try:

        async def notify_fn(event: dict):
            if not current_user:
                return
            await notification_service.create_notification(
                user_id=current_user["id"],
                message="Risk scenario computed",
                level="info",
                title="Risk Scenario",
                category=NotificationCategory.RISK,
                data=event,
            )

        result = await risk_scenario_service.compute_scenario(
            portfolio_value=req.portfolio_value,
            current_var=req.baseline_var,
            shock_percent=req.shock_percent,
            horizon_days=req.horizon_days,
            correlation_factor=req.correlation_factor,
            notify=notify_fn if current_user else None,
        )
        return result
    except Exception as e:
        logger.error("Scenario simulation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
