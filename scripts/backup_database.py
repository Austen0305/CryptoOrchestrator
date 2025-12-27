#!/usr/bin/env python3
"""
Database Backup Script
Automated database backup with compression and retention
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server_fastapi.services.backup_service import BackupService
from server_fastapi.config.settings import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main backup function"""
    try:
        settings = get_settings()
        
        # Initialize backup service
        backup_dir = os.getenv("BACKUP_DIR", "./backups")
        service = BackupService(
            db_url=settings.database_url,
            backup_dir=backup_dir,
            retention_days=7,
            retention_weeks=4,
            retention_months=12,
        )
        
        # Create backup
        logger.info("Creating database backup...")
        backup_metadata = service.create_backup(
            backup_type="full",
            compress=True,
        )
        
        logger.info(f"Backup created successfully: {backup_metadata['backup_id']}")
        logger.info(f"File: {backup_metadata['file_path']}")
        logger.info(f"Size: {backup_metadata['file_size']} bytes")
        logger.info(f"Checksum: {backup_metadata['checksum']}")
        
        # Verify backup
        logger.info("Verifying backup...")
        is_valid = service.verify_backup(
            backup_metadata["file_path"],
            backup_metadata["checksum"],
        )
        
        if is_valid:
            logger.info("Backup verification successful")
        else:
            logger.error("Backup verification failed!")
            sys.exit(1)
        
        # Cleanup old backups
        logger.info("Cleaning up old backups...")
        cleanup_stats = service.cleanup_old_backups()
        logger.info(f"Cleanup complete: {cleanup_stats}")
        
        logger.info("Backup process completed successfully")
        
    except Exception as e:
        logger.error(f"Backup failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
