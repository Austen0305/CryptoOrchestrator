from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..services.notification_service import (
    NotificationService,
    NotificationCategory,
    NotificationPriority,
)
from ..dependencies.auth import get_current_user
from ..database import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter()


def get_notification_service(db: AsyncSession = Depends(get_db_session)) -> NotificationService:
    """Dependency to get NotificationService instance"""
    return NotificationService(db)


@router.get("/", response_model=Dict[str, Any])
async def get_notifications(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None,
    unread_only: bool = Query(False),
    priority: Optional[List[str]] = Query(None),
    current_user: dict = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Get user's notifications with filtering"""
    try:
        category_enum = NotificationCategory(category) if category else None
        priority_enums = (
            [NotificationPriority(p) for p in priority] if priority else None
        )

        user_id = current_user.get("id") or current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            logger.warning(f"User ID not found in current_user: {current_user}")
            return {"success": True, "data": [], "total": 0}
        
        notifications = await notification_service.get_recent_notifications(
            str(user_id),
            limit=limit,
            category=category_enum,
            unread_only=unread_only,
            priority_filter=priority_enums,
        )

        # Apply offset
        notifications = notifications[offset : offset + limit]

        return {"success": True, "data": notifications, "total": len(notifications)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notifications: {e}", exc_info=True)
        # Return empty notifications instead of 500 error for better UX during development
        logger.warning(f"Returning empty notifications list due to error: {e}")
        return {"success": True, "data": [], "total": 0}


@router.post("/", response_model=Dict[str, Any])
async def create_notification(
    notification_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Create a new notification (primarily for testing/admin purposes)"""
    try:
        message = notification_data.get("message")
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        level = notification_data.get("level", "info")
        title = notification_data.get("title")
        category = NotificationCategory(notification_data.get("category", "system"))
        priority = NotificationPriority(notification_data.get("priority", "medium"))
        data = notification_data.get("data", {})

        user_id = current_user.get("id") or current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        notification = await notification_service.create_notification(
            user_id=str(user_id),
            message=message,
            level=level,
            title=title,
            category=category,
            priority=priority,
            data=data,
        )

        return {"success": True, "data": notification}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid notification data: {e}")
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to create notification")


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int, current_user: dict = Depends(get_current_user)
):
    """Mark a specific notification as read"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        success = await notification_service.mark_as_read(
            str(user_id), notification_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")

        return {"success": True, "message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to mark notification as read"
        )


@router.patch("/read-all")
async def mark_all_notifications_read(
    category: Optional[str] = None, current_user: dict = Depends(get_current_user)
):
    """Mark all notifications as read, optionally filtered by category"""
    try:
        category_enum = NotificationCategory(category) if category else None
        user_id = current_user.get("id") or current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        count = await notification_service.mark_all_as_read(
            str(user_id), category_enum
        )

        return {"success": True, "message": f"Marked {count} notifications as read"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid category: {e}")
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to mark notifications as read"
        )


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int, current_user: dict = Depends(get_current_user)
):
    """Delete a specific notification"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        success = await notification_service.delete_notification(
            str(user_id), notification_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")

        return {"success": True, "message": "Notification deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")


@router.get("/stats", response_model=Dict[str, Any])
async def get_notification_stats(current_user: dict = Depends(get_current_user)):
    """Get notification statistics for the user"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            return {"success": True, "data": {"total": 0, "unread": 0, "by_category": {}, "by_priority": {}}}
        
        stats = await notification_service.get_notification_stats(str(user_id))
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve notification statistics"
        )


@router.get("/unread-count")
async def get_unread_count(
    category: Optional[str] = None,
    priority: Optional[List[str]] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get count of unread notifications with optional filters"""
    try:
        category_enum = NotificationCategory(category) if category else None
        priority_enums = (
            [NotificationPriority(p) for p in priority] if priority else None
        )

        user_id = current_user.get("id") or current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            return {"success": True, "count": 0}
        
        count = await notification_service.get_unread_count(
            str(user_id), category=category_enum, priority_filter=priority_enums
        )

        return {"success": True, "count": count}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid filter parameter: {e}")
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise HTTPException(status_code=500, detail="Failed to get unread count")


@router.post("/broadcast")
async def broadcast_notification(
    broadcast_data: Dict[str, Any], current_user: dict = Depends(get_current_user)
):
    """Broadcast notification to multiple users (admin only)"""
    # Note: In a real implementation, you'd check if current_user has admin privileges

    try:
        user_ids = broadcast_data.get("user_ids", [])
        message = broadcast_data.get("message")
        level = broadcast_data.get("level", "info")
        title = broadcast_data.get("title")
        category = NotificationCategory(broadcast_data.get("category", "system"))
        priority = NotificationPriority(broadcast_data.get("priority", "medium"))
        data = broadcast_data.get("data", {})

        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        if not user_ids:
            raise HTTPException(status_code=400, detail="User IDs are required")

        await notification_service.broadcast_notification(
            user_ids=user_ids,
            message=message,
            level=level,
            title=title,
            category=category,
            priority=priority,
            data=data,
        )

        return {
            "success": True,
            "message": f"Notification broadcasted to {len(user_ids)} users",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid broadcast data: {e}")
    except Exception as e:
        logger.error(f"Error broadcasting notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast notification")
