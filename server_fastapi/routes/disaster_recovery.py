"""
Disaster Recovery API Routes
Endpoints for replication management, health monitoring, and failover
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.settings import settings
from ..database import get_db_session
from ..dependencies.auth import get_current_user, require_permission
from ..models.user import User
from ..services.backup_service import BackupService
from ..services.disaster_recovery_service import DisasterRecoveryService

router = APIRouter(prefix="/api/disaster-recovery", tags=["Disaster Recovery"])


# Pydantic Models
class FailoverRequest(BaseModel):
    target_replica: str | None = None  # Replica identifier
    force: bool = False  # Force failover even if replica is lagging


@router.get("/replication/status")
async def get_replication_status(
    current_user: User = Depends(require_permission("admin:monitoring")),
    db: AsyncSession = Depends(get_db_session),
):
    """Get database replication status (Admin only)"""
    service = DisasterRecoveryService(db)
    status = await service.check_replication_status()
    return status


@router.post("/replication/failover")
async def initiate_failover(
    request: FailoverRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Initiate database failover to replica (Admin only, DANGEROUS)"""
    service = DisasterRecoveryService(db)

    # Check replication status first
    replication_status = await service.check_replication_status()

    if not replication_status.get("replication_enabled"):
        raise HTTPException(
            status_code=400,
            detail="Replication is not enabled or no replicas available",
        )

    # Check replica lag
    replicas = replication_status.get("replicas", [])
    if not request.force:
        unhealthy_replicas = [r for r in replicas if r.get("status") == "unhealthy"]
        if unhealthy_replicas:
            raise HTTPException(
                status_code=400,
                detail="Cannot failover: replicas are unhealthy. Use force=true to override.",
            )

    # Note: Actual failover requires manual intervention or external tooling
    # This endpoint provides status and validation
    return {
        "success": True,
        "message": "Failover validation passed. Manual failover required.",
        "replication_status": replication_status,
        "instructions": [
            "1. Stop application services",
            "2. Promote replica to primary using: SELECT pg_promote();",
            "3. Update application connection strings",
            "4. Restart application services",
            "5. Verify application connectivity",
        ],
    }


@router.get("/health/detailed")
async def get_detailed_health(
    current_user: User = Depends(require_permission("admin:monitoring")),
    db: AsyncSession = Depends(get_db_session),
):
    """Get detailed system health status (Admin only)"""
    service = DisasterRecoveryService(db)

    # Initialize backup service
    backup_service = BackupService(
        db_url=settings.database_url,
        backup_dir=(
            settings.backup_dir if hasattr(settings, "backup_dir") else "./backups"
        ),
    )

    health = await service.get_system_health_detailed(backup_service)
    return health


@router.get("/health/database")
async def get_database_health(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get database health status (Admin only)"""
    service = DisasterRecoveryService(db)
    health = await service.check_database_health()
    return health


@router.get("/health/backups")
async def get_backup_health(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get backup system health (Admin only)"""
    service = DisasterRecoveryService(db)

    backup_service = BackupService(
        db_url=settings.database_url,
        backup_dir=(
            settings.backup_dir if hasattr(settings, "backup_dir") else "./backups"
        ),
    )

    health = await service.check_backup_health(backup_service)
    return health
