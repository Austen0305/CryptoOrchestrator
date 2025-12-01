"""
Backup Management Routes
API endpoints for managing database backups
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from ..dependencies.auth import get_current_user
from ..services.backup_service import backup_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backups", tags=["Backups"])


class BackupRequest(BaseModel):
    """Request to create a backup"""
    backup_type: str = "full"  # 'full' or 'incremental'
    encrypt: bool = True


class RestoreRequest(BaseModel):
    """Request to restore from backup"""
    backup_filename: str
    verify_only: bool = False


@router.post("/create", response_model=Dict[str, Any])
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a database backup
    
    Note: Requires admin privileges (you may want to add admin check)
    """
    try:
        # Create backup (can be run in background for large databases)
        result = await backup_service.create_backup(
            backup_type=request.backup_type,
            encrypt=request.encrypt
        )
        
        if result.get("status") == "failed":
            raise HTTPException(status_code=500, detail=result.get("error", "Backup failed"))
        
        return result
    except Exception as e:
        logger.error(f"Error creating backup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create backup")


@router.get("/list", response_model=List[Dict[str, Any]])
async def list_backups(
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List all available backups"""
    try:
        backups = await backup_service.list_backups()
        return backups
    except Exception as e:
        logger.error(f"Error listing backups: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list backups")


@router.post("/restore", response_model=Dict[str, Any])
async def restore_backup(
    request: RestoreRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Restore database from backup
    
    WARNING: This will overwrite the current database!
    Note: Requires admin privileges (you may want to add admin check)
    """
    try:
        result = await backup_service.restore_backup(
            backup_filename=request.backup_filename,
            verify_only=request.verify_only
        )
        
        if result.get("status") == "failed":
            raise HTTPException(status_code=500, detail=result.get("error", "Restore failed"))
        
        return result
    except Exception as e:
        logger.error(f"Error restoring backup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to restore backup")


@router.get("/status", response_model=Dict[str, Any])
async def get_backup_status(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get backup system status and statistics"""
    try:
        backups = await backup_service.list_backups()
        
        total_size = sum(b["size_bytes"] for b in backups)
        total_count = len(backups)
        
        return {
            "status": "active",
            "total_backups": total_count,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "retention_days": backup_service.retention_days,
            "backup_directory": str(backup_service.backup_dir),
            "encryption_enabled": backup_service.encryption_enabled,
            "latest_backup": backups[0] if backups else None
        }
    except Exception as e:
        logger.error(f"Error getting backup status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get backup status")

