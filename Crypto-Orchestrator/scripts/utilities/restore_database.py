#!/usr/bin/env python3
"""
Database restore script for CryptoOrchestrator
Supports point-in-time recovery and backup restoration
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
import boto3

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseRestore:
    """Database restore manager"""
    
    def __init__(
        self,
        database_url: str,
        backup_dir: str = "./backups",
        s3_bucket: Optional[str] = None,
        s3_prefix: str = "database-backups"
    ):
        self.database_url = database_url
        self.backup_dir = Path(backup_dir)
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        
        if s3_bucket:
            self.s3_client = boto3.client('s3')
        else:
            self.s3_client = None
    
    def list_backups(self) -> list:
        """List available backups"""
        backups = []
        
        # Local backups
        for backup_file in sorted(self.backup_dir.glob("*_backup_*"), reverse=True):
            backups.append({
                "type": "local",
                "path": str(backup_file),
                "name": backup_file.name,
                "size": backup_file.stat().st_size,
                "modified": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat()
            })
        
        # S3 backups
        if self.s3_client:
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.s3_bucket,
                    Prefix=self.s3_prefix
                )
                
                for obj in response.get('Contents', []):
                    backups.append({
                        "type": "s3",
                        "path": f"s3://{self.s3_bucket}/{obj['Key']}",
                        "name": obj['Key'].split('/')[-1],
                        "size": obj['Size'],
                        "modified": obj['LastModified'].isoformat()
                    })
            except Exception as e:
                logger.warning(f"Failed to list S3 backups: {e}")
        
        return sorted(backups, key=lambda x: x['modified'], reverse=True)
    
    def download_from_s3(self, s3_key: str, local_path: Path) -> Path:
        """Download backup from S3"""
        logger.info(f"Downloading {s3_key} from S3")
        
        try:
            self.s3_client.download_file(
                self.s3_bucket,
                s3_key,
                str(local_path)
            )
            
            logger.info(f"Downloaded to {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"S3 download failed: {e}")
            raise
    
    def restore_postgres(self, backup_file: Path, drop_existing: bool = False) -> bool:
        """Restore PostgreSQL database"""
        logger.info(f"Restoring PostgreSQL from {backup_file}")
        
        # Parse database URL
        db_url = self.database_url.replace("postgresql+asyncpg://", "postgresql://")
        
        try:
            if drop_existing:
                logger.warning("Dropping existing database...")
                # Extract database name from URL
                # Format: postgresql://user:pass@host:port/dbname
                db_name = db_url.split('/')[-1].split('?')[0]
                drop_cmd = [
                    "psql",
                    db_url.rsplit('/', 1)[0] + "/postgres",  # Connect to postgres DB
                    "-c",
                    f"DROP DATABASE IF EXISTS {db_name};"
                ]
                subprocess.run(drop_cmd, check=True)
            
            # Restore backup
            cmd = [
                "pg_restore",
                "--dbname", db_url,
                "--no-owner",
                "--no-acl",
                "--clean",
                "--if-exists",
                str(backup_file)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("PostgreSQL restore completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"PostgreSQL restore failed: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.error("pg_restore not found. Install PostgreSQL client tools.")
            return False
    
    def restore_sqlite(self, backup_file: Path, drop_existing: bool = False) -> bool:
        """Restore SQLite database"""
        logger.info(f"Restoring SQLite from {backup_file}")
        
        # Parse SQLite URL
        db_path = self.database_url.replace("sqlite+aiosqlite:///", "")
        db_path_obj = Path(db_path)
        
        try:
            if drop_existing and db_path_obj.exists():
                logger.warning("Removing existing database...")
                db_path_obj.unlink()
            
            # Copy backup to database location
            import shutil
            shutil.copy2(backup_file, db_path)
            
            logger.info("SQLite restore completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"SQLite restore failed: {e}")
            return False
    
    def restore(self, backup_path: str, drop_existing: bool = False) -> bool:
        """Restore from backup file"""
        backup_file = Path(backup_path)
        
        # Download from S3 if needed
        if backup_path.startswith("s3://"):
            s3_key = backup_path.replace(f"s3://{self.s3_bucket}/", "")
            backup_file = self.backup_dir / Path(s3_key).name
            self.download_from_s3(s3_key, backup_file)
        
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_file}")
            return False
        
        # Determine database type and restore
        if "postgresql" in self.database_url.lower():
            return self.restore_postgres(backup_file, drop_existing)
        elif "sqlite" in self.database_url.lower():
            return self.restore_sqlite(backup_file, drop_existing)
        else:
            logger.error(f"Unsupported database URL: {self.database_url}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Database restore script")
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
        "--backup-file",
        help="Backup file to restore (local path or s3:// URL)"
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Restore latest backup"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available backups"
    )
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop existing database before restore (DANGEROUS)"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm restore operation (required for safety)"
    )
    
    args = parser.parse_args()
    
    if not args.database_url:
        logger.error("DATABASE_URL not provided")
        sys.exit(1)
    
    restore_manager = DatabaseRestore(
        database_url=args.database_url,
        backup_dir=args.backup_dir,
        s3_bucket=args.s3_bucket,
        s3_prefix=args.s3_prefix
    )
    
    if args.list:
        backups = restore_manager.list_backups()
        print("\nAvailable Backups:")
        print("-" * 80)
        for i, backup in enumerate(backups, 1):
            print(f"{i}. {backup['name']}")
            print(f"   Type: {backup['type']}")
            print(f"   Size: {backup['size']:,} bytes")
            print(f"   Modified: {backup['modified']}")
            print()
        sys.exit(0)
    
    if not args.confirm:
        logger.error("Restore requires --confirm flag for safety")
        logger.error("This will overwrite your database!")
        sys.exit(1)
    
    if args.latest:
        backups = restore_manager.list_backups()
        if not backups:
            logger.error("No backups found")
            sys.exit(1)
        backup_path = backups[0]['path']
        logger.info(f"Using latest backup: {backup_path}")
    elif args.backup_file:
        backup_path = args.backup_file
    else:
        logger.error("Specify --backup-file or --latest")
        sys.exit(1)
    
    success = restore_manager.restore(backup_path, args.drop_existing)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
