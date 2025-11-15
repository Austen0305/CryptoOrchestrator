from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging
from pydantic import BaseModel
from ..services.risk_service import get_risk_service, RiskService, RiskLimits, RiskAlert, RiskMetrics

logger = logging.getLogger(__name__)

router = APIRouter()


def risk_service_dep() -> RiskService:
    return get_risk_service()


class UpdateLimitsRequest(BaseModel):
    maxPositionSize: float | None = None
    maxDailyLoss: float | None = None
    maxPortfolioRisk: float | None = None
    maxLeverage: int | None = None
    maxCorrelation: float | None = None
    minDiversification: float | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "maxPositionSize": 15,
                "maxDailyLoss": 5,
                "maxPortfolioRisk": 55,
                "maxLeverage": 4,
                "maxCorrelation": 0.75,
                "minDiversification": 0.5
            }
        }
    }


@router.get("/metrics", response_model=RiskMetrics)
async def get_metrics(svc: RiskService = Depends(risk_service_dep)):
    return await svc.get_metrics()


@router.get("/alerts", response_model=list[RiskAlert])
async def get_alerts(svc: RiskService = Depends(risk_service_dep)):
    return await svc.get_alerts()


@router.get("/limits", response_model=RiskLimits)
async def get_limits(svc: RiskService = Depends(risk_service_dep)):
    return await svc.get_limits()


@router.post("/limits", response_model=RiskLimits)
async def update_limits(payload: UpdateLimitsRequest, svc: RiskService = Depends(risk_service_dep)):
    # Manual validation to enforce reasonable ranges beyond model bounds if needed
    updates: Dict[str, Any] = {}
    for field, value in payload.model_dump(exclude_none=True).items():
        if field == "maxPositionSize" and not (0 <= value <= 100):
            raise HTTPException(status_code=400, detail="maxPositionSize out of range (0-100)")
        if field == "maxDailyLoss" and not (0 <= value <= 100):
            raise HTTPException(status_code=400, detail="maxDailyLoss out of range (0-100)")
        if field == "maxPortfolioRisk" and not (0 <= value <= 100):
            raise HTTPException(status_code=400, detail="maxPortfolioRisk out of range (0-100)")
        if field == "maxLeverage" and not (1 <= value <= 10):
            raise HTTPException(status_code=400, detail="maxLeverage out of range (1-10)")
        if field == "maxCorrelation" and not (0 <= value <= 1):
            raise HTTPException(status_code=400, detail="maxCorrelation out of range (0-1)")
        if field == "minDiversification" and not (0 <= value <= 1):
            raise HTTPException(status_code=400, detail="minDiversification out of range (0-1)")
        updates[field] = value
    updated = await svc.update_limits(updates)
    return updated


@router.post("/alerts/{alert_id}/acknowledge", response_model=RiskAlert)
async def acknowledge_alert(alert_id: str, svc: RiskService = Depends(risk_service_dep)):
    try:
        return await svc.acknowledge_alert(alert_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Alert not found")
