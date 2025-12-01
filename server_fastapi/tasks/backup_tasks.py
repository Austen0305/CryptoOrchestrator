"""
Celery Tasks for Automated Backups
Scheduled tasks for regular database backups
"""
import logging
from datetime import datetime

from ..celery_app import celery_app
from ..services.backup_service import backup_service

logger = logging.getLogger(__name__)


@celery_app.task(name="backups.create_daily_backup")
def create_daily_backup():
    """Create a daily database backup"""
    try:
        logger.info("Starting scheduled daily backup...")
        
        # Run backup in async context
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            backup_service.create_backup(backup_type="full", encrypt=True)
        )
        
        if result.get("status") == "success":
            logger.info(f"✅ Daily backup completed: {result.get('filename')}")
        else:
            logger.error(f"❌ Daily backup failed: {result.get('error')}")
        
        return result
    except Exception as e:
        logger.error(f"Error in scheduled backup task: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}


@celery_app.task(name="backups.cleanup_old_backups")
def cleanup_old_backups():
    """Clean up old backups beyond retention period"""
    try:
        logger.info("Starting backup cleanup...")
        
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        deleted_count = loop.run_until_complete(
            backup_service._cleanup_old_backups()
        )
        
        logger.info(f"✅ Cleaned up {deleted_count} old backups")
        return {"deleted_count": deleted_count}
    except Exception as e:
        logger.error(f"Error in backup cleanup task: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}


# Schedule tasks (merged into main celery_app beat_schedule)
# The schedule is defined in celery_app.py to avoid conflicts

