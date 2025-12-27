try:
    from pydantic import BaseModel, EmailStr
except Exception:
    from pydantic import BaseModel
    EmailStr = str  # Fallback when email-validator extra isn't installed
from typing import Optional, Dict, Any, List
from enum import Enum

# User Preferences schemas
class Theme(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"

class UserPreferences(BaseModel):
    userId: str
    theme: Theme = Theme.DARK
    notifications: Dict[str, bool] = {
        "trade_executed": True,
        "bot_status_change": True,
        "market_alert": True,
        "system": True
    }
    uiSettings: Dict[str, Any] = {
        "compact_mode": False,
        "auto_refresh": True,
        "refresh_interval": 30,  # seconds
        "default_chart_period": "1H",
        "language": "en"
    }
    tradingSettings: Dict[str, Any] = {
        "default_order_type": "market",
        "confirm_orders": True,
        "show_fees": True
    }
    createdAt: float
    updatedAt: float

class UpdateUserPreferences(BaseModel):
    theme: Optional[Theme] = None
    notifications: Optional[Dict[str, bool]] = None
    uiSettings: Optional[Dict[str, Any]] = None
    tradingSettings: Optional[Dict[str, Any]] = None

# Rate limit info
class RateLimitInfo(BaseModel):
    remaining: int
    reset: float

# Login/Register schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

# Backwards-compatible aliases
loginSchema = LoginRequest
registerSchema = RegisterRequest
