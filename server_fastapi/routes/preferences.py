from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional, Dict, Any
import logging
import json

from shared.schema import UserPreferences, UpdateUserPreferences, Theme
from pydantic import BaseModel
from ..database import get_db_context
from ..repositories.preferences_repository import preferences_repository
from ..repositories.user_repository import user_repository
from ..dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


def _default_notifications(enabled: bool) -> Dict[str, bool]:
    return {
        "trade_executed": enabled,
        "bot_status_change": enabled,
        "market_alert": enabled,
        "system": enabled,
    }


def _merge_with_defaults(prefs_obj) -> Dict[str, Any]:
    # Start with defaults from shared schema
    notifications_enabled = getattr(prefs_obj, "notifications_enabled", True)
    theme_value = (prefs_obj.theme or "light").lower()

    data_json = {}
    if getattr(prefs_obj, "data_json", None):
        try:
            data_json = json.loads(prefs_obj.data_json)
        except Exception:
            data_json = {}

    # Compose payload matching shared.schema.UserPreferences
    ui_settings = data_json.get("uiSettings") or {
        "compact_mode": False,
        "auto_refresh": True,
        "refresh_interval": 30,
        "default_chart_period": "1H",
        "language": prefs_obj.language or "en",
    }
    trading_settings = data_json.get("tradingSettings") or {
        "default_order_type": "market",
        "confirm_orders": True,
        "show_fees": True,
    }
    notifications = data_json.get("notifications") or _default_notifications(
        notifications_enabled
    )

    return {
        "userId": str(prefs_obj.user_id),
        "theme": theme_value,
        "notifications": notifications,
        "uiSettings": ui_settings,
        "tradingSettings": trading_settings,
        "createdAt": float(prefs_obj.created_at.timestamp()),
        "updatedAt": float(prefs_obj.updated_at.timestamp()),
    }


# Routes (mounted at /api/preferences in main.py)
@router.get("/", response_model=UserPreferences)
async def get_user_preferences(current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user.get("id") or current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            logger.warning(f"User ID not found in current_user: {current_user}")
            # Return default preferences
            return UserPreferences(
                userId="1",
                theme="dark",
                notifications=_default_notifications(True),
                uiSettings={
                    "compact_mode": False,
                    "auto_refresh": True,
                    "refresh_interval": 30,
                    "default_chart_period": "1H",
                    "language": "en",
                },
                tradingSettings={
                    "default_order_type": "market",
                    "confirm_orders": True,
                    "show_fees": True,
                },
                createdAt=float(datetime.now().timestamp()),
                updatedAt=float(datetime.now().timestamp()),
            )
        
        async with get_db_context() as session:
            prefs = await preferences_repository.get_by_user_id(session, str(user_id))
            if not prefs:
                prefs = await preferences_repository.upsert_for_user(
                    session,
                    str(user_id),
                    theme="light",
                    language="en",
                    notifications_enabled=True,
                    data_json=json.dumps({}),
                )
            data = _merge_with_defaults(prefs)
            return UserPreferences(**data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}", exc_info=True)
        # Return default preferences instead of 500 error for better UX during development
        logger.warning(f"Returning default preferences due to error: {e}")
        # Import UserPreferences from shared schema
        user_id = current_user.get("id") or current_user.get("user_id") or "1"
        return UserPreferences(
            userId=str(user_id),
            theme="dark",
            notifications={},
            uiSettings={},
            tradingSettings={},
            createdAt=float(datetime.now().timestamp()),
            updatedAt=float(datetime.now().timestamp()),
        )


@router.put("/", response_model=UserPreferences)
async def update_user_preferences(
    updates: UpdateUserPreferences, current_user: dict = Depends(get_current_user)
):
    update_data = updates.dict(exclude_unset=True)
    async with get_db_context() as session:
        prefs = await preferences_repository.get_by_user_id(session, current_user["id"])
        if not prefs:
            prefs = await preferences_repository.upsert_for_user(
                session, current_user["id"]
            )

        # Load existing data_json and merge
        existing_json = {}
        if getattr(prefs, "data_json", None):
            try:
                existing_json = json.loads(prefs.data_json)
            except Exception:
                existing_json = {}

        if update_data.get("notifications") is not None:
            existing_json["notifications"] = update_data["notifications"]
        if update_data.get("uiSettings") is not None:
            # Merge nested dict
            existing_json["uiSettings"] = {
                **existing_json.get("uiSettings", {}),
                **update_data["uiSettings"],
            }
        if update_data.get("tradingSettings") is not None:
            existing_json["tradingSettings"] = {
                **existing_json.get("tradingSettings", {}),
                **update_data["tradingSettings"],
            }

        await preferences_repository.upsert_for_user(
            session,
            current_user["id"],
            theme=(update_data.get("theme") or prefs.theme),
            language=(
                existing_json.get("uiSettings", {}).get("language") or prefs.language
            ),
            notifications_enabled=(
                prefs.notifications_enabled
                if update_data.get("notifications") is None
                else all(update_data["notifications"].values())
            ),
            data_json=json.dumps(existing_json),
        )

        # Reload and return
        prefs = await preferences_repository.get_by_user_id(session, current_user["id"])
        data = _merge_with_defaults(prefs)
        logger.info(f"Updated preferences for user {current_user['id']}")
        return UserPreferences(**data)


class ThemeUpdate(BaseModel):
    theme: Theme


@router.patch("/theme")
async def update_theme(
    payload: ThemeUpdate, current_user: dict = Depends(get_current_user)
):
    async with get_db_context() as session:
        await preferences_repository.upsert_for_user(
            session, current_user["id"], theme=payload.theme
        )
        return {"message": "Theme updated successfully", "theme": payload.theme}


@router.delete("/")
async def delete_user_preferences(current_user: dict = Depends(get_current_user)):
    async with get_db_context() as session:
        prefs = await preferences_repository.get_by_user_id(session, current_user["id"])
        if not prefs:
            raise HTTPException(status_code=404, detail="Preferences not found")
        await session.delete(prefs)
        await session.commit()
        return {"message": "Preferences reset to defaults"}


@router.post("/reset")
async def reset_user_preferences(current_user: dict = Depends(get_current_user)):
    async with get_db_context() as session:
        prefs = await preferences_repository.get_by_user_id(session, current_user["id"])
        if prefs:
            await session.delete(prefs)
            await session.commit()
        prefs = await preferences_repository.upsert_for_user(
            session,
            current_user["id"],
            theme="light",
            language="en",
            notifications_enabled=True,
            data_json=json.dumps({}),
        )
        data = _merge_with_defaults(prefs)
        return {"message": "Preferences reset to defaults", "preferences": data}
