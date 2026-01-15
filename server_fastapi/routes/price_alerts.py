"""
Price Alerts Routes
Manages price alerts for cryptocurrency trading
"""

import logging
from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["price-alerts"])  # Prefix is added in main.py


class PriceAlert(BaseModel):
    id: str
    symbol: str
    condition: Literal["above", "below", "change", "volume"]
    targetPrice: float | None = None
    changePercent: float | None = None
    volumeThreshold: float | None = None
    isActive: bool = True
    triggered: bool = False
    createdAt: datetime
    triggeredAt: datetime | None = None
    channels: list[Literal["email", "push", "sms", "telegram", "discord"]] = ["push"]
    sound: bool | None = False

    model_config = {"from_attributes": True}


class CreatePriceAlertRequest(BaseModel):
    symbol: str
    condition: Literal["above", "below", "change", "volume"]
    targetPrice: float | None = None
    changePercent: float | None = None
    volumeThreshold: float | None = None
    channels: list[Literal["email", "push", "sms", "telegram", "discord"]] = ["push"]
    sound: bool | None = False


class ToggleAlertRequest(BaseModel):
    isActive: bool


# In-memory storage for price alerts (replace with database in production)
_price_alerts_storage: dict[str, dict] = {}


@router.get("/", response_model=list[PriceAlert])
@cached(ttl=120, prefix="price_alerts")  # 120s TTL for price alerts list
async def get_price_alerts(
    current_user: Annotated[dict, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """Get all price alerts for the current user with pagination"""
    try:
        user_id = _get_user_id(current_user)

        # Filter alerts by user_id
        user_alerts = [
            alert
            for alert in _price_alerts_storage.values()
            if alert.get("user_id") == str(user_id)
        ]

        # Convert to PriceAlert models
        alerts = []
        for alert_data in user_alerts:
            try:
                alert = PriceAlert(**alert_data)
                alerts.append(alert)
            except Exception as e:
                logger.warning(f"Failed to parse alert {alert_data.get('id')}: {e}")
                continue

        # Apply pagination
        len(alerts)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_alerts = alerts[start_idx:end_idx]

        return paginated_alerts
    except Exception as e:
        logger.error(f"Failed to get price alerts: {e}", exc_info=True)
        return []  # Return empty list instead of 500 error


@router.post("/", response_model=PriceAlert)
async def create_price_alert(
    request: CreatePriceAlertRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Create a new price alert"""
    try:
        user_id = _get_user_id(current_user)

        # Validate request based on condition
        if request.condition in ["above", "below"] and not request.targetPrice:
            raise HTTPException(
                status_code=400,
                detail=f"targetPrice is required for {request.condition} condition",
            )
        if request.condition == "change" and not request.changePercent:
            raise HTTPException(
                status_code=400, detail="changePercent is required for change condition"
            )
        if request.condition == "volume" and not request.volumeThreshold:
            raise HTTPException(
                status_code=400,
                detail="volumeThreshold is required for volume condition",
            )

        # Create alert
        alert_id = str(uuid4())
        alert_data = {
            "id": alert_id,
            "user_id": str(user_id),
            "symbol": request.symbol,
            "condition": request.condition,
            "targetPrice": request.targetPrice,
            "changePercent": request.changePercent,
            "volumeThreshold": request.volumeThreshold,
            "isActive": True,
            "triggered": False,
            "createdAt": datetime.now(UTC),
            "triggeredAt": None,
            "channels": request.channels,
            "sound": request.sound or False,
        }

        _price_alerts_storage[alert_id] = alert_data

        logger.info(f"Created price alert {alert_id} for user {user_id}")

        return PriceAlert(**alert_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create price alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create price alert")


@router.patch("/{alert_id}/toggle", response_model=PriceAlert)
async def toggle_price_alert(
    alert_id: str,
    request: ToggleAlertRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Toggle a price alert's active status"""
    try:
        user_id = _get_user_id(current_user)

        # Find alert
        alert_data = _price_alerts_storage.get(alert_id)
        if not alert_data:
            raise HTTPException(status_code=404, detail="Alert not found")

        # Check ownership
        if alert_data.get("user_id") != str(user_id):
            raise HTTPException(status_code=403, detail="Not authorized")

        # Update alert
        alert_data["isActive"] = request.isActive
        _price_alerts_storage[alert_id] = alert_data

        logger.info(
            f"Toggled price alert {alert_id} to {request.isActive} for user {user_id}"
        )

        return PriceAlert(**alert_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle price alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to toggle price alert")


@router.delete("/{alert_id}")
async def delete_price_alert(
    alert_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Delete a price alert"""
    try:
        user_id = _get_user_id(current_user)

        # Find alert
        alert_data = _price_alerts_storage.get(alert_id)
        if not alert_data:
            raise HTTPException(status_code=404, detail="Alert not found")

        # Check ownership
        if alert_data.get("user_id") != str(user_id):
            raise HTTPException(status_code=403, detail="Not authorized")

        # Delete alert
        del _price_alerts_storage[alert_id]

        logger.info(f"Deleted price alert {alert_id} for user {user_id}")

        return {"message": "Alert deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete price alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete price alert")
