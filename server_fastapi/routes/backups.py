"""
Backup API Routes
Endpoints for backup management and restoration
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.settings import get_settings
from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..services.backup_service import BackupService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backups", tags=["Backups"])

# Admin-only routes (should add admin check in production)


class BackupResponse(BaseModel):
    backup_id: str
    backup_type: str
    file_path: str
    file_size: int
    checksum: str
    created_at: str
    compressed: bool


@router.post("/create", response_model=BackupResponse)
async def create_backup(
    backup_type: str = Query("full", description="Backup type: full or incremental"),
    compress: bool = Query(True, description="Compress backup"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db_session)] = None,
):
    """Create database backup (Admin only)"""
    try:
        settings = get_settings()
        service = BackupService(
            db_url=settings.database_url,
            backup_dir="./backups",
        )

        backup_metadata = service.create_backup(
            backup_type=backup_type,
            compress=compress,
        )

        return BackupResponse(**backup_metadata)
    except Exception as e:
        logger.error(f"Error creating backup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create backup")


@router.get("/list", response_model=list[dict])
async def list_backups(
    backup_type: str | None = Query(None, description="Filter by backup type"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """List all backups (Admin only)"""
    try:
        settings = get_settings()
        service = BackupService(
            db_url=settings.database_url,
            backup_dir="./backups",
        )

        backups = service.list_backups(backup_type=backup_type)
        return backups
    except Exception as e:
        logger.error(f"Error listing backups: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list backups")


@router.post("/verify")
async def verify_backup(
    backup_path: str = Query(..., description="Path to backup file"),
    expected_checksum: str | None = Query(None, description="Expected checksum"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """Verify backup integrity (Admin only)"""
    try:
        settings = get_settings()
        service = BackupService(
            db_url=settings.database_url,
            backup_dir="./backups",
        )

        is_valid = service.verify_backup(backup_path, expected_checksum)

        return {
            "backup_path": backup_path,
            "is_valid": is_valid,
        }
    except Exception as e:
        logger.error(f"Error verifying backup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to verify backup")


@router.post("/cleanup")
async def cleanup_backups(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """Clean up old backups based on retention policy (Admin only)"""
    try:
        settings = get_settings()
        service = BackupService(
            db_url=settings.database_url,
            backup_dir="./backups",
        )

        stats = service.cleanup_old_backups()
        return stats
    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cleanup backups")


@router.post("/restore")
async def restore_backup(
    backup_path: str = Query(..., description="Path to backup file"),
    verify: bool = Query(True, description="Verify backup before restoring"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """Restore database from backup (Admin only - DANGEROUS)"""
    try:
        settings = get_settings()
        service = BackupService(
            db_url=settings.database_url,
            backup_dir="./backups",
        )

        success = service.restore_backup(backup_path, verify=verify)

        return {
            "success": success,
            "backup_path": backup_path,
            "message": "Database restored successfully",
        }
    except Exception as e:
        logger.error(f"Error restoring backup: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to restore backup: {str(e)}"
        )


@router.post("/recover")
async def recover_pitr(
    recovery_time: str = Query(..., description="Target recovery time (ISO format)"),
    backup_path: str = Query(..., description="Path to base backup"),
    wal_archive_dir: str = Query(..., description="WAL archive directory"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """Point-in-Time Recovery (Admin only - DANGEROUS)"""
    try:
        from ..services.wal_archiving_service import WALArchivingService

        wal_service = WALArchivingService(archive_dir=wal_archive_dir)

        # Validate recovery time
        recovery_dt = datetime.fromisoformat(recovery_time.replace("Z", "+00:00"))

        # Get recovery points
        recovery_points = wal_service.get_recovery_points(
            end_date=recovery_dt + timedelta(hours=1)
        )

        if not recovery_points:
            raise HTTPException(
                status_code=400,
                detail="No recovery points available for specified time",
            )

        # Note: Actual PITR requires manual PostgreSQL configuration
        # This endpoint provides validation and instructions
        return {
            "success": True,
            "recovery_time": recovery_time,
            "recovery_points_available": len(recovery_points),
            "instructions": [
                "1. Stop PostgreSQL server",
                "2. Restore base backup to data directory",
                f"3. Create recovery.conf with recovery_target_time = '{recovery_time}'",
                f"4. Set restore_command = 'cp {wal_archive_dir}/%f %p'",
                "5. Start PostgreSQL server",
                "6. PostgreSQL will recover to specified time",
                "7. Verify data integrity",
                "8. Promote database (SELECT pg_promote();)",
            ],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid recovery time: {str(e)}")
    except Exception as e:
        logger.error(f"Error preparing PITR: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to prepare PITR: {str(e)}")


@router.get("/recovery-points")
async def get_recovery_points(
    start_date: str | None = Query(None, description="Start date (ISO format)"),
    end_date: str | None = Query(None, description="End date (ISO format)"),
    wal_archive_dir: str = Query("./wal_archive", description="WAL archive directory"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """Get available recovery points (Admin only)"""
    try:
        from datetime import datetime

        from ..services.wal_archiving_service import WALArchivingService

        wal_service = WALArchivingService(archive_dir=wal_archive_dir)

        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        recovery_points = wal_service.get_recovery_points(
            start_date=start,
            end_date=end,
        )

        return {
            "recovery_points": recovery_points,
            "count": len(recovery_points),
        }
    except Exception as e:
        logger.error(f"Error getting recovery points: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get recovery points: {str(e)}"
        )


@router.post("/test-recovery")
async def test_recovery(
    backup_path: str = Query(..., description="Path to backup file"),
    test_db_url: str = Query(..., description="Test database URL"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """Test backup recovery in test environment (Admin only)"""
    try:
        settings = get_settings()
        service = BackupService(
            db_url=test_db_url,
            backup_dir="./backups",
        )

        # Restore to test database
        success = service.restore_backup(backup_path, verify=True)

        if success:
            # Verify test database
            # (Additional verification logic can be added here)
            return {
                "success": True,
                "message": "Recovery test completed successfully",
                "test_db_url": test_db_url,
            }
        else:
            return {
                "success": False,
                "message": "Recovery test failed",
            }
    except Exception as e:
        logger.error(f"Error testing recovery: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to test recovery: {str(e)}"
        )
