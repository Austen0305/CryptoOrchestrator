"""
Disaster Recovery Service
Manages database replication, failover, and health monitoring
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func

logger = logging.getLogger(__name__)


class DisasterRecoveryService:
    """Service for disaster recovery operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_replication_status(self) -> Dict[str, Any]:
        """Check PostgreSQL replication status"""
        try:
            # Check if we're connected to PostgreSQL
            result = await self.db.execute(text("SELECT version()"))
            version = result.scalar()
            
            if "PostgreSQL" not in version:
                return {
                    "replication_enabled": False,
                    "message": "PostgreSQL replication only supported for PostgreSQL databases",
                }

            # Check replication status
            replication_query = text("""
                SELECT 
                    client_addr,
                    state,
                    sync_state,
                    sync_priority,
                    pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn) as lag_bytes,
                    EXTRACT(EPOCH FROM (now() - state_change)) as lag_seconds
                FROM pg_stat_replication
            """)
            
            result = await self.db.execute(replication_query)
            replicas = result.fetchall()

            if not replicas:
                return {
                    "replication_enabled": False,
                    "replica_count": 0,
                    "message": "No active replicas found",
                }

            replica_statuses = []
            for replica in replicas:
                lag_seconds = replica.lag_seconds or 0
                lag_bytes = replica.lag_bytes or 0
                
                status = "healthy"
                if lag_seconds > 300:  # 5 minutes
                    status = "degraded"
                if lag_seconds > 600:  # 10 minutes
                    status = "unhealthy"

                replica_statuses.append({
                    "client_addr": str(replica.client_addr) if replica.client_addr else None,
                    "state": replica.state,
                    "sync_state": replica.sync_state,
                    "sync_priority": replica.sync_priority,
                    "lag_bytes": int(lag_bytes),
                    "lag_seconds": float(lag_seconds),
                    "status": status,
                })

            overall_status = "healthy"
            if any(r["status"] == "unhealthy" for r in replica_statuses):
                overall_status = "unhealthy"
            elif any(r["status"] == "degraded" for r in replica_statuses):
                overall_status = "degraded"

            return {
                "replication_enabled": True,
                "replica_count": len(replica_statuses),
                "overall_status": overall_status,
                "replicas": replica_statuses,
            }

        except Exception as e:
            logger.error(f"Error checking replication status: {e}", exc_info=True)
            return {
                "replication_enabled": False,
                "error": str(e),
                "message": "Failed to check replication status",
            }

    async def check_database_health(self) -> Dict[str, Any]:
        """Comprehensive database health check"""
        health_checks = {}

        try:
            # Connection check
            start = datetime.utcnow()
            await self.db.execute(text("SELECT 1"))
            connection_latency = (datetime.utcnow() - start).total_seconds() * 1000

            health_checks["connection"] = {
                "status": "healthy" if connection_latency < 100 else "degraded",
                "latency_ms": round(connection_latency, 2),
            }

            # Database size
            size_query = text("""
                SELECT pg_database_size(current_database()) as db_size
            """)
            result = await self.db.execute(size_query)
            db_size = result.scalar()
            health_checks["database_size"] = {
                "size_bytes": db_size,
                "size_mb": round(db_size / (1024 * 1024), 2),
                "size_gb": round(db_size / (1024 * 1024 * 1024), 2),
            }

            # Active connections
            conn_query = text("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity
                WHERE datname = current_database()
            """)
            result = await self.db.execute(conn_query)
            conn_stats = result.fetchone()
            
            health_checks["connections"] = {
                "total": conn_stats.total_connections,
                "active": conn_stats.active_connections,
                "idle": conn_stats.idle_connections,
            }

            # Replication lag (if applicable)
            replication_status = await self.check_replication_status()
            if replication_status.get("replication_enabled"):
                max_lag = max(
                    (r.get("lag_seconds", 0) for r in replication_status.get("replicas", [])),
                    default=0
                )
                health_checks["replication"] = {
                    "status": replication_status.get("overall_status", "unknown"),
                    "max_lag_seconds": max_lag,
                    "replica_count": replication_status.get("replica_count", 0),
                }

            # Overall status
            overall_status = "healthy"
            if health_checks["connection"]["status"] != "healthy":
                overall_status = "degraded"
            if health_checks.get("replication", {}).get("status") == "unhealthy":
                overall_status = "degraded"

            return {
                "overall_status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "checks": health_checks,
            }

        except Exception as e:
            logger.error(f"Error checking database health: {e}", exc_info=True)
            return {
                "overall_status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def check_backup_health(self, backup_service) -> Dict[str, Any]:
        """Check backup system health"""
        try:
            from ..services.backup_service import BackupService

            # Get backup list
            backups = backup_service.list_backups()

            if not backups:
                return {
                    "status": "warning",
                    "message": "No backups found",
                    "backup_count": 0,
                }

            # Find most recent backup
            most_recent = max(backups, key=lambda b: b.get("created_at", ""))
            backup_age_hours = (
                datetime.utcnow() - datetime.fromisoformat(most_recent["created_at"])
            ).total_seconds() / 3600

            # Check backup age
            status = "healthy"
            if backup_age_hours > 48:
                status = "warning"
            if backup_age_hours > 72:
                status = "unhealthy"

            # Calculate total backup size
            total_size = sum(b.get("file_size", 0) for b in backups)

            return {
                "status": status,
                "backup_count": len(backups),
                "most_recent_backup": {
                    "file_path": most_recent.get("file_path"),
                    "created_at": most_recent.get("created_at"),
                    "age_hours": round(backup_age_hours, 2),
                },
                "total_backup_size_mb": round(total_size / (1024 * 1024), 2),
                "message": f"Most recent backup is {backup_age_hours:.1f} hours old",
            }

        except Exception as e:
            logger.error(f"Error checking backup health: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to check backup health",
            }

    async def get_system_health_detailed(self, backup_service) -> Dict[str, Any]:
        """Get detailed system health status"""
        db_health = await self.check_database_health()
        backup_health = await self.check_backup_health(backup_service)
        replication_status = await self.check_replication_status()

        # Determine overall status
        overall_status = "healthy"
        if (
            db_health.get("overall_status") != "healthy"
            or backup_health.get("status") == "unhealthy"
            or replication_status.get("overall_status") == "unhealthy"
        ):
            overall_status = "degraded"
        if (
            db_health.get("overall_status") == "unhealthy"
            or backup_health.get("status") == "error"
        ):
            overall_status = "unhealthy"

        return {
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_health,
            "backups": backup_health,
            "replication": replication_status,
        }
