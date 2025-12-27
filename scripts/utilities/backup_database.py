#!/usr/bin/env python3
"""
Automated database backup script for CryptoOrchestrator
Supports PostgreSQL and SQLite databases
"""

import os
import sys
import subprocess
import datetime
import argparse
import boto3
from pathlib import Path
from typing import Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseBackup:
    """Database backup manager"""
    
    def __init__(
        self,
        database_url: str,
        backup_dir: str = "./backups",
        s3_bucket: Optional[str] = None,
        s3_prefix: str = "database-backups",
        retention_days: int = 30
    ):
        self.database_url = database_url
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        self.retention_days = retention_days
        
        if s3_bucket:
            self.s3_client = boto3.client('s3')
        else:
            self.s3_client = None
    
    def backup_postgres(self) -> Path:
        """Backup PostgreSQL database"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"postgres_backup_{timestamp}.sql.gz"
        
        # Parse database URL
        # Format: postgresql+asyncpg://user:pass@host:port/dbname
        db_url = self.database_url.replace("postgresql+asyncpg://", "postgresql://")
        
        logger.info(f"Starting PostgreSQL backup to {backup_file}")
        
        try:
            # Use pg_dump with compression
            cmd = [
                "pg_dump",
                db_url,
                "--no-owner",
                "--no-acl",
                "--clean",
                "--if-exists",
                "--format=custom",
                "--compress=9",
                f"--file={backup_file}"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"PostgreSQL backup completed: {backup_file}")
            return backup_file
            
        except subprocess.CalledProcessError as e:
            logger.error(f"PostgreSQL backup failed: {e.stderr}")
            raise
        except FileNotFoundError:
            logger.error("pg_dump not found. Install PostgreSQL client tools.")
            raise
    
    def backup_sqlite(self) -> Path:
        """Backup SQLite database"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"sqlite_backup_{timestamp}.db"
        
        # Parse SQLite URL
        # Format: sqlite+aiosqlite:///path/to/db.db
        db_path = self.database_url.replace("sqlite+aiosqlite:///", "")
        
        logger.info(f"Starting SQLite backup from {db_path} to {backup_file}")
        
        try:
            # SQLite backup using VACUUM INTO (SQLite 3.27+)
            import sqlite3
            
            source_conn = sqlite3.connect(db_path)
            source_conn.execute(f"VACUUM INTO '{backup_file}'")
            source_conn.close()
            
            logger.info(f"SQLite backup completed: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"SQLite backup failed: {e}")
            raise
    
    def upload_to_s3(self, backup_file: Path) -> str:
        """Upload backup file to S3"""
        if not self.s3_client:
            logger.warning("S3 client not configured, skipping upload")
            return ""
        
        s3_key = f"{self.s3_prefix}/{backup_file.name}"
        
        logger.info(f"Uploading {backup_file} to s3://{self.s3_bucket}/{s3_key}")
        
        try:
            self.s3_client.upload_file(
                str(backup_file),
                self.s3_bucket,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'  # Infrequent Access for cost savings
                }
            )
            
            logger.info(f"Upload completed: s3://{self.s3_bucket}/{s3_key}")
            return s3_key
            
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise
    
    def cleanup_old_backups(self):
        """Remove backups older than retention period"""
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.retention_days)
        
        logger.info(f"Cleaning up backups older than {self.retention_days} days")
        
        deleted_count = 0
        for backup_file in self.backup_dir.glob("*_backup_*"):
            if backup_file.is_file():
                file_time = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_time < cutoff_date:
                    backup_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {backup_file.name}")
        
        logger.info(f"Cleanup completed: {deleted_count} files deleted")
    
    def verify_backup(self, backup_file: Path) -> bool:
        """Verify backup file integrity"""
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_file}")
            return False
        
        file_size = backup_file.stat().st_size
        if file_size == 0:
            logger.error(f"Backup file is empty: {backup_file}")
            return False
        
        logger.info(f"Backup verification passed: {backup_file} ({file_size} bytes)")
        return True
    
    def create_backup(self) -> dict:
        """Create backup and return metadata"""
        try:
            # Determine database type
            if "postgresql" in self.database_url.lower():
                backup_file = self.backup_postgres()
            elif "sqlite" in self.database_url.lower():
                backup_file = self.backup_sqlite()
            else:
                raise ValueError(f"Unsupported database URL: {self.database_url}")
            
            # Verify backup
            if not self.verify_backup(backup_file):
                raise ValueError("Backup verification failed")
            
            # Upload to S3 if configured
            s3_key = ""
            if self.s3_bucket:
                s3_key = self.upload_to_s3(backup_file)
            
            # Cleanup old backups
            self.cleanup_old_backups()
            
            metadata = {
                "backup_file": str(backup_file),
                "s3_key": s3_key,
                "size_bytes": backup_file.stat().st_size,
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "success"
            }
            
            logger.info("Backup completed successfully")
            return metadata
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }


def main():
    parser = argparse.ArgumentParser(description="Database backup script")
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL"),
        help="Database URL (default: DATABASE_URL env var)"
    )
    parser.add_argument(
        "--backup-dir",
        default=os.getenv("BACKUP_DIR", "./backups"),
        help="Backup directory (default: ./backups)"
    )
    parser.add_argument(
        "--s3-bucket",
        default=os.getenv("S3_BACKUP_BUCKET"),
        help="S3 bucket for backups (optional)"
    )
    parser.add_argument(
        "--s3-prefix",
        default=os.getenv("S3_BACKUP_PREFIX", "database-backups"),
        help="S3 key prefix (default: database-backups)"
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=int(os.getenv("BACKUP_RETENTION_DAYS", "30")),
        help="Backup retention in days (default: 30)"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing backups"
    )
    
    args = parser.parse_args()
    
    if not args.database_url:
        logger.error("DATABASE_URL not provided")
        sys.exit(1)
    
    backup_manager = DatabaseBackup(
        database_url=args.database_url,
        backup_dir=args.backup_dir,
        s3_bucket=args.s3_bucket,
        s3_prefix=args.s3_prefix,
        retention_days=args.retention_days
    )
    
    if args.verify_only:
        # Verify all backups
        backup_files = list(backup_manager.backup_dir.glob("*_backup_*"))
        verified = sum(1 for f in backup_files if backup_manager.verify_backup(f))
        logger.info(f"Verified {verified}/{len(backup_files)} backups")
        sys.exit(0 if verified == len(backup_files) else 1)
    else:
        # Create backup
        result = backup_manager.create_backup()
        sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
