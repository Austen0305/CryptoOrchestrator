"""
Price Alerts Routes
Manages price alerts for cryptocurrency trading
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime
import logging
from uuid import uuid4

from ..dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["price-alerts"])  # Prefix is added in main.py


class PriceAlert(BaseModel):
    id: str
    symbol: str
    condition: Literal["above", "below", "change", "volume"]
    targetPrice: Optional[float] = None
    changePercent: Optional[float] = None
    volumeThreshold: Optional[float] = None
    isActive: bool = True
    triggered: bool = False
    createdAt: datetime
    triggeredAt: Optional[datetime] = None
    channels: List[Literal["email", "push", "sms", "telegram", "discord"]] = ["push"]
    sound: Optional[bool] = False

    model_config = {"from_attributes": True}


class CreatePriceAlertRequest(BaseModel):
    symbol: str
    condition: Literal["above", "below", "change", "volume"]
    targetPrice: Optional[float] = None
    changePercent: Optional[float] = None
    volumeThreshold: Optional[float] = None
    channels: List[Literal["email", "push", "sms", "telegram", "discord"]] = ["push"]
    sound: Optional[bool] = False


class ToggleAlertRequest(BaseModel):
    isActive: bool


# In-memory storage for price alerts (replace with database in production)
_price_alerts_storage: dict[str, dict] = {}


@router.get("/", response_model=List[PriceAlert])
async def get_price_alerts(
    current_user: dict = Depends(get_current_user),
):
    """Get all price alerts for the current user"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            logger.warning(f"User ID not found in current_user: {current_user}")
            return []
        
        # Filter alerts by user_id
        user_alerts = [
            alert for alert in _price_alerts_storage.values()
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
        
        return alerts
    except Exception as e:
        logger.error(f"Failed to get price alerts: {e}", exc_info=True)
        return []  # Return empty list instead of 500 error


@router.post("/", response_model=PriceAlert)
async def create_price_alert(
    request: CreatePriceAlertRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a new price alert"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Validate request based on condition
        if request.condition in ["above", "below"] and not request.targetPrice:
            raise HTTPException(
                status_code=400,
                detail=f"targetPrice is required for {request.condition} condition"
            )
        if request.condition == "change" and not request.changePercent:
            raise HTTPException(
                status_code=400,
                detail="changePercent is required for change condition"
            )
        if request.condition == "volume" and not request.volumeThreshold:
            raise HTTPException(
                status_code=400,
                detail="volumeThreshold is required for volume condition"
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
            "createdAt": datetime.utcnow(),
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
    current_user: dict = Depends(get_current_user),
):
    """Toggle a price alert's active status"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
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
        
        logger.info(f"Toggled price alert {alert_id} to {request.isActive} for user {user_id}")
        
        return PriceAlert(**alert_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle price alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to toggle price alert")


@router.delete("/{alert_id}")
async def delete_price_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a price alert"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
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

